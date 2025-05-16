#!/bin/bash
set -e

# Script to start services locally without Docker (fallback option)

echo "Starting services locally without Docker..."
echo "Note: This is a fallback option. Using Docker is recommended."
echo ""

# Check for homebrew
if ! command -v brew &> /dev/null; then
    echo "Homebrew is required to install services. Please install it first."
    exit 1
fi

# Function to check and install service
check_and_install() {
    local service=$1
    local brew_name=$2
    
    if ! command -v $service &> /dev/null; then
        echo "$service not found. Installing via Homebrew..."
        brew install $brew_name
    else
        echo "$service is already installed."
    fi
}

# Check and install services
check_and_install "redis-server" "redis"
check_and_install "postgres" "postgresql@15"
check_and_install "minio" "minio"

# Start Redis
echo "Starting Redis..."
brew services start redis

# Start PostgreSQL
echo "Starting PostgreSQL..."
brew services start postgresql@15

# Start MinIO
echo "Starting MinIO..."
mkdir -p ~/minio/data
minio server ~/minio/data --console-address :9090 &

echo ""
echo "Services started locally!"
echo ""
echo "Service URLs:"
echo "- MinIO Console: http://localhost:9090 (use minioadmin/minioadmin)"
echo "- Redis: localhost:6379"
echo "- PostgreSQL: localhost:5432"
echo ""
echo "Note: To stop services:"
echo "- brew services stop redis"
echo "- brew services stop postgresql@15"
echo "- Kill the MinIO process (use 'ps aux | grep minio' to find it)"
echo ""
echo "Next steps:"
echo "1. Create PostgreSQL database: createdb bluelabel_aios"
echo "2. Run database migrations: alembic upgrade head"
echo "3. Start the API server: ./scripts/run_api.sh"