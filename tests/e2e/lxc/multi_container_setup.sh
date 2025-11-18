#!/bin/bash
# Multi-Container LXC Setup Script for Mancer E2E Tests
#
# This script sets up multiple interconnected LXC containers
# for comprehensive end-to-end testing scenarios.

set -euo pipefail

# Configuration
APP_CONTAINER="${APP_CONTAINER:-mancer-e2e-app}"
DB_CONTAINER="${DB_CONTAINER:-mancer-e2e-db}"
WORKER_CONTAINER="${WORKER_CONTAINER:-mancer-e2e-worker}"
TEMPLATE="${TEMPLATE:-debian}"
RELEASE="${RELEASE:-bullseye}"
NETWORK_BRIDGE="${NETWORK_BRIDGE:-lxcbr0}"

# Resource allocation
APP_MEMORY="${APP_MEMORY:-1GB}"
APP_CPUS="${APP_CPUS:-2}"
DB_MEMORY="${DB_MEMORY:-512MB}"
DB_CPUS="${DB_CPUS:-1}"
WORKER_MEMORY="${WORKER_MEMORY:-512MB}"
WORKER_CPUS="${WORKER_CPUS:-1}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

error() {
    log "ERROR: $*" >&2
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    if ! command -v lxc-create &> /dev/null; then
        error "LXC is not installed. Please install LXC first."
    fi

    if ! command -v brctl &> /dev/null; then
        error "Bridge utilities not installed. Please install bridge-utils."
    fi

    # Check if running as root or have sudo
    if [[ $EUID -ne 0 ]]; then
        if ! command -v sudo &> /dev/null; then
            error "This script must be run as root or with sudo available"
        fi
        SUDO="sudo"
    else
        SUDO=""
    fi
}

# Create network bridge if it doesn't exist
setup_network_bridge() {
    log "Setting up network bridge..."

    if ! $SUDO brctl show | grep -q "$NETWORK_BRIDGE"; then
        log "Creating bridge $NETWORK_BRIDGE"
        $SUDO brctl addbr "$NETWORK_BRIDGE"
        $SUDO ip link set "$NETWORK_BRIDGE" up
        $SUDO ip addr add 10.0.3.1/24 dev "$NETWORK_BRIDGE"
    else
        log "Bridge $NETWORK_BRIDGE already exists"
    fi
}

# Create and configure a container
create_container() {
    local container_name="$1"
    local memory="$2"
    local cpus="$3"
    local ip_addr="$4"

    log "Creating container $container_name with ${memory} RAM, ${cpus} CPU(s)"

    # Destroy existing container if it exists
    if $SUDO lxc-ls -1 | grep -q "^${container_name}$"; then
        log "Destroying existing container $container_name"
        $SUDO lxc-stop -n "$container_name" 2>/dev/null || true
        $SUDO lxc-destroy -n "$container_name"
    fi

    # Create new container
    $SUDO lxc-create -n "$container_name" -t "$TEMPLATE" -- --release "$RELEASE" || {
        error "Failed to create container $container_name"
    }

    # Configure container resources
    $SUDO lxc-cgroup -n "$container_name" memory.limit_in_bytes "$memory"
    $SUDO lxc-cgroup -n "$container_name" cpuset.cpus "0-$((cpus-1))"

    # Configure networking
    $SUDO lxc-start -n "$container_name" -d

    # Wait for container to start
    for i in {1..30}; do
        if $SUDO lxc-info -n "$container_name" | grep -q "RUNNING"; then
            log "Container $container_name started successfully"
            break
        fi
        sleep 1
    done

    if ! $SUDO lxc-info -n "$container_name" | grep -q "RUNNING"; then
        error "Container $container_name failed to start"
    fi

    # Configure static IP if provided
    if [[ -n "$ip_addr" ]]; then
        log "Configuring static IP $ip_addr for $container_name"

        # Create network configuration inside container
        $SUDO lxc-attach -n "$container_name" -- bash -c "
            cat > /etc/network/interfaces << EOF
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
    address $ip_addr
    netmask 255.255.255.0
    gateway 10.0.3.1
    dns-nameservers 8.8.8.8 8.8.4.4
EOF
        "

        # Restart networking
        $SUDO lxc-attach -n "$container_name" -- systemctl restart networking 2>/dev/null || {
            $SUDO lxc-attach -n "$container_name" -- /etc/init.d/networking restart 2>/dev/null || {
                log "Warning: Network restart failed, container may need manual restart"
            }
        }
    fi
}

# Install common packages in a container
install_common_packages() {
    local container_name="$1"

    log "Installing common packages in $container_name"

    $SUDO lxc-attach -n "$container_name" -- apt-get update
    $SUDO lxc-attach -n "$container_name" -- apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        coreutils \
        curl \
        wget \
        net-tools \
        iputils-ping \
        dnsutils \
        procps \
        htop \
        vim \
        openssh-server \
        postgresql-client \
        redis-tools \
        jq \
        unzip \
        rsync || {
        error "Failed to install packages in $container_name"
    }
}

