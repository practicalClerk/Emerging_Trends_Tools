"""
Prometheus Metrics for CI/CD Prediction Service
Exposes application metrics for monitoring and alerting
"""

import logging
from typing import Dict, Any
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST
)

logger = logging.getLogger(__name__)

# Registry for metrics
registry = CollectorRegistry()

# Application info
app_info = Info(
    'ml_cicd_predictor',
    'ML CI/CD Failure Prediction Service',
    registry=registry
)
app_info.info({
    'version': '1.0.0',
    'service': 'ml-cicd-predictor'
})

# HTTP request metrics
http_requests_total = Counter(
    'flask_http_request_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'flask_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    registry=registry
)

# Prediction metrics
predictions_total = Counter(
    'ml_predictions_total',
    'Total predictions made',
    ['outcome'],  # PASS or FAIL
    registry=registry
)

predictions_cache_hits_total = Counter(
    'ml_predictions_cache_hits_total',
    'Total cache hits',
    registry=registry
)

predictions_cache_misses_total = Counter(
    'ml_predictions_cache_misses_total',
    'Total cache misses',
    registry=registry
)

# Risk level metrics
predictions_by_risk_level = Counter(
    'ml_predictions_by_risk_level',
    'Predictions by risk level',
    ['risk_level'],  # LOW, MEDIUM, HIGH, CRITICAL
    registry=registry
)

# Feature value gauges (for monitoring input distributions)
commit_size_gauge = Gauge(
    'ml_commit_size',
    'Commit size in lines',
    registry=registry
)

files_changed_gauge = Gauge(
    'ml_files_changed',
    'Number of files changed',
    registry=registry
)

test_coverage_gauge = Gauge(
    'ml_test_coverage',
    'Test coverage percentage',
    registry=registry
)

build_time_gauge = Gauge(
    'ml_build_time',
    'Build time in seconds',
    registry=registry
)

# Probability gauges
failure_probability_gauge = Gauge(
    'ml_failure_probability',
    'Current failure probability',
    registry=registry
)

confidence_gauge = Gauge(
    'ml_prediction_confidence',
    'Prediction confidence score',
    registry=registry
)

# Model performance metrics
model_accuracy_gauge = Gauge(
    'ml_model_accuracy',
    'Model accuracy (updated via retraining)',
    registry=registry
)

# Groq API metrics
groq_api_requests_total = Counter(
    'groq_api_requests_total',
    'Total Groq API requests',
    ['status'],
    registry=registry
)

groq_api_duration_seconds = Histogram(
    'groq_api_duration_seconds',
    'Groq API call duration',
    registry=registry
)


class MetricsCollector:
    """Collects and tracks application metrics"""

    @staticmethod
    def record_http_request(method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

    @staticmethod
    def record_prediction(outcome: str, risk_level: str, failure_prob: float, confidence: float):
        """Record prediction metrics"""
        predictions_total.labels(outcome=outcome).inc()
        predictions_by_risk_level.labels(risk_level=risk_level).inc()
        failure_probability_gauge.set(failure_prob)
        confidence_gauge.set(confidence)

    @staticmethod
    def record_cache_hit():
        """Record a cache hit"""
        predictions_cache_hits_total.inc()

    @staticmethod
    def record_cache_miss():
        """Record a cache miss"""
        predictions_cache_misses_total.inc()

    @staticmethod
    def record_input_features(input_data: Dict[str, Any]):
        """Record input feature values"""
        commit_size_gauge.set(input_data.get('commit_size', 0))
        files_changed_gauge.set(input_data.get('files_changed', 0))
        test_coverage_gauge.set(input_data.get('test_coverage', 0))
        build_time_gauge.set(input_data.get('build_time', 0))

    @staticmethod
    def record_groq_request(status: str, duration: float):
        """Record Groq API request"""
        groq_api_requests_total.labels(status=status).inc()
        groq_api_duration_seconds.observe(duration)

    @staticmethod
    def get_metrics() -> bytes:
        """Get metrics in Prometheus format"""
        return generate_latest(registry)


def init_flask_metrics(app):
    """
    Initialize Prometheus metrics for Flask app

    Usage:
        from prometheus_metrics import init_flask_metrics
        init_flask_metrics(app)
    """
    from flask import Response
    import time

    @app.route('/metrics', methods=['GET'])
    def metrics():
        """Expose Prometheus metrics"""
        return Response(
            MetricsCollector.get_metrics(),
            mimetype=CONTENT_TYPE_LATEST
        )

    @app.before_request
    def before_request():
        """Record request start time"""
        from flask import request
        request.start_time = time.time()

    @app.after_request
    def after_request(response):
        """Record request metrics"""
        from flask import request
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            MetricsCollector.record_http_request(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=response.status_code,
                duration=duration
            )
        return response

    logger.info("✅ Prometheus metrics initialized")


# Lazy import flask to avoid circular dependency
flask = None


def get_flask():
    """Lazy import Flask"""
    global flask
    if flask is None:
        import flask
    return flask
