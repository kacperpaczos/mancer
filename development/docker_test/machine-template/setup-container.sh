#!/bin/bash
# Container setup script

# Create Python virtual environment
mkdir -p /home/mancer/projects
cd /home/mancer
python3 -m venv venv
chown -R mancer:mancer /home/mancer/venv
chown -R mancer:mancer /home/mancer/projects

# Setup bash profile
echo 'alias python=python3' >> /home/mancer/.bashrc
echo 'export PATH=$PATH:/home/mancer/venv/bin' >> /home/mancer/.bashrc
echo 'source /home/mancer/venv/bin/activate' >> /home/mancer/.bashrc

# Install basic Python packages
sudo -u mancer bash -c "source /home/mancer/venv/bin/activate && pip install --upgrade pip setuptools wheel"

echo "Container setup completed successfully!" 