#!/bin/bash
set -euo pipefail

# AIOS v2 Rollback Script
# Usage: ./rollback.sh [environment] [options]
# Options: --emergency, --to-version <version>

ENVIRONMENT=${1:-development}
OPTION=${2:-}
VERSION=${3:-}
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

# Get previous version
get_previous_version() {
    if [[ -f "$PROJECT_ROOT/DEPLOYMENT_HISTORY" ]]; then
        # Get the second-to-last line (previous version)
        tail -n 2 "$PROJECT_ROOT/DEPLOYMENT_HISTORY" | head -n 1 | cut -d' ' -f1
    else
        log_error "No deployment history found"
        exit 1
    fi
}

# Rollback database
rollback_database() {
    local target_version=$1
    log_info "Rolling back database to version: $target_version"
    
    # Find the migration revision for the target version
    docker run --rm \
        --env-file "$PROJECT_ROOT/.env.$ENVIRONMENT" \
        --network aios_network \
        -v "$PROJECT_ROOT:/app" \
        "${API_IMAGE:-aios-api:latest}" \
        alembic downgrade "$target_version"
    
    if [[ $? -eq 0 ]]; then
        log_success "Database rollback completed"
    else
        log_error "Database rollback failed"
        exit 1
    fi
}

# Rollback containers
rollback_containers() {
    local version=$1
    log_info "Rolling back containers to version: $version"
    
    # Update image tags
    export API_IMAGE="ghcr.io/${GITHUB_REPOSITORY}-api:$version"
    export WEB_IMAGE="ghcr.io/${GITHUB_REPOSITORY}-web:$version"
    
    # Deploy previous version
    local compose_file="$PROJECT_ROOT/docker/docker-compose.yml"
    if [[ "$ENVIRONMENT" != "development" ]]; then
        compose_file="$PROJECT_ROOT/docker/docker-compose.$ENVIRONMENT.yml"
    fi
    
    docker-compose -f "$compose_file" pull
    docker-compose -f "$compose_file" up -d --remove-orphans
    
    # Wait for services
    sleep 10
    
    # Check health
    if check_health; then
        log_success "Container rollback completed"
    else
        log_error "Container rollback failed - services unhealthy"
        exit 1
    fi
}

# Emergency rollback
emergency_rollback() {
    log_warning "EMERGENCY ROLLBACK INITIATED"
    
    # Get last known good version
    local last_good_version=$(get_previous_version)
    log_info "Rolling back to last known good version: $last_good_version"
    
    # Stop current deployment immediately
    docker-compose -f "$PROJECT_ROOT/docker/docker-compose.$ENVIRONMENT.yml" down
    
    # Rollback containers first (faster)
    rollback_containers "$last_good_version"
    
    # Rollback database if needed
    if [[ "$ROLLBACK_DATABASE" == "true" ]]; then
        rollback_database "$last_good_version"
    fi
    
    # Send alerts
    send_alert "Emergency rollback completed to version $last_good_version"
}

# Standard rollback
standard_rollback() {
    local target_version=${VERSION:-$(get_previous_version)}
    
    log_info "Starting rollback to version: $target_version"
    
    # Confirm rollback
    if [[ "$ENVIRONMENT" == "production" && "$SKIP_CONFIRMATION" != "true" ]]; then
        read -p "Are you sure you want to rollback production to $target_version? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_info "Rollback cancelled"
            exit 0
        fi
    fi
    
    # Create backup of current state
    log_info "Creating backup of current state..."
    mkdir -p "$PROJECT_ROOT/backups/rollback"
    docker-compose -f "$PROJECT_ROOT/docker/docker-compose.$ENVIRONMENT.yml" \
        ps > "$PROJECT_ROOT/backups/rollback/state_$(date +%Y%m%d_%H%M%S).txt"
    
    # Rollback process
    rollback_containers "$target_version"
    
    # Rollback database if specified
    if [[ "$ROLLBACK_DATABASE" == "true" ]]; then
        rollback_database "$target_version"
    fi
    
    # Verify rollback
    run_smoke_tests
}

# Health check
check_health() {
    local health_url="http://localhost:8000/health"
    if curl -f -s "$health_url" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    local endpoints=(
        "/health"
        "/api/v1/marketplace/stats"
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

# Send alert
send_alert() {
    local message=$1
    
    # Send to Slack if configured
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
    
    # Log to file
    echo "[$(date)] $message" >> "$PROJECT_ROOT/logs/rollback.log"
}

# Update deployment history
update_history() {
    local version=$1
    echo "$version $(date +%Y-%m-%d_%H:%M:%S) ROLLBACK" >> "$PROJECT_ROOT/DEPLOYMENT_HISTORY"
}

# Main rollback flow
main() {
    # Load environment
    if [[ -f "$PROJECT_ROOT/.env.$ENVIRONMENT" ]]; then
        export $(grep -v '^#' "$PROJECT_ROOT/.env.$ENVIRONMENT" | xargs)
    fi
    
    # Handle rollback options
    case "$OPTION" in
        "--emergency")
            emergency_rollback
            ;;
        "--to-version")
            if [[ -z "$VERSION" ]]; then
                log_error "Version required with --to-version option"
                exit 1
            fi
            standard_rollback
            ;;
        *)
            standard_rollback
            ;;
    esac
    
    # Update deployment history
    update_history "${VERSION:-$(get_previous_version)}"
    
    log_success "Rollback completed successfully!"
}

# Run main function
main "$@"