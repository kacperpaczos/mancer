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

if ! command -v jq &> /dev/null; then
    echo "jq is not installed. Please install jq first."
    exit 1
fi

# Check if presets.json exists
if [ ! -f presets.json ]; then
    echo "Error: presets.json not found. Please run manage_presets.sh first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from env.develop.test..."
    cp env.develop.test .env
    echo "Please edit .env file if needed and run this script again."
    exit 0
fi

# Function to validate preset
validate_preset() {
    local preset=$1
    if [ "$preset" != "none" ] && [ ! -d "presets/$preset" ]; then
        echo "Error: Preset '$preset' does not exist in presets directory"
        return 1
    fi
    return 0
}

# Get container configurations from presets.json
CONTAINER_1=$(jq -r '.containers."mancer-test-1".preset' presets.json)
CONTAINER_2=$(jq -r '.containers."mancer-test-2".preset' presets.json)
CONTAINER_3=$(jq -r '.containers."mancer-test-3".preset' presets.json)

# Validate presets
if ! validate_preset "$CONTAINER_1"; then
    exit 1
fi
if ! validate_preset "$CONTAINER_2"; then
    exit 1
fi
if ! validate_preset "$CONTAINER_3"; then
    exit 1
fi

# Update .env file with preset configurations
sed -i "s/^PRESET_1=.*/PRESET_1=$CONTAINER_1/" .env
sed -i "s/^PRESET_2=.*/PRESET_2=$CONTAINER_2/" .env
sed -i "s/^PRESET_3=.*/PRESET_3=$CONTAINER_3/" .env

# Build and start Docker containers
echo "Building and starting Docker containers..."
docker-compose up -d --build

# Wait for containers to start
echo "Waiting for containers to start..."
sleep 8

# Display container information
echo -e "\nContainer information:"
docker-compose ps

# Display network information
echo -e "\nNetwork information:"
docker network inspect docker_test_mancer_network | grep -A 20 "Containers"

# Test SSH connection
echo -e "\nTesting SSH connections:"
source .env

echo -e "\nContainer 1 (${TEST_USER_1}@10.100.2.101):"
ssh -o "StrictHostKeyChecking=no" -p "${SSH_PORT_1}" "${TEST_USER_1}@localhost" "echo SSH connection successful; hostname; ip addr show | grep 10.100.2"

echo -e "\nContainer 2 (${TEST_USER_2}@10.100.2.102):"
ssh -o "StrictHostKeyChecking=no" -p "${SSH_PORT_2}" "${TEST_USER_2}@localhost" "echo SSH connection successful; hostname; ip addr show | grep 10.100.2"

echo -e "\nContainer 3 (${TEST_USER_3}@10.100.2.103):"
ssh -o "StrictHostKeyChecking=no" -p "${SSH_PORT_3}" "${TEST_USER_3}@localhost" "echo SSH connection successful; hostname; ip addr show | grep 10.100.2"

# Test inter-container connectivity
echo -e "\nTesting inter-container connectivity:"
ssh -o "StrictHostKeyChecking=no" -p "${SSH_PORT_1}" "${TEST_USER_1}@localhost" "ping -c 2 10.100.2.102"

echo -e "\nSetup completed. Docker test environment is ready."
echo "Use the following commands to connect to containers:"
echo "  From host to containers:"
echo "    ssh ${TEST_USER_1}@localhost -p ${SSH_PORT_1}"
echo "    ssh ${TEST_USER_2}@localhost -p ${SSH_PORT_2}"
echo "    ssh ${TEST_USER_3}@localhost -p ${SSH_PORT_3}"
echo "  Between containers (from container 1 to 2):"
echo "    ssh ${TEST_USER_2}@10.100.2.102" 