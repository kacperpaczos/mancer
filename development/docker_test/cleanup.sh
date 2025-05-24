#!/bin/bash
# Script to clean up test environment

echo "Stopping and removing containers..."
docker-compose down

echo "Removing network..."
docker network rm docker_test_mancer_network 2>/dev/null || true

echo "Removing volumes..."
docker volume prune -f

echo "Cleaning up .env file..."
if [ -f .env ]; then
    rm .env
fi

echo "Cleanup completed!" 