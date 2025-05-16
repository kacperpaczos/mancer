#!/bin/bash
# Setup script for Docker test environment

# Check if docker and docker-compose are installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp env.example .env
    echo "Please edit .env file if needed and run this script again."
    exit 0
fi

# Build and start Docker containers
echo "Building and starting Docker containers..."
docker-compose up -d --build

# Wait for containers to start
echo "Waiting for containers to start..."
sleep 5

# Display container information
echo -e "\nContainer information:"
docker-compose ps

# Test SSH connection
echo -e "\nTesting SSH connections:"
source .env

echo -e "\nContainer 1 (${TEST_USER_1}@localhost:${SSH_PORT_1}):"
ssh -o "StrictHostKeyChecking=no" -p "${SSH_PORT_1}" "${TEST_USER_1}@localhost" "echo SSH connection successful; hostname; whoami"

echo -e "\nContainer 2 (${TEST_USER_2}@localhost:${SSH_PORT_2}):"
ssh -o "StrictHostKeyChecking=no" -p "${SSH_PORT_2}" "${TEST_USER_2}@localhost" "echo SSH connection successful; hostname; whoami"

echo -e "\nContainer 3 (${TEST_USER_3}@localhost:${SSH_PORT_3}):"
ssh -o "StrictHostKeyChecking=no" -p "${SSH_PORT_3}" "${TEST_USER_3}@localhost" "echo SSH connection successful; hostname; whoami"

echo -e "\nSetup completed. Docker test environment is ready."
echo "Use the following commands to connect to containers:"
echo "  ssh ${TEST_USER_1}@localhost -p ${SSH_PORT_1}"
echo "  ssh ${TEST_USER_2}@localhost -p ${SSH_PORT_2}"
echo "  ssh ${TEST_USER_3}@localhost -p ${SSH_PORT_3}" 