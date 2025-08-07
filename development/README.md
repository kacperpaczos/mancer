# Mancer Development Environment

This directory contains scripts and tools to help with the development and testing of Mancer prototypes.

## Project Structure

```
mancer/
├── src/                    # Mancer framework source code
├── prototypes/             # Directory with prototypes
│   ├── systemctl/          # Example prototype
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── .venv/          # Prototype's virtual environment
│   └── ...
├── development/            # Development scripts and tools
│   ├── scripts/            # Utility scripts
│   └── ...
└── ...
```

## Development Tools

The `development/scripts` directory contains utility scripts:

1. `install_prototype_deps.py` - installs dependencies for prototypes and Mancer in development mode
2. `run_prototype.py` - runs prototypes in their own virtual environments
3. `check_mancer_version.py` - checks Mancer versions installed in prototype environments
4. `make_requirements.py` - generates requirements.txt files for prototypes

## Setting up the Development Environment

### Installing Dependencies for a Prototype

```bash
python development/scripts/install_prototype_deps.py systemctl
```

This command will:
1. Create a virtual environment in the prototype directory
2. Install dependencies from the requirements.txt file
3. Install Mancer in development mode (-e)

To install dependencies for all prototypes:

```bash
python development/scripts/install_prototype_deps.py --all
```

### Generating a requirements.txt File

If a prototype doesn't have a requirements.txt file, you can generate one based on imports:

```bash
python development/scripts/make_requirements.py systemctl
```

For all prototypes:

```bash
python development/scripts/make_requirements.py --all
```

## Running Prototypes

To run a prototype in its own virtual environment:

```bash
python development/scripts/run_prototype.py systemctl
```

You can also pass arguments to the prototype:

```bash
python development/scripts/run_prototype.py systemctl arg1 arg2
```

To see a list of available prototypes:

```bash
python development/scripts/run_prototype.py --list
```

## Checking Mancer Versions

To check if all prototypes are using the latest version of Mancer:

```bash
python development/scripts/check_mancer_version.py
```

## Advantages of this Development Approach

1. **Isolation** - each prototype has its own virtual environment
2. **Consistency** - all prototypes use the same Mancer source code
3. **Fast development cycle** - changes in Mancer code are immediately available in all prototypes
4. **Independence** - ability to work on different prototypes in parallel

## Notes

- Scripts assume they are being run from the main project directory
- All scripts are written in Python and work on Linux/Unix systems
- On Windows systems, virtual environment activation paths may need modification 