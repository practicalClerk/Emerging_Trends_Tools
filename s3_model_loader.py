"""
S3 Model Loader for CI/CD Prediction Service
Loads ML models from AWS S3 with local fallback
"""

import os
import logging
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not available. Install with: pip install boto3")


class S3ModelLoader:
    """Load ML models from AWS S3 with local fallback"""

    def __init__(self):
        """Initialize S3 client and configuration"""
        if not BOTO3_AVAILABLE:
            self.s3_client = None
            logger.info("S3 loading disabled (boto3 not installed)")
            return

        self.bucket_name = os.getenv('S3_MODEL_BUCKET')
        self.prefix = os.getenv('S3_MODEL_PREFIX', 'models')
        self.region = os.getenv('AWS_REGION', 'us-east-1')

        if not self.bucket_name:
            self.s3_client = None
            logger.info("S3 loading disabled (S3_MODEL_BUCKET not set)")
            return

        try:
            self.s3_client = boto3.client('s3', region_name=self.region)
            logger.info(f"✅ S3 loader initialized: {self.bucket_name}/{self.prefix}")
        except Exception as e:
            self.s3_client = None
            logger.warning(f"Failed to initialize S3 client: {e}")

    def is_available(self) -> bool:
        """Check if S3 loading is available"""
        return self.s3_client is not None

    def download_model_file(self, filename: str, local_path: Optional[str] = None) -> Optional[str]:
        """
        Download a model file from S3

        Args:
            filename: Name of the file to download (e.g., 'random_forest_model.pkl')
            local_path: Optional local path. If None, uses temp directory

        Returns:
            Local path to downloaded file, or None if download failed
        """
        if not self.is_available():
            return None

        if local_path is None:
            local_path = os.path.join(tempfile.gettempdir(), filename)

        s3_key = f"{self.prefix}/{filename}"

        try:
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )
            logger.info(f"Downloaded {filename} from S3 to {local_path}")
            return local_path
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"File not found in S3: {s3_key}")
            else:
                logger.warning(f"S3 download error for {filename}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to download {filename}: {e}")
            return None

    def download_all_models(self, local_dir: Optional[str] = None) -> bool:
        """
        Download all model files from S3

        Args:
            local_dir: Optional local directory. If None, uses current directory

        Returns:
            True if all files downloaded successfully
        """
        if not self.is_available():
            return False

        model_files = [
            'random_forest_model.pkl',
            'scaler.pkl',
            'label_encoder.pkl',
            'feature_names.txt'
        ]

        success_count = 0
        for filename in model_files:
            local_path = os.path.join(local_dir or '.', filename) if local_dir else None
            if self.download_model_file(filename, local_path):
                success_count += 1

        return success_count == len(model_files)

    def check_models_exist(self) -> bool:
        """Check if all model files exist in S3"""
        if not self.is_available():
            return False

        model_files = [
            'random_forest_model.pkl',
            'scaler.pkl',
            'label_encoder.pkl',
            'feature_names.txt'
        ]

        for filename in model_files:
            try:
                self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=f"{self.prefix}/{filename}"
                )
            except ClientError:
                return False
            except Exception as e:
                logger.warning(f"S3 check error for {filename}: {e}")
                return False

        return True

    def get_model_info(self) -> dict:
        """Get information about models in S3"""
        if not self.is_available():
            return {"available": False}

        info = {
            "available": True,
            "bucket": self.bucket_name,
            "prefix": self.prefix,
            "region": self.region
        }

        model_files = [
            'random_forest_model.pkl',
            'scaler.pkl',
            'label_encoder.pkl',
            'feature_names.txt'
        ]

        files_info = {}
        for filename in model_files:
            try:
                response = self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=f"{self.prefix}/{filename}"
                )
                files_info[filename] = {
                    "size": response.get('ContentLength', 0),
                    "last_modified": response.get('LastModified')
                }
            except Exception:
                files_info[filename] = {"exists": False}

        info["files"] = files_info
        return info


# Global instance
_s3_loader = None


def get_s3_loader() -> S3ModelLoader:
    """Get or create the global S3 loader instance"""
    global _s3_loader
    if _s3_loader is None:
        _s3_loader = S3ModelLoader()
    return _s3_loader


def try_load_models_from_s3():
    """
    Attempt to load models from S3 if local files are missing

    Returns:
        True if models were loaded from S3, False otherwise
    """
    loader = get_s3_loader()

    if not loader.is_available():
        return False

    # Check if local files exist
    required_files = [
        'random_forest_model.pkl',
        'scaler.pkl',
        'label_encoder.pkl',
        'feature_names.txt'
    ]

    missing_files = [f for f in required_files if not os.path.exists(f)]

    if not missing_files:
        logger.info("All local model files exist, skipping S3 download")
        return False

    logger.info(f"Missing local files: {missing_files}. Attempting S3 download...")

    # Only download missing files
    success = True
    for filename in missing_files:
        if loader.download_model_file(filename) is None:
            success = False

    return success
