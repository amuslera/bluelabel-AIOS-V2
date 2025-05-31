"""
Metrics endpoints for monitoring and observability.
Provides Prometheus-compatible metrics.
"""
from fastapi import APIRouter, Response, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import time
import psutil
from typing import Dict, Any

from apps.api.dependencies.database import get_db
from shared.models.marketplace import AgentModel, AgentInstallationModel, AgentReviewModel
from shared.models.user import UserModel

router = APIRouter(prefix="/metrics", tags=["metrics"])

# Global metrics storage
_metrics: Dict[str, Any] = {
    "http_requests_total": {},
    "http_request_duration_seconds": {},
    "active_users": 0,
    "api_errors_total": 0,
    "database_connections": 0,
    "cache_hits": 0,
    "cache_misses": 0,
}

# Increment metrics (called by middleware)
def increment_metric(metric: str, labels: Dict[str, str] = None):
    """Increment a counter metric"""
    if labels:
        key = ",".join(f'{k}="{v}"' for k, v in labels.items())
        if key not in _metrics[metric]:
            _metrics[metric][key] = 0
        _metrics[metric][key] += 1
    else:
        _metrics[metric] = _metrics.get(metric, 0) + 1

def observe_metric(metric: str, value: float, labels: Dict[str, str] = None):
    """Observe a histogram/gauge metric"""
    if labels:
        key = ",".join(f'{k}="{v}"' for k, v in labels.items())
        if key not in _metrics[metric]:
            _metrics[metric][key] = []
        _metrics[metric][key].append(value)
    else:
        if metric not in _metrics:
            _metrics[metric] = []
        _metrics[metric].append(value)


