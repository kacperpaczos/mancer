FROM jrei/systemd-debian

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages (including SSH server)
RUN apt-get update && apt-get install -y \
    systemd \
    openssh-server \
    python3 \
    python3-pip \
    python3-venv \
    vim \
    nano \
    curl \
    wget \
    git \
    sudo \
    iproute2 \
    iputils-ping \
    net-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Setup SSH server
RUN mkdir -p /var/run/sshd && \
    echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config && \
    echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config && \
    ln -sf /lib/systemd/system/ssh.service /etc/systemd/system/multi-user.target.wants/ssh.service

# Create a test user
ARG TEST_USER=mancer
ARG TEST_PASSWORD=mancer_test
ARG TEST_UID=1000

RUN useradd -m -s /bin/bash -u ${TEST_UID} ${TEST_USER} && \
    echo "${TEST_USER}:${TEST_PASSWORD}" | chpasswd && \
    adduser ${TEST_USER} sudo && \
    echo "${TEST_USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${TEST_USER}

# Create directory for presets
RUN mkdir -p /presets

# Copy setup script to prepare the system
COPY machine-template/entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Copy preset scripts
COPY presets/ /presets/
RUN find /presets -name "*.sh" -exec chmod +x {} \;

# Add preset installation capability
ARG PRESET=none
RUN if [ "$PRESET" != "none" ] && [ -f "/presets/$PRESET/setup-$PRESET.sh" ]; then \
        echo "Installing preset: $PRESET" && \
        /presets/$PRESET/setup-$PRESET.sh; \
    else \
        echo "No preset specified or preset not found"; \
    fi

# Expose SSH port
EXPOSE 22

# Allow systemd cgroups mount inside container runtime
VOLUME [ "/sys/fs/cgroup" ]

# Set entrypoint that prepares the environment and then starts systemd (PID 1)
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]