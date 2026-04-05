# ML-Based CI/CD Failure Prediction

A production-ready ML service that predicts CI/CD build outcomes before full pipeline execution. Features cloud-native deployment, observability, and multiple deployment options.

## What Problem This Solves

Builds often fail after spending time on install/test/build steps. This service estimates failure risk early using commit-level metadata so teams can:
- Get fast feedback
- Avoid unnecessary build runs
- Use compute resources more efficiently

## Architecture Overview

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  GitHub/GitLab  │────>│ CI/CD Pipeline│────>│  Prediction │
│                 │     │              │     │   API       │
└─────────────────┘     └──────────────┘     └──────┬──────┘
                                                      │
                       ┌──────────────────────────────┼──────────────────────────┐
                       │                              │                          │
                       ▼                              ▼                          ▼
              ┌─────────────────┐           ┌──────────────┐          ┌─────────────┐
              │  Redis Cache    │           │  S3 Model    │          │  Prometheus │
              │                 │           │  Storage     │          │  + Grafana  │
              └─────────────────┘           └──────────────┘          └─────────────┘
                       │                              │
                       ▼                              ▼
              ┌─────────────────┐           ┌──────────────┐
              │  AWS Lambda     │           │ CloudWatch   │
              │  (Serverless)   │           │  Logs/Alarms │
              └─────────────────┘           └──────────────┘
```

## Project Structure

```text
.
├── app.py                      # Flask API with prediction endpoints
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container image definition
├── docker-compose.yml          # Multi-service orchestration
├── .env.example                # Environment variables template
│
├── models/                     # ML model artifacts
│   ├── random_forest_model.pkl
│   ├── scaler.pkl
│   ├── label_encoder.pkl
│   └── feature_names.txt
│
├── k8s/                        # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
│
├── helm/                       # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│
├── terraform/                  # AWS infrastructure
│   ├── main.tf
│   ├── vpc.tf
│   ├── ecs.tf
│   ├── lambda.tf
│   ├── s3.tf
│   ├── cloudwatch.tf
│   ├── variables.tf
│   └── outputs.tf
│
├── lambda/                     # AWS Lambda function
│   ├── lambda_handler.py
│   └── requirements.txt
│
├── s3_model_loader.py          # S3 model loading logic
├── redis_cache.py              # Redis caching layer
├── prometheus_metrics.py       # Prometheus metrics
│
├── prometheus.yml              # Prometheus configuration
├── cloudwatch_config.json      # CloudWatch dashboard config
├── grafana/                    # Grafana dashboards/provisioning
│
├── index.html                  # Web dashboard
├── ci_cd_workflow.yml          # GitHub Actions workflow
├── test_api.py                 # API tests
│
├── CONTRIBUTION_LOG.md         # Development history
└── README.md
```

## Prerequisites

| Tool | Version | Required For |
|------|---------|--------------|
| Python | 3.9+ | Local development |
| Docker | 20.10+ | Container deployment |
| kubectl | 1.25+ | Kubernetes deployment |
| helm | 3.0+ | Helm deployment |
| terraform | 1.0+ | AWS infrastructure |
| AWS CLI | 2.0+ | AWS deployment |

## Quick Start

### Option 1: Docker Compose (Recommended for Local)

```bash
# Clone repository
git clone https://github.com/practicalClerk/Emerging_Trends_Tools.git
cd Emerging_Trends_Tools

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

Services available:
- **API**: http://localhost:5000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### Option 2: Local Python

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

### Option 3: Kubernetes

```bash
kubectl apply -f k8s/
# Or with Helm:
helm install ml-cicd ./helm
```

### Option 4: AWS (Terraform)

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## API Endpoints

### GET /health
Service health check.

```json
{
  "status": "healthy",
  "service": "CI/CD Failure Predictor",
  "timestamp": "2026-04-05T10:20:30.123456"
}
```

### POST /predict
Predict single build outcome.

```json
{
  "commit_size": 100,
  "files_changed": 5,
  "test_coverage": 75.0,
  "past_failures": 2,
  "dependency_changes": 0,
  "author_experience": 60,
  "time_of_commit": 14,
  "build_time": 350.0
}
```

