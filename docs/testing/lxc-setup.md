# LXC Setup Guide for Testing

This document provides comprehensive instructions for setting up and configuring LXC (Linux Containers) for running Mancer integration and E2E tests.

## Table of Contents

- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)
- [Maintenance](#maintenance)

## Overview

LXC (Linux Containers) is used to create isolated test environments for:

- **Integration Tests**: Single-container environments with real system commands
- **E2E Tests**: Multi-container environments simulating production setups

LXC provides lightweight virtualization that's faster than full VMs while maintaining isolation.

## System Requirements

### Hardware Requirements

- **CPU**: 2+ cores recommended (4+ for E2E tests)
- **RAM**: Minimum 2GB, 4GB+ recommended for E2E tests
- **Disk**: 10GB+ free space for containers and images
- **Network**: Internet connection for downloading templates

### Software Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, or similar)
- **Kernel**: Linux 4.15+ with LXC support
- **User**: Non-root user with sudo access
- **Python**: 3.9+ with pip

### Kernel Support

Verify kernel supports LXC:

```bash
# Check kernel version
uname -r

# Check for required kernel features
grep -E "CONFIG_CGROUP|CONFIG_NAMESPACE" /boot/config-$(uname -r)
```

Required kernel features:
- `CONFIG_CGROUP_*`
- `CONFIG_NAMESPACE_*`
- `CONFIG_VETH`
- `CONFIG_MACVLAN`

## Installation

### Ubuntu/Debian

```bash
# Update package list
sudo apt-get update

# Install LXC and utilities
sudo apt-get install -y lxc lxc-utils lxc-templates bridge-utils

# Install additional tools (for E2E tests)
sudo apt-get install -y postgresql redis-server supervisor

# Verify installation
lxc-ls --version
```

### Other Distributions

For other Linux distributions, refer to:
- **CentOS/RHEL**: Use `yum` or `dnf` with EPEL repository
- **Arch Linux**: `pacman -S lxc`
- **Fedora**: `dnf install lxc lxc-templates`

### Python Dependencies

```bash
# Install Python testing dependencies
pip install -r requirements.txt
pip install pytest pytest-xdist psutil
```

## Configuration

### Network Configuration

LXC uses a bridge network for container connectivity:

```bash
# Start LXC networking service
sudo systemctl start lxc-net

# Enable on boot
sudo systemctl enable lxc-net

# Verify bridge exists
ip link show lxcbr0

# Check bridge IP configuration
ip addr show lxcbr0
```

Expected output:
```
lxcbr0: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
    inet 10.0.3.1/24 ...
```

### User Permissions

Add your user to the LXC group:

```bash
# Add user to lxc group
sudo usermod -aG lxc $USER

# Verify group membership
groups | grep lxc

# Log out and back in for changes to take effect
# Or use: newgrp lxc
```

### LXC Configuration

Edit `/etc/lxc/default.conf` (optional, for custom defaults):

```bash
sudo nano /etc/lxc/default.conf
```

Example configuration:
```
lxc.net.0.type = veth
lxc.net.0.link = lxcbr0
lxc.net.0.flags = up
lxc.net.0.ipv4.address = 10.0.3.2/24
lxc.net.0.ipv4.gateway = 10.0.3.1
```

### Template Configuration

LXC templates are stored in `/usr/share/lxc/templates/`:

```bash
# List available templates
ls /usr/share/lxc/templates/

# Verify Debian template exists
ls /usr/share/lxc/templates/lxc-debian
```

## Verification

### Basic LXC Test

Create and destroy a test container:

```bash
# Create test container
sudo lxc-create -n test-container -t debian -- --release bullseye

# Start container
sudo lxc-start -n test-container

# Check status
sudo lxc-info -n test-container

# Access container
sudo lxc-attach -n test-container -- /bin/bash

# Stop and destroy
sudo lxc-stop -n test-container
sudo lxc-destroy -n test-container
```

### Network Verification

Test container networking:

```bash
# Create test container
sudo lxc-create -n net-test -t debian -- --release bullseye
sudo lxc-start -n net-test

# Wait for container to start
sleep 10

# Test connectivity
sudo lxc-attach -n net-test -- ping -c 3 8.8.8.8

# Test DNS resolution
sudo lxc-attach -n net-test -- nslookup google.com

# Cleanup
sudo lxc-stop -n net-test
sudo lxc-destroy -n net-test
```

### Integration Test Verification

Run a simple integration test:

```bash
# Run single integration test
pytest tests/integration/commands/test_ls_integration.py::TestLsIntegration::test_ls_basic_directory_listing --run-integration -v
```

## Troubleshooting

### Issue: Cannot Create Containers

**Symptoms**: `lxc-create` fails with permission errors

**Solutions**:
```bash
# Verify user is in lxc group
groups | grep lxc

# Check sudo access
sudo -v

# Verify LXC templates are installed
ls /usr/share/lxc/templates/lxc-debian

# Check disk space
df -h

# Check LXC service status
sudo systemctl status lxc-net
```

### Issue: Network Bridge Not Created

**Symptoms**: `lxcbr0` bridge doesn't exist

**Solutions**:
```bash
# Start LXC networking
sudo systemctl start lxc-net

# Check service status
sudo systemctl status lxc-net

# Manually create bridge (if needed)
sudo brctl addbr lxcbr0
sudo ip addr add 10.0.3.1/24 dev lxcbr0
sudo ip link set lxcbr0 up

# Verify bridge
ip link show lxcbr0
```

### Issue: Containers Cannot Reach Internet

**Symptoms**: Containers cannot ping external hosts

**Solutions**:
```bash
# Check NAT rules
sudo iptables -t nat -L -n | grep MASQUERADE

# Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# Make forwarding permanent
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf

# Check firewall rules
sudo iptables -L FORWARD -n

# Restart LXC networking
sudo systemctl restart lxc-net
```

### Issue: Container Startup Fails

**Symptoms**: Containers fail to start or hang

**Solutions**:
```bash
# Check container logs
sudo lxc-info -n <container-name> -L

# Check system resources
free -h
df -h

# Check kernel logs
dmesg | tail -50

# Verify cgroup support
mount | grep cgroup

# Try starting with debug
sudo lxc-start -n <container-name> -F -l DEBUG -o /tmp/lxc-debug.log
```

### Issue: Permission Denied in Containers

**Symptoms**: Cannot execute commands in containers

**Solutions**:
```bash
# Check container user configuration
sudo lxc-attach -n <container-name> -- id

# Verify test user exists
sudo lxc-attach -n <container-name> -- id mancer

# Check container permissions
sudo lxc-info -n <container-name> -c lxc.cgroup.devices.allow

# Recreate container with proper setup
sudo lxc-destroy -n <container-name>
# Run container_setup.sh again
```

### Issue: High Resource Usage

**Symptoms**: Containers consume too much CPU/memory

**Solutions**:
```bash
# Set resource limits in container config
sudo lxc-cgroup -n <container-name> memory.limit_in_bytes 512M
sudo lxc-cgroup -n <container-name> cpuset.cpus "0-1"

# Check resource usage
sudo lxc-info -n <container-name> -c lxc.cgroup.memory.usage_in_bytes

# Limit container count
# Reduce number of parallel test containers
```

## Advanced Configuration

### Custom Network Configuration

For custom network setups:

```bash
# Create custom bridge
sudo brctl addbr my-bridge
sudo ip addr add 192.168.100.1/24 dev my-bridge
sudo ip link set my-bridge up

# Configure container to use custom bridge
# Edit container config: /var/lib/lxc/<container>/config
# Set: lxc.net.0.link = my-bridge
```

### Resource Limits

Set container resource limits:

```bash
# Memory limit
sudo lxc-cgroup -n <container-name> memory.limit_in_bytes 1G

# CPU limit
sudo lxc-cgroup -n <container-name> cpuset.cpus "0-3"

# CPU shares (priority)
sudo lxc-cgroup -n <container-name> cpu.shares 512
```

### Container Snapshots

Create container snapshots for faster test setup:

```bash
# Create snapshot
sudo lxc-snapshot -n <container-name> -s snapshot1

# List snapshots
sudo lxc-snapshot -n <container-name> -L

# Restore snapshot
sudo lxc-snapshot -n <container-name> -r snapshot1

# Delete snapshot
sudo lxc-snapshot -n <container-name> -d snapshot1
```

### Multi-Container Networking

For E2E tests with multiple containers:

```bash
# Use network_config.sh script
cd tests/e2e/lxc
sudo ./network_config.sh mancer-e2e-app mancer-e2e-db mancer-e2e-worker

# Or configure manually
# See tests/e2e/lxc/network_config.sh for details
```

## Maintenance

### Regular Maintenance Tasks

1. **Clean Up Old Containers**:
   ```bash
   # List all containers
   sudo lxc-ls -1

   # Stop and destroy old test containers
   sudo lxc-stop -n <old-container>
   sudo lxc-destroy -n <old-container>
   ```

2. **Update Container Templates**:
   ```bash
   # Update package lists
   sudo apt-get update

   # Upgrade LXC packages
   sudo apt-get upgrade lxc lxc-utils lxc-templates
   ```

3. **Clean Up Container Images**:
   ```bash
   # List container images
   sudo lxc-ls --fancy

   # Remove unused images
   sudo lxc-destroy -n <unused-container>
   ```

4. **Monitor Disk Usage**:
   ```bash
   # Check container storage
   du -sh /var/lib/lxc/*

   # Clean up old logs
   sudo journalctl --vacuum-time=7d
   ```

### Performance Optimization

1. **Use Container Snapshots**: Create snapshots of base containers for faster test setup
2. **Parallel Execution**: Use `pytest-xdist` for parallel test execution
3. **Resource Limits**: Set appropriate limits to prevent resource exhaustion
4. **Template Caching**: Keep frequently used templates cached

### Backup and Recovery

1. **Backup Container Configs**:
   ```bash
   sudo tar -czf lxc-backup.tar.gz /var/lib/lxc/
   ```

2. **Backup Network Configuration**:
   ```bash
   sudo cp /etc/default/lxc-net /etc/default/lxc-net.backup
   ```

3. **Document Custom Configurations**: Keep notes on any custom LXC configurations

## Additional Resources

- **LXC Official Documentation**: https://linuxcontainers.org/lxc/
- **LXC Man Pages**: `man lxc-create`, `man lxc-start`, etc.
- **Mancer Test Documentation**: `docs/testing/plan.md`
- **Integration Test README**: `tests/integration/README.md`
- **E2E Test README**: `tests/e2e/README.md`

## Support

For LXC-specific issues:

1. Check this guide's troubleshooting section
2. Review LXC logs: `sudo journalctl -u lxc-net`
3. Check container logs: `sudo lxc-info -n <container> -L`
4. Consult LXC documentation: https://linuxcontainers.org/lxc/documentation/
5. Create an issue with test failure template: `.github/ISSUE_TEMPLATE/test_failure.md`
