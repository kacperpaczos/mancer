# Mancer Docker Test Environment

A comprehensive test environment for prototyping and testing Mancer solutions in Debian containers.

---

## Table of Contents
1. [What Has Been Done?](#what-has-been-done)
2. [Requirements](#requirements)
3. [Quick Start](#quick-start)
4. [Preset Management](#preset-management)
5. [Starting the Environment](#starting-the-environment)
6. [Accessing Containers](#accessing-containers)
7. [Cleaning Up the Environment](#cleaning-up-the-environment)
8. [Directory Structure](#directory-structure)
9. [Example Presets](#example-presets)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)
12. [Contact](#contact)

---

## What Has Been Done?
- **Interactive preset manager** (`manage_presets.sh`):
  - Create, remove, assign, enable/disable presets for containers.
  - Configuration is stored in `presets.json`.
- **Automated environment startup** (`start_test.sh`):
  - Loads configuration from `presets.json` and `.env`.
  - Builds and starts Docker containers.
  - Tests SSH connections and inter-container connectivity.
- **Environment cleanup** (`cleanup.sh`):
  - Removes containers, network, volumes, and the `.env` file.
- **Example presets**: `none`, `sac`, `basic_web`.

---

## Requirements
- Linux with sudo privileges
- Docker & Docker Compose
- jq
- git

---

## Quick Start
```bash
cd development/docker_test
cp env.develop.test .env
sudo chmod +x *.sh
```

---

## Preset Management

Start the preset manager:
```bash
./manage_presets.sh
```

Features:
- List available presets
- Assign presets to containers
- Create new presets (with automatic directory and setup script generation)
- Remove presets (if not in use)
- Enable/disable presets and containers

**Creating your own preset:**
1. Select "Create new preset" in the manager.
2. Enter a description.
3. Edit the file `presets/<name>/setup-<name>.sh` and the README.

---

## Starting the Environment

1. (Optional) Configure presets and assign them to containers using `manage_presets.sh`.
2. Start the environment:
```bash
sudo ./start_test.sh
```
- The script will automatically build and start containers according to the configuration.
- It will display container info and test SSH connections.

---

## Accessing Containers

From the host:
```bash
ssh mancer1@localhost -p 2221
ssh mancer2@localhost -p 2222
ssh mancer3@localhost -p 2223
```
From one container to another:
```bash
ssh mancer2@10.100.2.102
```

---

## Cleaning Up the Environment

To stop and remove the environment and clean up the `.env` file:
```bash
sudo ./cleanup.sh
```

---

## Directory Structure
```
development/docker_test/
├── machine-template/         # Container template
│   ├── Dockerfile           # Base image definition
│   └── entrypoint.sh        # Container startup script
├── presets/                 # Preset directories
│   ├── basic_web/           # Web preset
│   │   ├── setup-basic_web.sh
│   │   └── README.md
│   └── sac/                 # SAC preset
│       ├── setup-sac.sh
│       └── README.md
├── docker-compose.yml       # Container orchestration
├── env.develop.test         # .env file template
├── presets.json             # Preset and container configuration
├── start_test.sh            # Startup script
├── cleanup.sh               # Cleanup script
└── manage_presets.sh        # Preset manager
```

---

## Example Presets

- **none**: Clean Debian + Python + SSH
- **sac**: Config files + systemd services
- **basic_web**: Nginx + Apache + Flask

Each preset has its own directory with a setup script (`setup-<preset>.sh`) and README.

---

## Troubleshooting

### Permission Issues
- Make sure to run `start_test.sh` and `cleanup.sh` with `sudo`.
- If you encounter volume permission errors:
```bash
sudo chown -R mancer1:mancer1 /home/mancer1/mancer
```

### Network Issues
- Check network configuration:
```bash
docker network inspect docker_test_mancer_network
ping 10.100.2.102
```

### Service Issues
- Check service status inside a container:
```bash
systemctl status <service_name>
journalctl -u <service_name>
```

---

## Best Practices
- Always clean up the environment before restarting (`sudo ./cleanup.sh`).
- Create custom presets for specific test scenarios.
- Document changes in presets and use version control.
- Do not store sensitive data in presets – use environment variables.

---

## Contact
For questions or issues, open an issue in the repository or contact the Mancer team.