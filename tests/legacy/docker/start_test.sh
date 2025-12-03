#!/bin/bash
# Setup script for Docker test environment

# Check if docker and docker compose are installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker compose command is available
docker compose version &> /dev/null
if [ $? -ne 0 ]; then
    echo "Docker Compose is not available. Please install Docker with Compose support."
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "jq is not installed. Trying to install..."
    if command -v apt >/dev/null 2>&1; then
        sudo apt update && sudo apt install -y jq
    else
        echo "apt not found. Please install jq manually."
        exit 1
    fi
fi

# Check if presets.json exists
if [ ! -f presets.json ]; then
    echo "Error: presets.json not found. Please run manage_presets.sh first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -n "File .env does not exist. Do you want to create it from env.develop.test? [Y/n]: "
    read answer
    if [[ "$answer" == "" || "$answer" == "T" || "$answer" == "t" || "$answer" == "y" || "$answer" == "Y" ]]; then
        cp env.develop.test .env
        echo "Created .env file. Do you want to edit it now? [y/N]: "
        read edit_answer
        if [[ "$edit_answer" == "t" || "$edit_answer" == "T" || "$edit_answer" == "y" || "$edit_answer" == "Y" ]]; then
            ${EDITOR:-nano} .env
        else
            echo "Continuing without editing .env file..."
        fi
    else
        echo "Cancelled. Create .env file manually before running this script again."
        exit 0
    fi
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
echo "Building and starting Docker containers in a new window..."

# Launch in a new terminal
gnome-terminal -- bash -c "cd \"$(pwd)\" && docker compose up -d --build && echo -e '\nContainers started. Press Enter to close this window...' && read" 2>/dev/null || \
xterm -e "cd \"$(pwd)\" && docker compose up -d --build && echo -e '\nContainers started. Press Enter to close this window...' && read" 2>/dev/null || \
x-terminal-emulator -e "cd \"$(pwd)\" && docker compose up -d --build && echo -e '\nContainers started. Press Enter to close this window...' && read" 2>/dev/null || \
{
  echo "Could not open a new terminal. Running in the same window..."
  docker compose up -d --build
}

# Wait for containers to start
echo "Waiting for containers to start..."
sleep 10

# Display container information
echo -e "\nContainer information:"
docker compose ps

# Display network information
echo -e "\nNetwork information:"
docker network inspect docker_test_mancer_network 2>/dev/null | grep -A 20 "Containers" || echo "Network does not exist yet"

# Test SSH connection
echo -e "\nTesting SSH connections:"
source .env

echo -e "\nContainer 1 (${TEST_USER_1}@10.100.2.101):"
ssh -o "StrictHostKeyChecking=no" -o "ConnectTimeout=5" -p "${SSH_PORT_1}" "${TEST_USER_1}@localhost" "echo SSH connection successful; hostname; ip addr show | grep 10.100.2" 2>/dev/null || echo "Container 1 is not available yet"

echo -e "\nContainer 2 (${TEST_USER_2}@10.100.2.102):"
ssh -o "StrictHostKeyChecking=no" -o "ConnectTimeout=5" -p "${SSH_PORT_2}" "${TEST_USER_2}@localhost" "echo SSH connection successful; hostname; ip addr show | grep 10.100.2" 2>/dev/null || echo "Container 2 is not available yet"

echo -e "\nContainer 3 (${TEST_USER_3}@10.100.2.103):"
ssh -o "StrictHostKeyChecking=no" -o "ConnectTimeout=5" -p "${SSH_PORT_3}" "${TEST_USER_3}@localhost" "echo SSH connection successful; hostname; ip addr show | grep 10.100.2" 2>/dev/null || echo "Container 3 is not available yet"

# Test inter-container connectivity
echo -e "\nTesting inter-container connectivity:"
ssh -o "StrictHostKeyChecking=no" -o "ConnectTimeout=5" -p "${SSH_PORT_1}" "${TEST_USER_1}@localhost" "ping -c 2 10.100.2.102" 2>/dev/null || echo "Container 1 is not available yet or cannot connect to container 2"

echo -e "\nSetup completed. Docker test environment is ready (or starting up)."
echo "Use the following commands to connect to containers:"
echo "  From host to containers:"
echo "    ssh ${TEST_USER_1}@localhost -p ${SSH_PORT_1}"
echo "    ssh ${TEST_USER_2}@localhost -p ${SSH_PORT_2}"
echo "    ssh ${TEST_USER_3}@localhost -p ${SSH_PORT_3}"
echo "  Between containers (from container 1 to 2):"
echo "    ssh ${TEST_USER_2}@10.100.2.102" 