#!/bin/bash
# LXC Container Setup Script for Mancer Integration Tests
#
# This script sets up a Debian LXC container with all necessary
# dependencies for running Mancer integration tests.

set -euo pipefail

# Configuration
CONTAINER_NAME="${CONTAINER_NAME:-mancer-test}"
TEMPLATE="${TEMPLATE:-debian}"
RELEASE="${RELEASE:-bullseye}"
MEMORY="${MEMORY:-512MB}"
CPUS="${CPUS:-1}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

error() {
    log "ERROR: $*" >&2
    exit 1
}

# Check if running as root or have sudo
if [[ $EUID -ne 0 ]]; then
    if ! command -v sudo &> /dev/null; then
        error "This script must be run as root or with sudo available"
    fi
    SUDO="sudo"
else
    SUDO=""
fi

# Check if lxc is installed
if ! command -v lxc-create &> /dev/null; then
    error "LXC is not installed. Please install LXC first."
fi

log "Starting LXC container setup for $CONTAINER_NAME"

# Destroy existing container if it exists
if $SUDO lxc-ls -1 | grep -q "^${CONTAINER_NAME}$"; then
    log "Destroying existing container $CONTAINER_NAME"
    $SUDO lxc-stop -n "$CONTAINER_NAME" 2>/dev/null || true
    $SUDO lxc-destroy -n "$CONTAINER_NAME"
fi

# Create new container
log "Creating LXC container $CONTAINER_NAME with template $TEMPLATE/$RELEASE"
$SUDO lxc-create -n "$CONTAINER_NAME" -t "$TEMPLATE" -- --release "$RELEASE" || {
    error "Failed to create LXC container"
}

# Configure container resources
log "Configuring container resources (memory: $MEMORY, cpus: $CPUS)"
$SUDO lxc-cgroup -n "$CONTAINER_NAME" memory.limit_in_bytes "$MEMORY"
$SUDO lxc-cgroup -n "$CONTAINER_NAME" cpuset.cpus "0-$((CPUS-1))"

# Start container
log "Starting container $CONTAINER_NAME"
$SUDO lxc-start -n "$CONTAINER_NAME"

# Wait for container to start
log "Waiting for container to fully start..."
sleep 10

# Check if container is running
if ! $SUDO lxc-info -n "$CONTAINER_NAME" | grep -q "RUNNING"; then
    error "Container failed to start"
fi

# Install required packages
log "Installing required packages in container"
$SUDO lxc-attach -n "$CONTAINER_NAME" -- apt-get update
$SUDO lxc-attach -n "$CONTAINER_NAME" -- apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    coreutils \
    findutils \
    grep \
    sed \
    awk \
    curl \
    wget \
    procps \
    hostname \
    util-linux \
    systemd \
    openssh-server || {
    error "Failed to install packages in container"
}

# Create test user
log "Creating test user 'mancer' in container"
$SUDO lxc-attach -n "$CONTAINER_NAME" -- useradd -m -s /bin/bash mancer || {
    error "Failed to create test user"
}

# Set up passwordless sudo for test user
$SUDO lxc-attach -n "$CONTAINER_NAME" -- bash -c "echo 'mancer ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/mancer"
$SUDO lxc-attach -n "$CONTAINER_NAME" -- chmod 440 /etc/sudoers.d/mancer

# Set up SSH keys for passwordless access (optional)
log "Setting up SSH access for testing"
$SUDO lxc-attach -n "$CONTAINER_NAME" -- mkdir -p /home/mancer/.ssh
$SUDO lxc-attach -n "$CONTAINER_NAME" -- chown mancer:mancer /home/mancer/.ssh
$SUDO lxc-attach -n "$CONTAINER_NAME" -- chmod 700 /home/mancer/.ssh

# Create test directories
log "Creating test directories"
$SUDO lxc-attach -n "$CONTAINER_NAME" -- mkdir -p /tmp/integration_test
$SUDO lxc-attach -n "$CONTAINER_NAME" -- mkdir -p /home/mancer/test_workspace
$SUDO lxc-attach -n "$CONTAINER_NAME" -- chown mancer:mancer /home/mancer/test_workspace

# Install Python test dependencies
log "Installing Python test dependencies"
$SUDO lxc-attach -n "$CONTAINER_NAME" -- pip3 install --break-system-packages \
    pytest \
    requests \
    pyyaml || {
    error "Failed to install Python dependencies"
}

# Configure systemd (if needed)
log "Configuring systemd services"
$SUDO lxc-attach -n "$CONTAINER_NAME" -- systemctl enable ssh
$SUDO lxc-attach -n "$CONTAINER_NAME" -- systemctl start ssh || {
    log "Warning: SSH service start failed (may not be critical)"
}

# Final container info
log "Container setup completed successfully!"
log "Container information:"
$SUDO lxc-info -n "$CONTAINER_NAME"

log "Container IP addresses:"
$SUDO lxc-attach -n "$CONTAINER_NAME" -- hostname -I

log "Test user access:"
$SUDO lxc-attach -n "$CONTAINER_NAME" -- su - mancer -c "whoami && pwd"

log "Setup complete. Container $CONTAINER_NAME is ready for integration tests."
