#!/bin/bash
set -e

# Script to start development services

echo "Starting Bluelabel AIOS development services..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Change to project root
cd "$(dirname "$0")/.."

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Start services
echo "Starting MinIO, Redis, and PostgreSQL..."
$COMPOSE_CMD -f docker-compose.dev.yml up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 5

# Check service health
$COMPOSE_CMD -f docker-compose.dev.yml ps

# Create MinIO bucket for file storage
echo "Creating MinIO bucket..."
docker exec bluelabel-minio sh -c '
    until curl -s http://localhost:9000/minio/health/live; do
        echo "Waiting for MinIO..."
        sleep 2
    done
    mc alias set local http://localhost:9000 minioadmin minioadmin
    mc mb local/bluelabel-files --ignore-existing
    mc policy set public local/bluelabel-files
'

echo ""
echo "Development services started successfully!"
echo ""
echo "Service URLs:"
echo "- MinIO Console: http://localhost:9090 (minioadmin/minioadmin)"
echo "- Redis: localhost:6379"
echo "- PostgreSQL: localhost:5432 (postgres/postgres)"
echo ""
echo "Next steps:"
echo "1. Run database migrations: alembic upgrade head"
echo "2. Start the API server: ./scripts/run_api.sh"