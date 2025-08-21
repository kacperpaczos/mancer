#!/bin/bash

# Mancer Development Tools (mancer_tools.sh)
# Script for managing Mancer development environment

# Setting colors for display
YELLOW="\033[1;33m"
GREEN="\033[1;32m"
RED="\033[1;31m"
BLUE="\033[1;34m"
RESET="\033[0m"

# Change to the project root directory
cd "$(dirname "$0")/.." || exit 1

# Function to display help
show_help() {
    echo -e "${BLUE}Mancer Development Tools - help${RESET}"
    echo
    echo "Usage: $0 [option] [parameters]"
    echo
    echo -e "${YELLOW}Available options:${RESET}"
    echo "  -h, --help              Display this help"
    echo "  -i, --install           Install development environment"
    echo "  -r, --run               Run Mancer application"
    echo "  -t, --test [type]       Run tests (all, unit, integration, privileged)"
    echo "  -b, --build [format]    Build package (all, wheel, sdist)"
    echo "  -u, --uninstall         Remove development environment"
    echo "  -v, --version           Display current Mancer version"
    echo "  -f, --force             Force operations without asking (for -i, -u)"
    echo "  -d, --docs [action]     Documentation management (dev, build, deploy)"
    echo
    echo "Examples:"
    echo "  $0                      Run interactive menu"
    echo "  $0 --install            Install development environment"
    echo "  $0 --test unit          Run unit tests"
    echo "  $0 --build wheel        Build package in wheel format"
    echo "  $0 --uninstall --force  Remove development environment without asking"
    echo
}

# Function to display banner
show_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║             MANCER - DEVELOPMENT TOOLS                 ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
}

# Function to display main menu
show_menu() {
    echo -e "${YELLOW}Select operation:${RESET}"
    echo "1) Install development environment"
    echo "2) Run Mancer application"
    echo "3) Run tests"
    echo "4) Build package"
    echo "5) Remove development environment"
    echo "6) Check Mancer version"
    echo "7) Documentation management"
    echo "8) Version management"
    echo "0) Exit"
    echo
    echo -n "Your choice [0-8]: "
}

# Function checking if we're in virtualenv
check_venv() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        return 0  # We're in venv
    else
        return 1  # We're not in venv
    fi
}

# Function activating virtualenv
activate_venv() {
    if ! check_venv; then
        if [ -d ".venv" ]; then
            echo -e "${YELLOW}Activating virtual environment...${RESET}"
            # shellcheck disable=SC1091
            source .venv/bin/activate
            echo -e "${GREEN}Virtual environment activated.${RESET}"
            return 0
        else
            echo -e "${RED}Virtual environment doesn't exist.${RESET}"
            echo -e "${YELLOW}First install the development environment (option 1).${RESET}"
            return 1
        fi
    else
        echo -e "${GREEN}You're already in a virtual environment.${RESET}"
        return 0
    fi
}

# Function getting version from setup.py
get_version() {
    if [ -f "setup.py" ]; then
        VERSION=$(grep -o 'version="[0-9]*\.[0-9]*\.[0-9]*"' setup.py | grep -o '[0-9]*\.[0-9]*\.[0-9]*')
        echo -e "${GREEN}Current Mancer version: ${YELLOW}$VERSION${RESET}"
    else
        echo -e "${RED}File setup.py not found.${RESET}"
        return 1
    fi
}

