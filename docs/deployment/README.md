# AIOS v2 Deployment Guide

This guide provides comprehensive instructions for deploying the AIOS v2 platform across different environments.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Docker Deployment](#docker-deployment)
- [CI/CD Pipeline](#cicd-pipeline)
- [Database Migrations](#database-migrations)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## Prerequisites

### Required Tools
- Docker 20.10+ and Docker Compose 2.0+
- Git 2.30+
- PostgreSQL client (for database operations)
- Node.js 18+ (for frontend builds)
- Python 3.11+ (for API development)

### Access Requirements
- GitHub repository access
- Container registry credentials
- Production server SSH access (for production deployments)
- Database credentials for each environment
- API keys for external services (OpenAI, Anthropic, etc.)

## Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/bluelabel-AIOS-V2.git
cd bluelabel-AIOS-V2
```

### 2. Configure Environment Variables
Copy the example environment file and configure for your environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

Key environment variables:
- `ENVIRONMENT`: development, staging, or production
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Application secret (generate secure key)
- `JWT_SECRET_KEY`: JWT signing key (generate secure key)

### 3. Generate Secure Keys
```bash
# Generate secure keys for production
python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')"
python -c "import secrets; print(f'JWT_SECRET_KEY={secrets.token_urlsafe(32)}')"
```

## Docker Deployment

### Local Development
```bash
# Start all services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Building Images
```bash
# Build API image
docker build -f docker/api.Dockerfile -t aios-api:latest .

# Build frontend image
docker build -f docker/web.Dockerfile -t aios-web:latest .
```

### Production Deployment
```bash
# Deploy using the deployment script
./scripts/deployment/deploy.sh production

# Blue-Green deployment (production only)
./scripts/deployment/deploy.sh production --blue-green

# Switch traffic after blue-green deployment
./scripts/deployment/deploy.sh production --switch-traffic
```

## CI/CD Pipeline

### GitHub Actions Workflows

1. **Test Pipeline** (`test.yml`)
   - Triggered on: Push to main/develop, Pull requests
   - Runs: Linting, type checking, unit tests, integration tests
   - Security scanning with Trivy

2. **Staging Deployment** (`staging.yml`)
   - Triggered on: Push to develop
   - Deploys to staging environment automatically
   - Runs smoke tests after deployment

3. **Production Deployment** (`production.yml`)
   - Triggered manually with version tag
   - Requires approval for production environment
   - Supports blue-green deployment
   - Automatic rollback on failure

### Manual Deployment
```bash
# Trigger production deployment
gh workflow run production.yml -f version=v1.0.0
```

## Database Migrations

### Running Migrations
```bash
# Development
alembic upgrade head

# Production (via Docker)
docker run --rm \
  --env-file .env.production \
  --network aios_network \
  aios-api:latest \
  alembic upgrade head
```

### Creating New Migrations
```bash
# Auto-generate migration
alembic revision --autogenerate -m "Add new feature"

# Manual migration
alembic revision -m "Custom migration"
```

### Rollback Migrations
```bash
# Rollback one revision
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Emergency rollback
./scripts/deployment/rollback.sh production --emergency
```

## Monitoring

### Health Checks
- **Basic Health**: `GET /health`
- **Liveness Probe**: `GET /health/live`
- **Readiness Probe**: `GET /health/ready`
- **Detailed Health**: `GET /health/detailed`

### Metrics
- **Prometheus Metrics**: `GET /metrics`
- Includes system metrics, API metrics, and business metrics

### Recommended Monitoring Stack
1. **Prometheus**: Metrics collection
2. **Grafana**: Visualization
3. **AlertManager**: Alert routing
4. **Sentry**: Error tracking

### Setting up Monitoring
```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker logs aios-api

# Verify environment variables
docker exec aios-api env | grep -E "DATABASE|REDIS"

# Check container health
docker inspect aios-api --format='{{.State.Health.Status}}'
```

#### Database Connection Issues
```bash
# Test database connection
docker exec -it aios-postgres psql -U aios -d aios_v2

# Check migration status
docker exec aios-api alembic current
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# View detailed metrics
curl http://localhost:8000/metrics

# Check slow queries
docker exec -it aios-postgres psql -U aios -d aios_v2 -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Emergency Procedures

#### Rollback Deployment
```bash
# Standard rollback
./scripts/deployment/rollback.sh production

# Emergency rollback (immediate)
./scripts/deployment/rollback.sh production --emergency

# Rollback to specific version
./scripts/deployment/rollback.sh production --to-version v1.0.0
```

#### Database Restore
```bash
# List backups
ls -la backups/

# Restore from backup
docker exec -i aios-postgres psql -U aios -d aios_v2 < backups/db_backup_20240101_120000.sql
```

## Security Considerations

### Secrets Management
1. Never commit secrets to version control
2. Use environment variables for all sensitive data
3. Rotate keys regularly
4. Use different keys for each environment

### Network Security
1. Use HTTPS for all external communication
2. Implement rate limiting
3. Enable CORS only for trusted domains
4. Use firewall rules to restrict access

### Container Security
1. Run containers as non-root user
2. Use minimal base images
3. Scan images for vulnerabilities
4. Keep dependencies updated

### Database Security
1. Use strong passwords
2. Enable SSL/TLS for connections
3. Restrict network access
4. Regular backups with encryption

## Production Checklist

Before deploying to production:

- [ ] All tests passing
- [ ] Security scan completed
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Monitoring configured
- [ ] Backup procedures verified
- [ ] Rollback plan documented
- [ ] Load testing completed
- [ ] SSL certificates valid
- [ ] DNS records configured
- [ ] CDN configured (if applicable)
- [ ] Rate limiting enabled
- [ ] Error tracking (Sentry) configured
- [ ] Logging aggregation setup
- [ ] Documentation updated

## Support

For deployment issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review application logs
3. Check the [Runbook](runbook.md) for detailed procedures
4. Contact the development team

## Additional Resources

- [Runbook](runbook.md) - Detailed operational procedures
- [Architecture Documentation](../ARCHITECTURE.md)
- [API Documentation](../API_INSTRUCTIONS.md)
- [Security Guidelines](../security/README.md)