Response:
```json
{
  "prediction": "PASS",
  "risk_level": "MEDIUM",
  "failure_probability": 0.3421,
  "pass_probability": 0.6579,
  "confidence": 0.7654,
  "recommendation": "CONTINUE PIPELINE"
}
```

### POST /predict-batch
Batch predictions for multiple commits.

### GET /features
Model feature names and importance.

### GET /metrics
Prometheus metrics endpoint.

## Features

### Caching Layer
- Redis-backed prediction caching
- TTL-based cache invalidation
- Configurable cache keys

### Observability
- **Prometheus**: Request latency, prediction counts, cache hit rates
- **Grafana**: Pre-built dashboards for visualization
- **CloudWatch**: AWS-native logging and alarms (when deployed to AWS)

### S3 Model Storage
- Load models from S3 on startup
- Local fallback if S3 unavailable
- Supports model versioning

### AWS Lambda
- Serverless prediction function
- Pay-per-use pricing
- Auto-scaling

## Environment Variables

```bash
# API Configuration
FLASK_ENV=production
GROQ_API_KEY=your_api_key_here

# AWS (optional)
AWS_REGION=us-east-1
S3_MODEL_BUCKET=your-bucket-name
S3_MODEL_PREFIX=models

# Features
ENABLE_CACHE=true
ENABLE_METRICS=true

# Redis (when using Docker Compose)
REDIS_HOST=redis
REDIS_PORT=6379
```

## CI/CD Integration

### GitHub Actions

Copy `ci_cd_workflow.yml` to `.github/workflows/`:

```bash
mkdir -p .github/workflows
cp ci_cd_workflow.yml .github/workflows/
```

The workflow:
1. Extracts commit metadata
2. Calls prediction API
3. Skips/continues pipeline based on risk

### Jenkins/GitLab CI

Similar integration using HTTP requests to `/predict` endpoint.

## Monitoring Dashboards

### Grafana
Import provided dashboards from `grafana/provisioning/`:
- Prediction success rate
- Response times
- Resource utilization

### Prometheus
Access at http://localhost:9090 (with Docker Compose)

Key metrics:
- `prediction_requests_total`
- `prediction_duration_seconds`
- `cache_hits_total`

## AWS Deployment Details

### Terraform Components

| Module | Purpose |
|--------|---------|
| `vpc.tf` | VPC, subnets, security groups |
| `ecs.tf` | ECS task definitions and service |
| `lambda.tf` | Lambda function and API Gateway |
| `s3.tf` | Model storage bucket |
| `cloudwatch.tf` | Logs, metrics, and alarms |

### Outputs

After `terraform apply`:
- API endpoint URL
- Lambda function URL
- S3 bucket name
- CloudWatch dashboard link

## Testing

```bash
# Unit tests
python test_api.py

# Integration tests (with Docker Compose running)
curl http://localhost:5000/health
curl -X POST http://localhost:5000/predict -H "Content-Type: application/json" \
  -d '{"commit_size": 100, "files_changed": 5, "test_coverage": 75.0}'
```

## Model Notes

- **Algorithm**: Random Forest
- **Dataset**: 2,000 CI/CD build samples
- **Features**: 8 (commit size, files changed, test coverage, etc.)
- **Classes**: PASS, FAIL
- **Accuracy**: ~85% on test set

**Note**: This is a course project model. For production use, retrain with your pipeline's historical data.

## Limitations

- Predictions depend on training data quality
- May miss edge-case failures
- Should complement, not replace, full CI/CD checks
- Requires feature retraining for different project types

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Models not loading | Check S3 credentials or local file paths |
| High latency | Enable Redis caching |
| Out of memory | Increase Docker container limits |
| 500 errors | Check CloudWatch logs (AWS) or container logs |

## References

- [scikit-learn](https://scikit-learn.org/)
- [Flask](https://flask.palletsprojects.com/)
- [Docker](https://docs.docker.com/)
- [Kubernetes](https://kubernetes.io/docs/)
- [Terraform](https://www.terraform.io/docs)
- [Prometheus](https://prometheus.io/docs/)

## License

For academic use unless otherwise defined by your team.

## Author

Ayush
Emerging Tools and Technologies Lab

---

For questions or issues, please open a GitHub issue.
