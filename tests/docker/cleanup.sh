#!/bin/bash
# Script to clean up test environment

if ! command -v jq >/dev/null 2>&1; then
    echo "jq is not installed. Trying to install..."
    if command -v apt >/dev/null 2>&1; then
        sudo apt update && sudo apt install -y jq
    else
        echo "apt not found. Please install jq manually."
        exit 1
    fi
fi

echo "Stopping and removing containers..."
docker compose down

echo "Removing network..."
docker network rm docker_test_mancer_network 2>/dev/null || true

echo "Removing volumes..."
docker volume prune -f

echo "Cleaning up .env file..."
if [ -f .env ]; then
    rm .env
fi

echo "Cleanup completed!" 