# Setup specific container roles
setup_app_container() {
    log "Setting up application container..."

    install_common_packages "$APP_CONTAINER"

    # Install additional app-specific packages
    $SUDO lxc-attach -n "$APP_CONTAINER" -- apt-get install -y \
        nginx \
        supervisor \
        git \
        build-essential \
        libpq-dev \
        libffi-dev \
        libssl-dev || {
        error "Failed to install app packages"
    }

    # Create application user
    $SUDO lxc-attach -n "$APP_CONTAINER" -- useradd -m -s /bin/bash app
    $SUDO lxc-attach -n "$APP_CONTAINER" -- usermod -aG sudo app
    $SUDO lxc-attach -n "$APP_CONTAINER" -- bash -c "echo 'app:app123' | chpasswd"

    # Setup application directories
    $SUDO lxc-attach -n "$APP_CONTAINER" -- mkdir -p /opt/mancer
    $SUDO lxc-attach -n "$APP_CONTAINER" -- chown app:app /opt/mancer

    log "Application container setup complete"
}

setup_db_container() {
    log "Setting up database container..."

    install_common_packages "$DB_CONTAINER"

    # Install database packages
    $SUDO lxc-attach -n "$DB_CONTAINER" -- apt-get install -y \
        postgresql \
        postgresql-contrib \
        redis-server \
        sqlite3 || {
        error "Failed to install database packages"
    }

    # Create database user
    $SUDO lxc-attach -n "$DB_CONTAINER" -- useradd -m -s /bin/bash dbadmin
    $SUDO lxc-attach -n "$DB_CONTAINER" -- usermod -aG sudo dbadmin
    $SUDO lxc-attach -n "$DB_CONTAINER" -- bash -c "echo 'dbadmin:db123' | chpasswd"

    # Setup database directories
    $SUDO lxc-attach -n "$DB_CONTAINER" -- mkdir -p /var/lib/postgresql/data
    $SUDO lxc-attach -n "$DB_CONTAINER" -- chown postgres:postgres /var/lib/postgresql/data

    # Basic PostgreSQL setup
    $SUDO lxc-attach -n "$DB_CONTAINER" -- sudo -u postgres createuser -s dbadmin 2>/dev/null || true
    $SUDO lxc-attach -n "$DB_CONTAINER" -- sudo -u postgres createdb -O dbadmin mancer_test 2>/dev/null || true

    # Start services
    $SUDO lxc-attach -n "$DB_CONTAINER" -- systemctl enable postgresql
    $SUDO lxc-attach -n "$DB_CONTAINER" -- systemctl start postgresql
    $SUDO lxc-attach -n "$DB_CONTAINER" -- systemctl enable redis-server
    $SUDO lxc-attach -n "$DB_CONTAINER" -- systemctl start redis-server

    log "Database container setup complete"
}

setup_worker_container() {
    log "Setting up worker container..."

    install_common_packages "$WORKER_CONTAINER"

    # Install worker-specific packages
    $SUDO lxc-attach -n "$WORKER_CONTAINER" -- apt-get install -y \
        supervisor \
        cron \
        at \
        build-essential \
        python3-dev \
        libpq-dev || {
        error "Failed to install worker packages"
    }

    # Create worker user
    $SUDO lxc-attach -n "$WORKER_CONTAINER" -- useradd -m -s /bin/bash worker
    $SUDO lxc-attach -n "$WORKER_CONTAINER" -- usermod -aG sudo worker
    $SUDO lxc-attach -n "$WORKER_CONTAINER" -- bash -c "echo 'worker:worker123' | chpasswd"

    # Setup worker directories
    $SUDO lxc-attach -n "$WORKER_CONTAINER" -- mkdir -p /opt/worker/jobs /opt/worker/logs
    $SUDO lxc-attach -n "$WORKER_CONTAINER" -- chown worker:worker /opt/worker/jobs /opt/worker/logs

    log "Worker container setup complete"
}

# Configure inter-container networking
setup_networking() {
    log "Configuring inter-container networking..."

    # Enable IP forwarding on host
    $SUDO sysctl -w net.ipv4.ip_forward=1

    # Setup NAT for containers to reach external network
    if ! $SUDO iptables -t nat -C POSTROUTING -s 10.0.3.0/24 -j MASQUERADE 2>/dev/null; then
        $SUDO iptables -t nat -A POSTROUTING -s 10.0.3.0/24 -j MASQUERADE
    fi

    # Allow forwarding
    if ! $SUDO iptables -C FORWARD -i "$NETWORK_BRIDGE" -j ACCEPT 2>/dev/null; then
        $SUDO iptables -C FORWARD -i "$NETWORK_BRIDGE" -o "$NETWORK_BRIDGE" -j ACCEPT 2>/dev/null || \
        $SUDO iptables -A FORWARD -i "$NETWORK_BRIDGE" -j ACCEPT
    fi

    log "Networking setup complete"
}

