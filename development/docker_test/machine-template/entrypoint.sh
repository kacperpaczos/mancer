#!/bin/bash
# Container entrypoint script

# Setup network configuration if IP address is provided
if [ ! -z "$STATIC_IP" ]; then
    echo "Configuring static IP: $STATIC_IP"
    
    # Extract interface name (usually eth0 in Docker)
    INTERFACE=$(ip -o -4 route show to default | awk '{print $5}')
    
    if [ -z "$INTERFACE" ]; then
        echo "Warning: Could not determine network interface, using eth0"
        INTERFACE="eth0"
    fi
    
    # Extract gateway
    GATEWAY=$(ip -o -4 route show to default | awk '{print $3}')
    
    if [ -z "$GATEWAY" ]; then
        echo "Warning: Could not determine gateway, using network address with .1 suffix"
        # Assume gateway is first address in network
        NETWORK=$(echo $STATIC_IP | cut -d. -f1-3)
        GATEWAY="${NETWORK}.1"
    fi
    
    # Configure network
    echo "Network interface: $INTERFACE"
    echo "Gateway: $GATEWAY"
    
    # Add static IP to interface
    ip addr add $STATIC_IP/24 dev $INTERFACE || true
    
    # Add route if needed
    ip route add default via $GATEWAY dev $INTERFACE || true
    
    # Print network configuration
    echo "Network configuration:"
    ip addr show
    echo "Routing table:"
    ip route
fi

# Run environment setup if not already done
if [ ! -f "/tmp/.setup_done" ]; then
    # Create Python virtual environment
    mkdir -p /home/$(whoami)/projects
    cd /home/$(whoami)
    python3 -m venv venv
    chown -R $(whoami):$(whoami) /home/$(whoami)/venv
    chown -R $(whoami):$(whoami) /home/$(whoami)/projects

    # Setup bash profile
    echo 'alias python=python3' >> /home/$(whoami)/.bashrc
    echo 'export PATH=$PATH:/home/$(whoami)/venv/bin' >> /home/$(whoami)/.bashrc
    echo 'source /home/$(whoami)/venv/bin/activate' >> /home/$(whoami)/.bashrc

    # Install basic Python packages
    sudo -u $(whoami) bash -c "source /home/$(whoami)/venv/bin/activate && pip install --upgrade pip setuptools wheel"
    
    # Mark setup as done
    touch /tmp/.setup_done
    echo "Container setup completed successfully!"
fi

# Print host information
echo "Container hostname: $(hostname)"
echo "Container IP: $STATIC_IP"
echo "User: $(whoami)"
echo "Working directory: $(pwd)"

# Execute the command passed to docker run
exec "$@" 