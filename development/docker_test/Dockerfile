FROM debian:bullseye

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages
RUN apt-get update && apt-get install -y \
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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Setup SSH server
RUN mkdir /var/run/sshd
RUN echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config

# Create a test user
ARG TEST_USER=mancer
ARG TEST_PASSWORD=mancer_test
ARG TEST_UID=1000

RUN useradd -m -s /bin/bash -u ${TEST_UID} ${TEST_USER} && \
    echo "${TEST_USER}:${TEST_PASSWORD}" | chpasswd && \
    adduser ${TEST_USER} sudo && \
    echo "${TEST_USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${TEST_USER}

# Copy setup script to prepare the system
COPY setup-container.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/setup-container.sh

# Expose SSH port
EXPOSE 22

# Start SSH service
CMD ["/usr/sbin/sshd", "-D"] 