# Function updating version in setup.py (increments Z in X.Y.Z)
update_version() {
    if [ -f "setup.py" ]; then
        # Find current version
        VERSION=$(grep -o 'version="[0-9]*\.[0-9]*\.[0-9]*"' setup.py | grep -o '[0-9]*\.[0-9]*\.[0-9]*')
        
        if [ -n "$VERSION" ]; then
            # Get version components
            X=$(echo "$VERSION" | cut -d. -f1)
            Y=$(echo "$VERSION" | cut -d. -f2)
            Z=$(echo "$VERSION" | cut -d. -f3)
            
            # Increment Z
            Z=$((Z + 1))
            NEW_VERSION="$X.$Y.$Z"
            
            # Update setup.py file
            sed -i "s/version=\"$VERSION\"/version=\"$NEW_VERSION\"/" setup.py
            
            echo -e "${GREEN}Updated version from ${YELLOW}$VERSION${GREEN} to ${YELLOW}$NEW_VERSION${RESET}"
            return 0
        else
            echo -e "${RED}Version not found in setup.py file.${RESET}"
            return 1
        fi
    else
        echo -e "${RED}File setup.py not found.${RESET}"
        return 1
    fi
}

# Function installing development environment
install_dev_env() {
    echo -e "${YELLOW}Installing development environment...${RESET}"
    
    # Note: Version management is now available in option 8 (Version management)
    
    # Check if virtualenv already exists
    if [ -d ".venv" ] || ls -d .venv-* 2>/dev/null | grep -q .; then
        if [ "$FORCE_MODE" != "true" ]; then
            echo -e "${YELLOW}Virtual environment(s) already exist.${RESET}"
            read -rp "Do you want to replace them? [y/N]: " response
            if [[ $response =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}Removing existing environment(s)...${RESET}"
                rm -rf .venv .venv-*
            else
                echo -e "${YELLOW}Skipping environment creation.${RESET}"
            fi
        else
            echo -e "${YELLOW}Virtual environment(s) already exist. Removing (forced mode)...${RESET}"
            rm -rf .venv .venv-*
        fi
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Creating new virtual environment...${RESET}"
        python3 -m venv .venv
        if [ $? -ne 0 ]; then
            echo -e "${RED}Error creating virtual environment.${RESET}"
            return 1
        fi
        echo -e "${GREEN}Virtual environment created successfully.${RESET}"
    fi
    
    # Activate environment
    activate_venv
    
    # Install package
    echo -e "${YELLOW}Updating pip...${RESET}"
    pip install --upgrade pip
    
    echo -e "${YELLOW}Installing dependencies...${RESET}"
    pip install -r requirements.txt
    
    echo -e "${YELLOW}Installing package in development mode...${RESET}"
    pip install -e .
    
    echo -e "${GREEN}Development environment installation completed successfully!${RESET}"
    echo -e "${YELLOW}-------------------------------------------------------------${RESET}"
    echo -e "${YELLOW}To activate the virtual environment in the future, run:${RESET}"
    echo -e "${GREEN}source .venv/bin/activate${RESET}"
    echo -e "${YELLOW}Or use this script with --run option to automatically activate it.${RESET}"
    echo -e "${YELLOW}-------------------------------------------------------------${RESET}"
    return 0
}

# Function running the application
run_app() {
    echo -e "${YELLOW}Running Mancer application...${RESET}"
    
    # Check if we're in a virtual environment
    if ! activate_venv; then
        return 1
    fi
    
    # Check if startup file exists
    if [ -f "src/mancer/main.py" ]; then
        echo -e "${YELLOW}Starting Mancer...${RESET}"
        python -m mancer.main
    else
        echo -e "${RED}Application startup file not found.${RESET}"
        return 1
    fi
}

# Function running tests
run_tests() {
    echo -e "${YELLOW}Running tests...${RESET}"
    local test_type="$1"
    local verbose="$2"
    local parallel="$3"
    local coverage="$4"
    local html_report="$5"
    
    # Check if we're in a virtual environment
    if ! activate_venv; then
        return 1
    fi
    
    # If no test type and we're not in non-interactive mode
    if [ -z "$test_type" ] && [ "$NON_INTERACTIVE" != "true" ]; then
        # Submenu for tests
        echo -e "${YELLOW}Select test type:${RESET}"
        echo "1) All tests"
        echo "2) Unit tests"
        echo "3) Integration tests"
        echo "4) Privileged tests"
        echo "0) Return to main menu"
        echo
        read -rp "Your choice [0-4]: " test_choice
        
        case $test_choice in
            0)
                return 0
                ;;
            1)
                test_type="all"
                ;;
            2)
                test_type="unit"
                ;;
            3)
                test_type="integration"
                ;;
            4)
                test_type="privileged"
                ;;
            *)
                echo -e "${RED}Invalid choice.${RESET}"
                return 1
                ;;
        esac
        
        # Test options
        echo -e "${YELLOW}Test options:${RESET}"
        read -rp "Verbose mode? [y/N]: " verbose
        read -rp "Parallel tests? [y/N]: " parallel
        read -rp "Code coverage report? [y/N]: " coverage
        
        if [[ $coverage =~ ^[Yy]$ ]]; then
            read -rp "HTML report? [y/N]: " html_report
        fi
    fi
    
    # Install test dependencies
    echo -e "${YELLOW}Installing required test packages...${RESET}"
    pip install pytest pytest-cov pytest-xdist pytest-mock
    
    # Building command
    cmd="python -m pytest"
    
    if [[ $test_type == "unit" ]]; then
        cmd="$cmd tests/unit"
    elif [[ $test_type == "integration" ]]; then
        cmd="$cmd -m integration"
    elif [[ $test_type == "privileged" ]]; then
        cmd="$cmd -m privileged"
    fi
    
    if [[ $verbose =~ ^[Yy]$ ]]; then
        cmd="$cmd -v"
    fi
    
    if [[ $parallel =~ ^[Yy]$ ]]; then
        cmd="$cmd -n auto"
    fi
    
    if [[ $coverage =~ ^[Yy]$ ]]; then
        cmd="$cmd --cov=src/mancer --cov-report=term"
        if [[ $html_report =~ ^[Yy]$ ]]; then
            cmd="$cmd --cov-report=html"
        fi
    fi
    
    # Run tests
    echo -e "${YELLOW}Running tests: ${RESET}$cmd"
    eval "$cmd"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Tests completed successfully.${RESET}"
    else
        echo -e "${RED}Some tests failed.${RESET}"
    fi
}

