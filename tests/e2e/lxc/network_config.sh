#!/bin/bash
# Network Configuration Script for E2E Multi-Container Setup
#
# This script configures networking between multiple LXC containers
# for E2E testing scenarios.

set -euo pipefail

# Configuration
BRIDGE_NAME="${BRIDGE_NAME:-lxcbr0}"
SUBNET="${SUBNET:-10.0.3.0/24}"
GATEWAY="${GATEWAY:-10.0.3.1}"
DNS_SERVERS="${DNS_SERVERS:-8.8.8.8 8.8.4.4}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

error() {
    log "ERROR: $*" >&2
    exit 1
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    if command -v sudo &> /dev/null; then
        SUDO="sudo"
    else
        error "This script must be run as root or with sudo available"
    fi
else
    SUDO=""
fi

# Create network bridge
create_bridge() {
    log "Creating network bridge $BRIDGE_NAME..."

    # Check if bridge already exists
    if $SUDO ip link show "$BRIDGE_NAME" &>/dev/null; then
        log "Bridge $BRIDGE_NAME already exists"
        return 0
    fi

    # Create bridge
    $SUDO ip link add name "$BRIDGE_NAME" type bridge
    $SUDO ip addr add "$GATEWAY/24" dev "$BRIDGE_NAME"
    $SUDO ip link set "$BRIDGE_NAME" up

    log "Bridge $BRIDGE_NAME created successfully"
}

# Configure NAT and forwarding
configure_nat() {
    log "Configuring NAT and IP forwarding..."

    # Enable IP forwarding
    $SUDO sysctl -w net.ipv4.ip_forward=1

    # Add NAT rule if it doesn't exist
    if ! $SUDO iptables -t nat -C POSTROUTING -s "$SUBNET" -j MASQUERADE 2>/dev/null; then
        $SUDO iptables -t nat -A POSTROUTING -s "$SUBNET" -j MASQUERADE
        log "Added NAT rule for $SUBNET"
    else
        log "NAT rule already exists"
    fi

    # Allow forwarding between bridge interfaces
    if ! $SUDO iptables -C FORWARD -i "$BRIDGE_NAME" -j ACCEPT 2>/dev/null; then
        $SUDO iptables -A FORWARD -i "$BRIDGE_NAME" -j ACCEPT
        log "Added forwarding rule for $BRIDGE_NAME"
    fi

    log "NAT and forwarding configured"
}

# Configure container networking
configure_container_network() {
    local container_name="$1"
    local container_ip="$2"

    log "Configuring network for container $container_name ($container_ip)..."

    # Check if container is running
    if ! sudo lxc-info -n "$container_name" | grep -q "RUNNING"; then
        error "Container $container_name is not running"
    fi

    # Configure network interface inside container
    sudo lxc-attach -n "$container_name" -- bash -c "
        # Backup original interfaces file
        cp /etc/network/interfaces /etc/network/interfaces.backup 2>/dev/null || true

        # Configure static IP
        cat > /etc/network/interfaces << EOF
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
auto eth0
iface eth0 inet static
    address $container_ip
    netmask 255.255.255.0
    gateway $GATEWAY
    dns-nameservers $DNS_SERVERS
EOF

        # Restart networking
        systemctl restart networking 2>/dev/null || /etc/init.d/networking restart 2>/dev/null || {
            echo 'Warning: Network restart failed, container may need manual restart'
        }
    "

    log "Network configured for $container_name"
}

# Test network connectivity
test_connectivity() {
    local container_name="$1"

    log "Testing connectivity for $container_name..."

    # Test local connectivity
    if ! sudo lxc-attach -n "$container_name" -- ping -c 1 "$GATEWAY" &>/dev/null; then
        log "Warning: $container_name cannot reach gateway"
    else
        log "$container_name can reach gateway"
    fi

    # Test external connectivity
    if ! sudo lxc-attach -n "$container_name" -- ping -c 1 8.8.8.8 &>/dev/null; then
        log "Warning: $container_name cannot reach external network"
    else
        log "$container_name has external connectivity"
    fi

    # Test DNS resolution
    if ! sudo lxc-attach -n "$container_name" -- nslookup google.com &>/dev/null; then
        log "Warning: DNS resolution failed in $container_name"
    else
        log "DNS resolution works in $container_name"
    fi
}

# Setup DNS resolution
configure_dns() {
    log "Configuring DNS resolution..."

    # Create resolv.conf if it doesn't exist
    for container in "$@"; do
        sudo lxc-attach -n "$container" -- bash -c "
            # Backup existing resolv.conf
            cp /etc/resolv.conf /etc/resolv.conf.backup 2>/dev/null || true

            # Set DNS servers
            cat > /etc/resolv.conf << EOF
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
EOF
        "
        log "DNS configured for $container"
    done
}

# Setup hostname resolution
configure_hosts() {
    log "Configuring hostname resolution..."

    # Create hosts entries for inter-container communication
    local hosts_entries="
# E2E test environment hosts
10.0.3.10    mancer-e2e-app
10.0.3.11    mancer-e2e-db
10.0.3.12    mancer-e2e-worker
"

    for container in "$@"; do
        sudo lxc-attach -n "$container" -- bash -c "
            # Backup hosts file
            cp /etc/hosts /etc/hosts.backup 2>/dev/null || true

            # Add container hosts
            echo '$hosts_entries' >> /etc/hosts
        "
        log "Hosts configured for $container"
    done
}

# Configure firewall rules for inter-container communication
configure_firewall() {
    log "Configuring firewall rules..."

    # Allow all traffic between containers on the bridge network
    if ! $SUDO iptables -C FORWARD -i "$BRIDGE_NAME" -o "$BRIDGE_NAME" -j ACCEPT 2>/dev/null; then
        $SUDO iptables -A FORWARD -i "$BRIDGE_NAME" -o "$BRIDGE_NAME" -j ACCEPT
        log "Added inter-container forwarding rule"
    fi

    # Allow specific services (PostgreSQL, Redis, SSH, HTTP)
    local allowed_ports="22 80 443 5432 6379 8080"

    for port in $allowed_ports; do
        if ! $SUDO iptables -C FORWARD -i "$BRIDGE_NAME" -p tcp --dport "$port" -j ACCEPT 2>/dev/null; then
            $SUDO iptables -A FORWARD -i "$BRIDGE_NAME" -p tcp --dport "$port" -j ACCEPT
            log "Allowed port $port from containers"
        fi
    done

    log "Firewall rules configured"
}

# Persist iptables rules
persist_rules() {
    log "Persisting iptables rules..."

    # Save current rules
    $SUDO iptables-save | $SUDO tee /etc/iptables/rules.v4 > /dev/null

    # Create systemd service to restore rules on boot
    if [[ ! -f /etc/systemd/system/iptables-restore.service ]]; then
        cat | $SUDO tee /etc/systemd/system/iptables-restore.service > /dev/null << 'EOF'
[Unit]
Description=Restore iptables rules
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/iptables-restore /etc/iptables/rules.v4
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

        $SUDO systemctl enable iptables-restore.service
        log "Created iptables persistence service"
    fi
}

# Main execution
main() {
    case "${1:-}" in
        --help)
            echo "Usage: $0 [container1] [container2] ... [--help]"
            echo
            echo "Configure networking for E2E test containers"
            echo
            echo "Arguments:"
            echo "  container1, container2, ...    Container names to configure"
            echo
            echo "Environment variables:"
            echo "  BRIDGE_NAME    Bridge name (default: lxcbr0)"
            echo "  SUBNET         Network subnet (default: 10.0.3.0/24)"
            echo "  GATEWAY        Gateway IP (default: 10.0.3.1)"
            echo "  DNS_SERVERS    DNS servers (default: '8.8.8.8 8.8.4.4')"
            exit 0
            ;;
    esac

    local containers=("$@")

    if [[ ${#containers[@]} -eq 0 ]]; then
        echo "Error: No containers specified"
        echo "Usage: $0 container1 [container2] ..."
        exit 1
    fi

    log "Starting network configuration for E2E containers..."

    create_bridge
    configure_nat
    configure_firewall

    # Configure each container
    declare -A container_ips=(
        ["mancer-e2e-app"]="10.0.3.10"
        ["mancer-e2e-db"]="10.0.3.11"
        ["mancer-e2e-worker"]="10.0.3.12"
    )

    for container in "${containers[@]}"; do
        container_ip="${container_ips[$container]:-}"
        if [[ -z "$container_ip" ]]; then
            log "Warning: No IP configured for $container, using DHCP"
            continue
        fi

        configure_container_network "$container" "$container_ip"
        test_connectivity "$container"
    done

    configure_dns "${containers[@]}"
    configure_hosts "${containers[@]}"
    persist_rules

    log "Network configuration completed successfully"
    echo
    echo "Network Summary:"
    echo "================"
    echo "Bridge:     $BRIDGE_NAME ($SUBNET)"
    echo "Gateway:    $GATEWAY"
    echo "DNS:        $DNS_SERVERS"
    echo
    echo "Container IPs:"
    for container in "${!container_ips[@]}"; do
        printf "  %-20s %s\n" "$container:" "${container_ips[$container]}"
    done
}

main "$@"