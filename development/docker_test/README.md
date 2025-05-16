# Docker Test Environment for Mancer

This directory contains Docker configurations to create a test environment for Mancer prototypes on Debian-based containers with SSH access.

## Overview

The setup provides:
- Multiple Debian containers with SSH enabled
- Python environments pre-configured
- Ability to test Mancer prototype SSH functionality
- Volume mapping for easy code sharing between host and containers

## Requirements

- Docker
- Docker Compose

## Setup

1. Copy the example environment file:
   ```
   cp env.example .env
   ```

2. Edit the `.env` file to customize user credentials and SSH ports if needed.

3. Run the setup script:
   ```
   ./setup.sh
   ```

The script will:
- Check if Docker and Docker Compose are installed
- Create the .env file if it doesn't exist
- Build and start the Docker containers
- Test SSH connections to all containers
- Display connection information

## Container Details

By default, three containers are created:

| Container Name | User     | Password      | SSH Port |
|----------------|----------|---------------|----------|
| mancer-test-1  | mancer1  | test_password1 | 2221     |
| mancer-test-2  | mancer2  | test_password2 | 2222     |
| mancer-test-3  | mancer3  | test_password3 | 2223     |

## Usage

### SSH Access

Connect to the containers using SSH:
```
ssh mancer1@localhost -p 2221
ssh mancer2@localhost -p 2222
ssh mancer3@localhost -p 2223
```

### Testing Mancer Prototypes

The Mancer project directory is mounted at `/home/[username]/mancer` in each container.

You can test the prototypes by running:
```
cd ~/mancer
python development/scripts/install_prototype_deps.py --all
python development/scripts/run_prototype.py [prototype_name]
```

### Using the systemctl Prototype

To test the systemctl prototype across containers:
```
cd ~/mancer
python prototypes/systemctl/main.py
```

Then add the other containers as servers with their credentials from the `.env` file.

## Management Commands

- Start containers: `docker-compose up -d`
- Stop containers: `docker-compose down`
- Rebuild containers: `docker-compose up -d --build`
- View container logs: `docker-compose logs -f`
- SSH into a container: `ssh [username]@localhost -p [port]`

## Troubleshooting

### SSH Connection Issues

If you're unable to connect via SSH, check:
1. Container status: `docker-compose ps`
2. Container logs: `docker-compose logs -f`
3. SSH service in container: `docker exec -it mancer-test-1 service ssh status`

### Permission Issues

If you encounter permission issues with the mounted volume:
```
docker exec -it mancer-test-1 chown -R mancer1:mancer1 /home/mancer1/mancer
```

## Customization

To add more containers or modify the configuration, edit:
- `docker-compose.yml`
- `env.example` (and your `.env` file)
- `Dockerfile` if you need to install additional system packages 