#!/bin/bash
set -euo pipefail

# AIOS v2 Deployment Script
# Usage: ./deploy.sh [environment] [options]
# Environments: development, staging, production
# Options: --blue-green, --switch-traffic, --rollback

ENVIRONMENT=${1:-development}
OPTION=${2:-}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment configuration
load_environment() {
    local env_file="$PROJECT_ROOT/.env.$ENVIRONMENT"
    if [[ -f "$env_file" ]]; then
        log_info "Loading environment: $ENVIRONMENT"
        export $(grep -v '^#' "$env_file" | xargs)
    else
        log_error "Environment file not found: $env_file"
        exit 1
    fi
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Create backup before migration
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_info "Creating database backup..."
        docker run --rm \
            --env-file "$PROJECT_ROOT/.env.$ENVIRONMENT" \
            --network aios_network \
            postgres:15 \
            pg_dump -h postgres -U "$DATABASE_USER" -d "$DATABASE_NAME" \
            > "$PROJECT_ROOT/backups/db_backup_$(date +%Y%m%d_%H%M%S).sql"
    fi
    
    # Run migrations
    docker run --rm \
        --env-file "$PROJECT_ROOT/.env.$ENVIRONMENT" \
        --network aios_network \
        -v "$PROJECT_ROOT:/app" \
        "${API_IMAGE:-aios-api:latest}" \
        alembic upgrade head
    
    if [[ $? -eq 0 ]]; then
        log_success "Migrations completed successfully"
    else
        log_error "Migration failed"
        exit 1
    fi
}

# Deploy with Docker Compose
deploy_compose() {
    log_info "Deploying with Docker Compose..."
    
    local compose_file="$PROJECT_ROOT/docker/docker-compose.yml"
    if [[ "$ENVIRONMENT" != "development" ]]; then
        compose_file="$PROJECT_ROOT/docker/docker-compose.$ENVIRONMENT.yml"
    fi
    
    # Pull latest images
    docker-compose -f "$compose_file" pull
    
    # Deploy services
    docker-compose -f "$compose_file" up -d --remove-orphans
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check health
    check_health
}

# Blue-Green deployment
deploy_blue_green() {
    log_info "Starting Blue-Green deployment..."
    
    # Deploy to blue environment
    export DEPLOYMENT_COLOR=blue
    docker-compose -f "$PROJECT_ROOT/docker/docker-compose.$ENVIRONMENT.yml" \
        -p aios-blue \
        up -d --remove-orphans
    
    # Wait and check health
    sleep 30
    if ! check_health "http://localhost:8001/health"; then
        log_error "Blue deployment health check failed"
        exit 1
    fi
    
    log_success "Blue deployment successful"
    log_info "Run with --switch-traffic to switch traffic to blue deployment"
}

# Switch traffic in Blue-Green deployment
switch_traffic() {
    log_info "Switching traffic to blue deployment..."
    
    # Update load balancer configuration
    # This is a placeholder - actual implementation depends on your load balancer
    # For nginx, you might update upstream configuration
    # For cloud load balancers, use their APIs
    
    # Example for nginx
    if command -v nginx &> /dev/null; then
        sed -i 's/server localhost:8000/server localhost:8001/' /etc/nginx/sites-available/aios
        nginx -t && nginx -s reload
    fi
    
    # Stop green deployment after successful switch
    docker-compose -f "$PROJECT_ROOT/docker/docker-compose.$ENVIRONMENT.yml" \
        -p aios-green \
        down
    
    # Rename blue to green for next deployment
    docker-compose -f "$PROJECT_ROOT/docker/docker-compose.$ENVIRONMENT.yml" \
        -p aios-blue \
        down
    docker-compose -f "$PROJECT_ROOT/docker/docker-compose.$ENVIRONMENT.yml" \
        -p aios-green \
        up -d --remove-orphans
    
    log_success "Traffic switched successfully"
}

# Health check
check_health() {
    local health_url=${1:-"http://localhost:8000/health"}
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f -s "$health_url" > /dev/null; then
            log_success "Health check passed"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_info "Health check attempt $attempt/$max_attempts..."
        sleep 2
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Test API endpoints
    local endpoints=(
        "/health"
        "/api/v1/marketplace/stats"
        "/api/v1/agents"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s "http://localhost:8000$endpoint" > /dev/null; then
            log_success "Smoke test passed: $endpoint"
        else
            log_error "Smoke test failed: $endpoint"
            return 1
        fi
    done
    
    return 0
}

# Main deployment flow
main() {
    log_info "Starting deployment for environment: $ENVIRONMENT"
    
    # Load environment
    load_environment
    
    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/backups"
    
    # Handle different deployment options
    case "$OPTION" in
        "--blue-green")
            if [[ "$ENVIRONMENT" == "production" ]]; then
                deploy_blue_green
            else
                log_warning "Blue-Green deployment only available for production"
                deploy_compose
            fi
            ;;
        "--switch-traffic")
            if [[ "$ENVIRONMENT" == "production" ]]; then
                switch_traffic
            else
                log_error "Traffic switching only available for production"
                exit 1
            fi
            ;;
        "--rollback")
            log_info "Rolling back deployment..."
            "$SCRIPT_DIR/rollback.sh" "$ENVIRONMENT"
            ;;
        *)
            # Standard deployment
            run_migrations
            deploy_compose
            run_smoke_tests
            ;;
    esac
    
    log_success "Deployment completed successfully!"
}

# Run main function
main "$@"