# Verify container connectivity
verify_setup() {
    log "Verifying multi-container setup..."

    # Test container connectivity
    for container in "$APP_CONTAINER" "$DB_CONTAINER" "$WORKER_CONTAINER"; do
        log "Testing $container..."

        # Check if container is running
        if ! $SUDO lxc-info -n "$container" | grep -q "RUNNING"; then
            error "Container $container is not running"
        fi

        # Test basic connectivity
        $SUDO lxc-attach -n "$container" -- ping -c 1 10.0.3.1 >/dev/null || {
            log "Warning: $container cannot reach bridge"
        }

        # Test package installation
        $SUDO lxc-attach -n "$container" -- which python3 >/dev/null || {
            error "Python3 not found in $container"
        }

        log "$container verification passed"
    done

    # Test inter-container connectivity
    app_ip=$($SUDO lxc-attach -n "$APP_CONTAINER" -- hostname -I | awk '{print $1}')
    db_ip=$($SUDO lxc-attach -n "$DB_CONTAINER" -- hostname -I | awk '{print $1}')

    if [[ -n "$app_ip" && -n "$db_ip" ]]; then
        log "Testing inter-container connectivity..."
        $SUDO lxc-attach -n "$APP_CONTAINER" -- ping -c 1 "$db_ip" >/dev/null && {
            log "Inter-container connectivity verified"
        } || {
            log "Warning: Inter-container ping failed (may be normal if firewall blocks ICMP)"
        }
    fi

    log "Multi-container setup verification complete"
}

# Print setup information
print_info() {
    log "Multi-container E2E environment setup completed successfully!"
    echo
    echo "Container Information:"
    echo "======================"
    echo "App Container:    $APP_CONTAINER"
    echo "DB Container:     $DB_CONTAINER"
    echo "Worker Container: $WORKER_CONTAINER"
    echo

    echo "Container IPs:"
    echo "=============="
    for container in "$APP_CONTAINER" "$DB_CONTAINER" "$WORKER_CONTAINER"; do
        ip=$($SUDO lxc-attach -n "$container" -- hostname -I 2>/dev/null | awk '{print $1}' || echo "N/A")
        printf "%-15s : %s\n" "$container" "$ip"
    done
    echo

    echo "Access Information:"
    echo "==================="
    echo "SSH to containers: ssh <username>@<container-ip>"
    echo "App user:         app / app123"
    echo "DB admin:         dbadmin / db123"
    echo "Worker user:      worker / worker123"
    echo

    echo "Services:"
    echo "========="
    echo "PostgreSQL:       Running on $DB_CONTAINER (port 5432)"
    echo "Redis:           Running on $DB_CONTAINER (port 6379)"
    echo

    echo "Next steps:"
    echo "==========="
    echo "1. Run E2E tests: pytest tests/e2e/ --run-e2e"
    echo "2. Monitor logs:  tail -f e2e_test.log"
    echo "3. Access containers: sudo lxc-attach -n <container-name>"
    echo "4. Cleanup: sudo ./multi_container_setup.sh --cleanup"
}

# Cleanup function
cleanup() {
    log "Cleaning up E2E containers..."

    for container in "$APP_CONTAINER" "$DB_CONTAINER" "$WORKER_CONTAINER"; do
        log "Stopping and destroying $container..."
        $SUDO lxc-stop -n "$container" 2>/dev/null || true
        $SUDO lxc-destroy -n "$container" 2>/dev/null || true
    done

    log "Cleanup complete"
}

# Main execution
main() {
    case "${1:-}" in
        --cleanup)
            cleanup
            exit 0
            ;;
        --help)
            echo "Usage: $0 [--cleanup] [--help]"
            echo
            echo "Multi-container LXC setup for Mancer E2E tests"
            echo
            echo "Options:"
            echo "  --cleanup    Remove all E2E containers"
            echo "  --help       Show this help message"
            echo
            echo "Environment variables:"
            echo "  APP_CONTAINER    App container name (default: mancer-e2e-app)"
            echo "  DB_CONTAINER     DB container name (default: mancer-e2e-db)"
            echo "  WORKER_CONTAINER Worker container name (default: mancer-e2e-worker)"
            exit 0
            ;;
    esac

    log "Starting multi-container E2E setup..."

    check_prerequisites
    setup_network_bridge

    # Create containers with static IPs
    create_container "$APP_CONTAINER" "$APP_MEMORY" "$APP_CPUS" "10.0.3.10"
    create_container "$DB_CONTAINER" "$DB_MEMORY" "$DB_CPUS" "10.0.3.11"
    create_container "$WORKER_CONTAINER" "$WORKER_MEMORY" "$WORKER_CPUS" "10.0.3.12"

    # Setup container roles
    setup_app_container
    setup_db_container
    setup_worker_container

    # Configure networking
    setup_networking

    # Verify setup
    verify_setup

    # Print information
    print_info
}

main "$@"