@router.get("/", response_class=Response)
async def get_metrics(db: Session = Depends(get_db)):
    """
    Prometheus-compatible metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    lines = []
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    lines.extend([
        "# HELP system_cpu_usage_percent CPU usage percentage",
        "# TYPE system_cpu_usage_percent gauge",
        f"system_cpu_usage_percent {cpu_percent}",
        "",
        "# HELP system_memory_usage_bytes Memory usage in bytes",
        "# TYPE system_memory_usage_bytes gauge",
        f"system_memory_usage_bytes {memory.used}",
        "",
        "# HELP system_memory_total_bytes Total memory in bytes",
        "# TYPE system_memory_total_bytes gauge",
        f"system_memory_total_bytes {memory.total}",
        "",
        "# HELP system_disk_usage_bytes Disk usage in bytes",
        "# TYPE system_disk_usage_bytes gauge",
        f"system_disk_usage_bytes {disk.used}",
        "",
        "# HELP system_disk_total_bytes Total disk space in bytes",
        "# TYPE system_disk_total_bytes gauge",
        f"system_disk_total_bytes {disk.total}",
        "",
    ])
    
    # HTTP metrics
    lines.extend([
        "# HELP http_requests_total Total number of HTTP requests",
        "# TYPE http_requests_total counter",
    ])
    for labels, count in _metrics["http_requests_total"].items():
        lines.append(f"http_requests_total{{{labels}}} {count}")
    lines.append("")
    
    # Request duration metrics
    if _metrics["http_request_duration_seconds"]:
        lines.extend([
            "# HELP http_request_duration_seconds HTTP request duration in seconds",
            "# TYPE http_request_duration_seconds histogram",
        ])
        for labels, durations in _metrics["http_request_duration_seconds"].items():
            if durations:
                # Calculate percentiles
                sorted_durations = sorted(durations)
                p50 = sorted_durations[int(len(sorted_durations) * 0.5)]
                p90 = sorted_durations[int(len(sorted_durations) * 0.9)]
                p99 = sorted_durations[int(len(sorted_durations) * 0.99)]
                
                lines.extend([
                    f'http_request_duration_seconds_bucket{{le="0.1",{labels}}} {sum(1 for d in durations if d <= 0.1)}',
                    f'http_request_duration_seconds_bucket{{le="0.5",{labels}}} {sum(1 for d in durations if d <= 0.5)}',
                    f'http_request_duration_seconds_bucket{{le="1.0",{labels}}} {sum(1 for d in durations if d <= 1.0)}',
                    f'http_request_duration_seconds_bucket{{le="5.0",{labels}}} {sum(1 for d in durations if d <= 5.0)}',
                    f'http_request_duration_seconds_bucket{{le="+Inf",{labels}}} {len(durations)}',
                    f"http_request_duration_seconds_sum{{{labels}}} {sum(durations)}",
                    f"http_request_duration_seconds_count{{{labels}}} {len(durations)}",
                ])
        lines.append("")
    
    # Database metrics
    try:
        # User metrics
        total_users = db.query(func.count(UserModel.id)).scalar()
        new_users_24h = db.query(func.count(UserModel.id)).filter(
            UserModel.created_at >= datetime.utcnow() - timedelta(days=1)
        ).scalar()
        
        lines.extend([
            "# HELP users_total Total number of users",
            "# TYPE users_total gauge",
            f"users_total {total_users}",
            "",
            "# HELP users_new_24h New users in last 24 hours",
            "# TYPE users_new_24h gauge",
            f"users_new_24h {new_users_24h}",
            "",
        ])
        
        # Marketplace metrics
        total_agents = db.query(func.count(AgentModel.id)).filter(
            AgentModel.is_active == True
        ).scalar()
        total_installations = db.query(func.count(AgentInstallationModel.id)).filter(
            AgentInstallationModel.is_active == True
        ).scalar()
        total_reviews = db.query(func.count(AgentReviewModel.id)).scalar()
        avg_rating = db.query(func.avg(AgentReviewModel.rating)).scalar() or 0
        
        lines.extend([
            "# HELP marketplace_agents_total Total number of active agents",
            "# TYPE marketplace_agents_total gauge",
            f"marketplace_agents_total {total_agents}",
            "",
            "# HELP marketplace_installations_total Total number of active installations",
            "# TYPE marketplace_installations_total gauge",
            f"marketplace_installations_total {total_installations}",
            "",
            "# HELP marketplace_reviews_total Total number of reviews",
            "# TYPE marketplace_reviews_total gauge",
            f"marketplace_reviews_total {total_reviews}",
            "",
            "# HELP marketplace_average_rating Average agent rating",
            "# TYPE marketplace_average_rating gauge",
            f"marketplace_average_rating {avg_rating:.2f}",
            "",
        ])
        
        # Agent category breakdown
        category_counts = db.query(
            AgentModel.category,
            func.count(AgentModel.id)
        ).filter(
            AgentModel.is_active == True
        ).group_by(AgentModel.category).all()
        
        lines.extend([
            "# HELP marketplace_agents_by_category Number of agents by category",
            "# TYPE marketplace_agents_by_category gauge",
        ])
        for category, count in category_counts:
            if category:
                lines.append(f'marketplace_agents_by_category{{category="{category}"}} {count}')
        lines.append("")
        
    except Exception as e:
        # Log error but don't fail the metrics endpoint
        lines.extend([
            "# HELP database_error Database query error",
            "# TYPE database_error counter",
            f"database_error 1",
            "",
        ])
    
    # Error metrics
    lines.extend([
        "# HELP api_errors_total Total number of API errors",
        "# TYPE api_errors_total counter",
        f"api_errors_total {_metrics.get('api_errors_total', 0)}",
        "",
    ])
    
    # Cache metrics
    lines.extend([
        "# HELP cache_hits_total Total number of cache hits",
        "# TYPE cache_hits_total counter",
        f"cache_hits_total {_metrics.get('cache_hits', 0)}",
        "",
        "# HELP cache_misses_total Total number of cache misses",
        "# TYPE cache_misses_total counter",
        f"cache_misses_total {_metrics.get('cache_misses', 0)}",
        "",
    ])
    
    # Application info
    lines.extend([
        "# HELP app_info Application information",
        "# TYPE app_info gauge",
        f'app_info{{version="{_metrics.get("app_version", "unknown")}",environment="{_metrics.get("environment", "unknown")}"}} 1',
        "",
    ])
    
    # Convert to Prometheus text format
    content = "\n".join(lines)
    
    return Response(
        content=content,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@router.get("/health")
async def metrics_health():
    """Health check for metrics endpoint"""
    return {
        "status": "healthy",
        "metrics_count": sum(
            len(v) if isinstance(v, dict) else 1 
            for v in _metrics.values()
        )
    }