# Function building package
build_package() {
    echo -e "${YELLOW}Building distribution package...${RESET}"
    local build_format="$1"
    local do_clean="$2"
    local do_install="$3"
    
    # Check if we're in a virtual environment
    if ! activate_venv; then
        return 1
    fi
    
    # Install build dependencies
    echo -e "${YELLOW}Installing required build packages...${RESET}"
    pip install wheel setuptools build twine
    
    # If no format provided and we're not in non-interactive mode
    if [ -z "$build_format" ] && [ "$NON_INTERACTIVE" != "true" ]; then
        # Submenu for build options
        echo -e "${YELLOW}Build options:${RESET}"
        echo "1) All formats (wheel + sdist)"
        echo "2) Wheel only (.whl)"
        echo "3) Source distribution only (.tar.gz)"
        echo "0) Return to main menu"
        echo
        read -rp "Your choice [0-3]: " build_choice
        
        case $build_choice in
            0)
                return 0
                ;;
            1)
                build_format="all"
                ;;
            2)
                build_format="wheel"
                ;;
            3)
                build_format="sdist"
                ;;
            *)
                echo -e "${RED}Invalid choice.${RESET}"
                return 1
                ;;
        esac
        
        # Whether to clean directories
        read -rp "Clean build/dist directories before building? [Y/n]: " clean
        if [[ ! $clean =~ ^[Nn]$ ]]; then
            do_clean="true"
        fi
    fi
    
    # Set default values if not provided
    if [ -z "$build_format" ]; then
        build_format="all"
    fi
    
    # Whether to clean directories
    if [ "$do_clean" == "true" ]; then
        echo -e "${YELLOW}Cleaning directories...${RESET}"
        rm -rf build dist *.egg-info
    fi
    
    # Build package
    echo -e "${YELLOW}Building package...${RESET}"
    if [[ $build_format == "wheel" ]]; then
        python -m build --wheel
    elif [[ $build_format == "sdist" ]]; then
        python -m build --sdist
    else
        python -m build
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Package built successfully.${RESET}"
        
        # Check package for PyPI compatibility
        echo -e "${YELLOW}Checking PyPI compatibility...${RESET}"
        twine check dist/*
        
        # Whether to install locally
        if [ "$NON_INTERACTIVE" != "true" ] && [ -z "$do_install" ]; then
            read -rp "Install package locally? [y/N]: " install_local
            if [[ $install_local =~ ^[Yy]$ ]]; then
                do_install="true"
            fi
        fi
        
        if [ "$do_install" == "true" ]; then
            echo -e "${YELLOW}Installing package...${RESET}"
            pip install --force-reinstall dist/*.whl
            echo -e "${GREEN}Package installed locally.${RESET}"
        fi
    else
        echo -e "${RED}Error building package.${RESET}"
    fi
}

# Function removing development environment
uninstall_dev_env() {
    echo -e "${YELLOW}Removing development environment...${RESET}"
    
    # Check if we're in a virtual environment
    if [ -n "$VIRTUAL_ENV" ]; then
        echo -e "${RED}Cannot remove active virtual environment.${RESET}"
        echo -e "${YELLOW}First deactivate the environment with 'deactivate' command, then run the script again.${RESET}"
        return 1
    fi
    
    # Confirm removal if not in forced mode
    if [ "$FORCE_MODE" != "true" ] && [ "$NON_INTERACTIVE" != "true" ]; then
        echo -e "${RED}WARNING: This operation will remove:${RESET}"
        echo "  - Python virtual environment (.venv)"
        echo "  - Installation files (*.egg-info, __pycache__, etc.)"
        echo "  - Build and dist directories (if they exist)"
        echo
        read -rp "Are you sure you want to continue? [y/N]: " confirm
        
        if [[ ! $confirm =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Environment removal cancelled.${RESET}"
            return 0
        fi
    elif [ "$FORCE_MODE" == "true" ]; then
        echo -e "${YELLOW}Forced mode: removing without confirmation.${RESET}"
    fi
    
    # Remove environment
    if [ -d ".venv" ] || ls -d .venv-* 2>/dev/null | grep -q .; then
        echo -e "${YELLOW}Removing virtual environment(s)...${RESET}"
        rm -rf .venv .venv-*
    fi
    
    # Remove installation files
    echo -e "${YELLOW}Removing installation files...${RESET}"
    rm -rf src/mancer.egg-info
    find . -name "__pycache__" -type d -exec rm -rf {} +  2>/dev/null || true
    find . -name "*.pyc" -delete
    
    # Remove build and dist directories
    if [ -d "build" ] || [ -d "dist" ]; then
        echo -e "${YELLOW}Removing build and dist directories...${RESET}"
        rm -rf build dist
    fi
    
    echo -e "${GREEN}Development environment successfully removed.${RESET}"
    echo -e "${YELLOW}To reinstall the environment, use option 1 in the main menu.${RESET}"
}

# Function managing documentation
docs_management() {
    echo -e "${YELLOW}Documentation management${RESET}"
    echo "1) Start documentation server (dev)"
    echo "2) Build documentation (build)"
    echo "3) Deploy to GitHub Pages (deploy)"
    echo "0) Return to main menu"
    read -r docs_choice
    case $docs_choice in
        1)
            mkdocs serve
            ;;
        2)
            mkdocs build
            ;;
        3)
            deploy_docs
            ;;
        0)
            return
            ;;
        *)
            echo "Invalid choice."
            ;;
    esac
}

# Function deploying documentation
deploy_docs() {
    echo -e "${YELLOW}Deploying documentation to GitHub Pages...${RESET}"
    mkdocs gh-deploy
}

# Function managing versions
version_management() {
    echo -e "${YELLOW}Version management${RESET}"
    echo "1) Check current version"
    echo "2) Increment version (patch)"
    echo "3) Increment version (minor)"
    echo "4) Increment version (major)"
    echo "5) Set specific version"
    echo "0) Return to main menu"
    read -r version_choice
    
    case $version_choice in
        1)
            get_version
            ;;
        2)
            increment_version "patch"
            ;;
        3)
            increment_version "minor"
            ;;
        4)
            increment_version "major"
            ;;
        5)
            set_specific_version
            ;;
        0)
            return
            ;;
        *)
            echo "Invalid choice."
            ;;
    esac
}

# Function to increment version by type
increment_version() {
    local increment_type="$1"
    
    if [ -f "setup.py" ]; then
        # Find current version
        VERSION=$(grep -o 'version="[0-9]*\.[0-9]*\.[0-9]*"' setup.py | grep -o '[0-9]*\.[0-9]*\.[0-9]*')
        
        if [ -n "$VERSION" ]; then
            # Get version components
            X=$(echo "$VERSION" | cut -d. -f1)
            Y=$(echo "$VERSION" | cut -d. -f2)
            Z=$(echo "$VERSION" | cut -d. -f3)
            
            case $increment_type in
                "patch")
                    Z=$((Z + 1))
                    NEW_VERSION="$X.$Y.$Z"
                    ;;
                "minor")
                    Y=$((Y + 1))
                    Z=0
                    NEW_VERSION="$X.$Y.$Z"
                    ;;
                "major")
                    X=$((X + 1))
                    Y=0
                    Z=0
                    NEW_VERSION="$X.$Y.$Z"
                    ;;
                *)
                    echo -e "${RED}Invalid increment type: $increment_type${RESET}"
                    return 1
                    ;;
            esac
            
            # Update setup.py file
            sed -i "s/version=\"$VERSION\"/version=\"$NEW_VERSION\"/" setup.py
            
            echo -e "${GREEN}Updated version from ${YELLOW}$VERSION${GREEN} to ${YELLOW}$NEW_VERSION${RESET}"
            return 0
        else
            echo -e "${RED}Version not found in setup.py file.${RESET}"
            return 1
        fi
    else
        echo -e "${RED}File setup.py not found.${RESET}"
        return 1
    fi
}

# Function to set specific version
set_specific_version() {
    echo -e "${YELLOW}Enter new version (format: X.Y.Z): ${RESET}"
    read -r new_version
    
    if [[ $new_version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        if [ -f "setup.py" ]; then
            # Find current version
            VERSION=$(grep -o 'version="[0-9]*\.[0-9]*\.[0-9]*"' setup.py | grep -o '[0-9]*\.[0-9]*\.[0-9]*')
            
            if [ -n "$VERSION" ]; then
                # Update setup.py file
                sed -i "s/version=\"$VERSION\"/version=\"$new_version\"/" setup.py"
                
                echo -e "${GREEN}Updated version from ${YELLOW}$VERSION${GREEN} to ${YELLOW}$new_version${RESET}"
                return 0
            else
                echo -e "${RED}Version not found in setup.py file.${RESET}"
                return 1
            fi
        else
            echo -e "${RED}File setup.py not found.${RESET}"
            return 1
        fi
    else
        echo -e "${RED}Invalid version format. Use X.Y.Z format.${RESET}"
        return 1
    fi
}

# Process command line parameters
process_args() {
    # Check if we have any arguments
    if [ $# -eq 0 ]; then
        # No arguments, run interactive mode
        interactive_mode
        exit 0
    fi
    
    NON_INTERACTIVE="true"
    
    while [ $# -gt 0 ]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -i|--install)
                install_dev_env
                exit $?
                ;;
            -r|--run)
                run_app
                exit $?
                ;;
            -t|--test)
                shift
                test_type="$1"
                if [ -z "$test_type" ] || [[ "$test_type" == -* ]]; then
                    # No test type, use default
                    test_type="all"
                    # Return argument if it's a flag
                    if [[ "$test_type" == -* ]]; then
                        set -- "$test_type" "$@"
                    fi
                else
                    shift
                fi
                
                # Check if test_type is valid
                if [[ ! "$test_type" =~ ^(all|unit|integration|privileged)$ ]]; then
                    echo -e "${RED}Invalid test type: $test_type${RESET}"
                    echo "Allowed types: all, unit, integration, privileged"
                    exit 1
                fi
                
                # Check additional test options
                verbose="n"
                parallel="n"
                coverage="n"
                html_report="n"
                
                # Check options in remaining arguments
                while [ $# -gt 0 ]; do
                    case "$1" in
                        --verbose|-v)
                            verbose="y"
                            shift
                            ;;
                        --parallel|-p)
                            parallel="y"
                            shift
                            ;;
                        --coverage|-c)
                            coverage="y"
                            shift
                            ;;
                        --html)
                            html_report="y"
                            shift
                            ;;
                        *)
                            # End processing test options
                            break
                            ;;
                    esac
                done
                
                run_tests "$test_type" "$verbose" "$parallel" "$coverage" "$html_report"
                exit $?
                ;;
            -b|--build)
                shift
                build_format="$1"
                if [ -z "$build_format" ] || [[ "$build_format" == -* ]]; then
                    # No format, use default
                    build_format="all"
                    # Return argument if it's a flag
                    if [[ "$build_format" == -* ]]; then
                        set -- "$build_format" "$@"
                    fi
                else
                    shift
                fi
                
                # Check if build_format is valid
                if [[ ! "$build_format" =~ ^(all|wheel|sdist)$ ]]; then
                    echo -e "${RED}Invalid package format: $build_format${RESET}"
                    echo "Allowed formats: all, wheel, sdist"
                    exit 1
                fi
                
                # Check additional build options
                do_clean="true"  # Clean by default
                do_install="false"
                
                # Check options in remaining arguments
                while [ $# -gt 0 ]; do
                    case "$1" in
                        --no-clean)
                            do_clean="false"
                            shift
                            ;;
                        --install|-i)
                            do_install="true"
                            shift
                            ;;
                        *)
                            # End processing build options
                            break
                            ;;
                    esac
                done
                
                build_package "$build_format" "$do_clean" "$do_install"
                exit $?
                ;;
            -u|--uninstall)
                uninstall_dev_env
                exit $?
                ;;
            -v|--version)
                get_version
                exit $?
                ;;
            -f|--force)
                FORCE_MODE="true"
                shift
                ;;
            -d|--docs)
                action="$2"
                case $action in
                    dev)
                        mkdocs serve
                        ;;
                    build)
                        mkdocs build
                        ;;
                    deploy)
                        deploy_docs
                        ;;
                    *)
                        docs_management
                        ;;
                esac
                exit $?
                ;;
            *)
                echo -e "${RED}Unknown parameter: $1${RESET}"
                show_help
                exit 1
                ;;
        esac
    done
}

# Main program loop in interactive mode
interactive_mode() {
    show_banner
    
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            0)
                echo -e "${GREEN}Goodbye!${RESET}"
                exit 0
                ;;
            1)
                install_dev_env
                ;;
            2)
                run_app
                ;;
            3)
                run_tests
                ;;
            4)
                build_package
                ;;
            5)
                uninstall_dev_env
                ;;
            6)
                get_version
                ;;
            7)
                docs_management
                ;;
            8)
                version_management
                ;;
            *)
                echo -e "${RED}Invalid choice. Try again.${RESET}"
                ;;
        esac
        
        echo
        read -rp "Press Enter to continue..."
        clear
        show_banner
    done
}

# Initialize variables
FORCE_MODE="false"
NON_INTERACTIVE="false"

# Run program
process_args "$@" 