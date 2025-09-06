#!/bin/bash

# ==============================================================================
# WebGCS Linux Desktop Setup Script for Ubuntu 24.04 LTS
# ==============================================================================
#
# Automated setup script for WebGCS on Linux systems.
# Creates Python virtual environment, installs dependencies, and downloads
# required frontend libraries.
#
# Requirements: Ubuntu 24.04 LTS, Python 3.10+, curl, git
#
# Usage:
#   chmod +x setup_desktop.sh
#   ./setup_desktop.sh
#
# ==============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Script configuration - Use absolute paths to prevent issues
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly VENV_PATH="${SCRIPT_DIR}/venv"
readonly STATIC_LIB_DIR="${SCRIPT_DIR}/static/lib"
readonly MIN_PYTHON_VERSION="3.10"

# Validation: Ensure we're in the correct directory
if [[ ! -f "${SCRIPT_DIR}/app.py" ]]; then
    echo -e "${RED}[ERROR]${NC} This script must be run from the WebGCS directory containing app.py"
    echo -e "${RED}[ERROR]${NC} Current directory: $(pwd)"
    echo -e "${RED}[ERROR]${NC} Script directory: ${SCRIPT_DIR}"
    echo -e "${RED}[ERROR]${NC} Please cd to the WebGCS directory and run the script again"
    exit 1
fi

# Record start time
START_TIME=$(date +%s)
START_TIME_HUMAN=$(date)

# Enhanced logging functions with better formatting
log_info() {
    printf "${BLUE}[INFO]${NC} %s\n" "$1"
}

log_success() {
    printf "${GREEN}[SUCCESS]${NC} %s\n" "$1"
}

log_warning() {
    printf "${YELLOW}[WARNING]${NC} %s\n" "$1"
}

log_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$1" >&2
}

# Enhanced error handler
handle_error() {
    local line_no=$1
    local error_code=$2
    log_error "Script failed at line $line_no with exit code $error_code"
    log_error "Please check the output above for details"
    exit $error_code
}

# Set up error handling
trap 'handle_error ${LINENO} $?' ERR

# Validate script environment
validate_environment() {
    log_info "Validating script environment..."
    
    # Check we have required commands
    local required_commands=("cd" "pwd" "dirname" "realpath")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "Required command '$cmd' not found"
            exit 1
        fi
    done
    
    # Validate paths are absolute and canonical
    if [[ ! "${SCRIPT_DIR}" =~ ^/ ]]; then
        log_error "SCRIPT_DIR is not an absolute path: ${SCRIPT_DIR}"
        exit 1
    fi
    
    log_success "Environment validation passed"
}

# Check if running on Linux
check_linux() {
    log_info "Checking operating system..."
    if [[ "$(uname)" != "Linux" ]]; then
        log_error "This script is designed for Linux systems only."
        log_error "For other operating systems, please use manual installation:"
        log_error "  python3 -m venv venv"
        log_error "  source venv/bin/activate"
        log_error "  pip install -r requirements.txt"
        exit 1
    fi
    log_success "Running on Linux"
}

# Check Ubuntu version compatibility
check_ubuntu_version() {
    log_info "Checking Ubuntu version compatibility..."
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        log_info "Detected OS: $NAME $VERSION_ID"
        
        # Check if it's Ubuntu
        if [[ "$ID" == "ubuntu" ]]; then
            # Check version compatibility (20.04, 22.04, 24.04)
            case "$VERSION_ID" in
                "20.04"|"22.04"|"24.04")
                    log_success "Ubuntu $VERSION_ID is supported"
                    ;;
                *)
                    log_warning "Ubuntu $VERSION_ID may work but is not specifically tested"
                    ;;
            esac
        else
            log_warning "$NAME may work but Ubuntu is recommended"
        fi
    else
        log_warning "Could not detect OS version"
    fi
}

# Update package lists (essential for fresh Ubuntu 24.04)
update_package_lists() {
    log_info "Updating package lists..."
    
    # Skip if running in non-interactive mode and not root
    if [[ ! -t 0 ]] && [[ $EUID -ne 0 ]]; then
        log_warning "Skipping package list update in non-interactive mode"
        return 0
    fi
    
    if command -v apt &> /dev/null; then
        if [[ $EUID -eq 0 ]]; then
            apt update
        else
            sudo apt update
        fi
        log_success "Package lists updated"
    elif command -v dnf &> /dev/null; then
        if [[ $EUID -eq 0 ]]; then
            dnf check-update || true
        else
            sudo dnf check-update || true
        fi
        log_success "Package lists updated"
    elif command -v yum &> /dev/null; then
        if [[ $EUID -eq 0 ]]; then
            yum check-update || true
        else
            sudo yum check-update || true
        fi
        log_success "Package lists updated"
    else
        log_warning "Could not detect package manager to update package lists"
    fi
}

# Enhanced dependency installation with better error handling
install_system_dependencies() {
    log_info "Installing required system dependencies..."
    
    local packages_to_install=()
    local install_cmd=""
    
    # Detect package manager and set packages
    if command -v apt &> /dev/null; then
        # For Ubuntu/Debian
        packages_to_install+=(
            "python3"
            "python3-venv" 
            "python3-pip"
            "python3-dev"
            "build-essential"
            "pkg-config"
            "libevent-dev"
            "curl"
            "git"
        )
        install_cmd="apt install -y"
        
    elif command -v dnf &> /dev/null; then
        # For CentOS/RHEL/Fedora
        packages_to_install+=(
            "python3"
            "python3-venv"
            "python3-pip"
            "python3-devel"
            "gcc"
            "pkgconfig"
            "libevent-devel"
            "curl"
            "git"
        )
        install_cmd="dnf install -y"
        
    elif command -v yum &> /dev/null; then
        # For older CentOS/RHEL
        packages_to_install+=(
            "python3"
            "python3-pip"
            "python3-devel"
            "gcc"
            "pkgconfig"
            "libevent-devel"
            "curl"
            "git"
        )
        install_cmd="yum install -y"
        
    else
        log_error "Could not detect package manager. Please install the following manually:"
        log_error "  - Python 3.10+"
        log_error "  - python3-venv"
        log_error "  - python3-dev"
        log_error "  - build-essential/gcc"
        log_error "  - pkg-config"
        log_error "  - libevent-dev"
        log_error "  - curl"
        log_error "  - git"
        exit 1
    fi
    
    log_info "Installing packages: ${packages_to_install[*]}"
    
    # Execute installation command with proper privileges
    if [[ $EUID -eq 0 ]]; then
        $install_cmd "${packages_to_install[@]}"
    else
        sudo $install_cmd "${packages_to_install[@]}"
    fi
    
    log_success "System dependencies installed"
}

# Enhanced Python version check
check_python_version() {
    log_info "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Installing it now..."
        install_system_dependencies
    fi

    local python_version
    if ! python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null); then
        log_error "Failed to get Python version"
        exit 1
    fi
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
        log_error "Python ${python_version} detected. WebGCS requires Python ${MIN_PYTHON_VERSION}+."
        log_error "Please upgrade Python and try again."
        log_error "On Ubuntu 20.04, install python3.10: sudo apt install python3.10 python3.10-venv"
        exit 1
    fi
    
    log_success "Python ${python_version} detected"
}

# Enhanced dependency checker
check_dependencies() {
    log_info "Checking system dependencies..."
    
    local missing_deps=()
    local ubuntu_deps=()
    
    # Check for curl
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
        ubuntu_deps+=("curl")
    fi
    
    # Check for git
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
        ubuntu_deps+=("git")
    fi
    
    # Check for python3-venv (on some systems it's separate)
    if ! python3 -m venv --help &> /dev/null; then
        missing_deps+=("python3-venv")
        ubuntu_deps+=("python3-venv")
    fi
    
    # Check for python3-dev (needed for some pip packages like gevent)
    if command -v dpkg &> /dev/null && ! dpkg -l python3-dev &> /dev/null; then
        missing_deps+=("python3-dev")
        ubuntu_deps+=("python3-dev")
    fi
    
    # Check for build essentials
    if ! command -v gcc &> /dev/null; then
        missing_deps+=("build-essential")
        ubuntu_deps+=("build-essential")
    fi
    
    # Check for pkg-config
    if ! command -v pkg-config &> /dev/null; then
        missing_deps+=("pkg-config")
        ubuntu_deps+=("pkg-config")
    fi
    
    # Check for development headers
    if command -v dpkg &> /dev/null && ! dpkg -l libevent-dev &> /dev/null; then
        missing_deps+=("libevent-dev")
        ubuntu_deps+=("libevent-dev")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_warning "Missing dependencies detected: ${missing_deps[*]}"
        log_info "Installing missing dependencies automatically..."
        install_system_dependencies
        log_success "Missing dependencies installed"
    else
        log_success "All system dependencies found"
    fi
}

# Create directory structure with proper error handling
create_directories() {
    log_info "Creating directory structure..."
    
    local directories=(
        "${SCRIPT_DIR}/templates"
        "${SCRIPT_DIR}/static/css"
        "${STATIC_LIB_DIR}"
        "${SCRIPT_DIR}/logs"
    )
    
    for dir in "${directories[@]}"; do
        if ! mkdir -p "$dir"; then
            log_error "Failed to create directory: $dir"
            exit 1
        fi
    done
    
    log_success "Directories created"
}

# Enhanced virtual environment setup
setup_virtual_environment() {
    log_info "Setting up Python virtual environment..."
    
    if [[ -d "${VENV_PATH}" ]]; then
        log_warning "Virtual environment already exists at ${VENV_PATH}"
        if [[ -t 0 ]]; then  # Only prompt if interactive
            read -p "Do you want to recreate it? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log_info "Removing existing virtual environment..."
                rm -rf "${VENV_PATH}"
            else
                log_info "Using existing virtual environment"
                return 0
            fi
        else
            log_info "Non-interactive mode: using existing virtual environment"
            return 0
        fi
    fi
    
    log_info "Creating Python virtual environment..."
    if ! python3 -m venv "${VENV_PATH}"; then
        log_error "Failed to create virtual environment"
        exit 1
    fi
    
    # Activate and upgrade pip
    if ! source "${VENV_PATH}/bin/activate"; then
        log_error "Failed to activate virtual environment"
        exit 1
    fi
    
    # Upgrade pip, wheel, and setuptools
    if ! pip install --upgrade pip wheel setuptools; then
        log_error "Failed to upgrade pip, wheel, and setuptools"
        exit 1
    fi
    
    log_success "Virtual environment created at ${VENV_PATH}"
}

# Enhanced Python dependency installation
install_python_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Verify virtual environment
    if [[ ! -f "${VENV_PATH}/bin/python" ]]; then
        log_error "Virtual environment Python not found at ${VENV_PATH}/bin/python"
        exit 1
    fi
    
    # Check if requirements.txt exists
    if [[ -f "${SCRIPT_DIR}/requirements.txt" ]]; then
        log_info "Installing from requirements.txt..."
        
        # Try installation with enhanced error handling
        if ! "${VENV_PATH}/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt"; then
            log_warning "Initial installation failed, trying alternative approach..."
            
            # Install problematic packages individually with specific versions
            local packages=(
                "gevent==23.9.1"
                "gevent-websocket==0.10.1"
                "Flask==3.0.2"
                "Flask-SocketIO==5.3.6"
                "pymavlink==2.4.39"
                "python-dotenv==1.0.1"
                "python-engineio==4.9.0"
                "python-socketio==5.11.1"
            )
            
            for package in "${packages[@]}"; do
                log_info "Installing $package..."
                if ! "${VENV_PATH}/bin/pip" install "$package"; then
                    log_error "Failed to install $package"
                    exit 1
                fi
            done
        fi
    else
        log_warning "requirements.txt not found, installing core dependencies..."
        local core_packages=(
            "Flask==3.0.2"
            "Flask-SocketIO==5.3.6"
            "gevent==23.9.1"
            "gevent-websocket==0.10.1"
            "pymavlink==2.4.39"
            "python-dotenv==1.0.1"
            "python-engineio==4.9.0"
            "python-socketio==5.11.1"
        )
        
        for package in "${core_packages[@]}"; do
            log_info "Installing $package..."
            if ! "${VENV_PATH}/bin/pip" install "$package"; then
                log_error "Failed to install $package"
                exit 1
            fi
        done
    fi
    
    log_success "Python dependencies installed"
}

# Enhanced frontend library download
download_frontend_libraries() {
    log_info "Downloading frontend JavaScript libraries..."
    
    # Create array of libraries to download
    declare -A libraries=(
        ["leaflet.css"]="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        ["leaflet.js"]="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
        ["socket.io.min.js"]="https://cdn.socket.io/4.7.4/socket.io.min.js"
        ["bootstrap.min.css"]="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
        ["bootstrap.bundle.min.js"]="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"
    )
    
    for filename in "${!libraries[@]}"; do
        local url="${libraries[$filename]}"
        local filepath="${STATIC_LIB_DIR}/${filename}"
        
        if [[ -f "$filepath" ]]; then
            log_info "Skipping ${filename} (already exists)"
        else
            log_info "Downloading ${filename}..."
            if ! curl -fsSL --retry 3 --retry-delay 2 "$url" -o "$filepath"; then
                log_error "Failed to download ${filename} from ${url}"
                exit 1
            fi
            log_success "Downloaded ${filename}"
        fi
    done
}

# Set proper permissions
set_permissions() {
    log_info "Setting file permissions..."
    
    # Make Python scripts executable
    find "${SCRIPT_DIR}" -name "*.py" -type f -exec chmod +x {} \; || {
        log_warning "Some Python files could not be made executable"
    }
    
    # Make sure the virtual environment is accessible
    chmod -R u+rwX "${VENV_PATH}" || {
        log_warning "Could not set permissions on virtual environment"
    }
    
    log_success "Permissions set"
}

# Create .env file template
create_env_template() {
    local env_example="${SCRIPT_DIR}/.env.example"
    local env_file="${SCRIPT_DIR}/.env"
    
    if [[ ! -f "$env_example" ]]; then
        log_info "Creating .env.example file..."
        cat > "$env_example" << 'EOF'
# WebGCS Configuration Example
# Copy this file to .env and modify as needed

# Drone Connection Settings
DRONE_TCP_ADDRESS=127.0.0.1
DRONE_TCP_PORT=5678

# Web Server Settings
WEB_SERVER_HOST=0.0.0.0
WEB_SERVER_PORT=5000
SECRET_KEY=change_this_to_a_secure_secret_key

# MAVLink Settings
HEARTBEAT_TIMEOUT=15
REQUEST_STREAM_RATE_HZ=4
COMMAND_ACK_TIMEOUT=5
TELEMETRY_UPDATE_INTERVAL=0.1
EOF
        log_success "Created .env.example configuration template"
        
        # If no .env exists, create one from example
        if [[ ! -f "$env_file" ]]; then
            cp "$env_example" "$env_file"
            log_info "Created default .env file from template"
        fi
    fi
}

# Enhanced systemd service creation with robust path handling
create_systemd_service() {
    log_info "Creating systemd service for WebGCS..."
    
    local service_name="webgcs"
    local service_file="/etc/systemd/system/${service_name}.service"
    local current_user="$(whoami)"
    
    # Use absolute, canonical paths to prevent any issues
    local script_dir_abs="$(realpath "${SCRIPT_DIR}")"
    local venv_path_abs="$(realpath "${VENV_PATH}")"
    local python_path="${venv_path_abs}/bin/python"
    local app_path="${script_dir_abs}/app.py"
    
    # Debug: Show the paths being used
    log_info "Service configuration paths:"
    log_info "  Script directory: ${script_dir_abs}"
    log_info "  Virtual environment: ${venv_path_abs}"
    log_info "  Python executable: ${python_path}"
    log_info "  App path: ${app_path}"
    log_info "  Current user: ${current_user}"
    
    # Comprehensive path validation
    if [[ ! -f "$python_path" ]]; then
        log_error "Python executable not found at: $python_path"
        log_error "Virtual environment may not be properly created"
        return 1
    fi
    
    if [[ ! -f "$app_path" ]]; then
        log_error "app.py not found at: $app_path"
        log_error "Make sure you're running this script from the WebGCS directory"
        return 1
    fi
    
    # Verify Python executable works
    if ! "$python_path" --version &> /dev/null; then
        log_error "Python executable at $python_path is not working"
        return 1
    fi
    
    # Verify Python can import required modules
    if ! "$python_path" -c "import flask, flask_socketio, pymavlink" &> /dev/null; then
        log_error "Python dependencies not properly installed in virtual environment"
        return 1
    fi
    
    log_info "Path validation successful"
    
    # Create the service file content with validated paths
    local service_content="[Unit]
Description=WebGCS - Web-Based Ground Control Station
Documentation=https://github.com/PeterJBurke/WebGCS
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=${current_user}
Group=${current_user}
WorkingDirectory=${script_dir_abs}
Environment=PATH=${venv_path_abs}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=${script_dir_abs}
ExecStart=${python_path} ${app_path}
Restart=on-failure
RestartSec=10
TimeoutStartSec=30
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=webgcs

# Security settings for Ubuntu 24.04
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=${script_dir_abs}
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
RemoveIPC=yes
PrivateDevices=yes

[Install]
WantedBy=multi-user.target"

    # Install service with proper privilege handling
    local use_sudo=false
    if [[ ! -w "/etc/systemd/system" ]]; then
        use_sudo=true
        log_info "Installing systemd service (requires sudo)..."
        if ! command -v sudo &> /dev/null; then
            log_error "sudo is required to install the systemd service but is not available."
            log_error "Please install sudo or run this script as root."
            return 1
        fi
    else
        log_info "Installing systemd service (running with root privileges)..."
    fi
    
    # Create service file
    if [[ "$use_sudo" == true ]]; then
        echo "$service_content" | sudo tee "$service_file" > /dev/null
        sudo chmod 644 "$service_file"
    else
        echo "$service_content" > "$service_file"
        chmod 644 "$service_file"
    fi
    
    # Reload systemd and enable the service
    if [[ "$use_sudo" == true ]]; then
        sudo systemctl daemon-reload
        sudo systemctl enable "$service_name"
    else
        systemctl daemon-reload
        systemctl enable "$service_name"
    fi
    
    log_success "Systemd service created and enabled"
    
    # Start the service with enhanced error checking
    log_info "Starting WebGCS service..."
    local start_success=false
    
    if [[ "$use_sudo" == true ]]; then
        if sudo systemctl start "$service_name"; then
            start_success=true
        fi
    else
        if systemctl start "$service_name"; then
            start_success=true
        fi
    fi
    
    if [[ "$start_success" == true ]]; then
        log_success "WebGCS service started successfully"
        
        # Wait and check status
        sleep 3
        local is_active=false
        if [[ "$use_sudo" == true ]]; then
            sudo systemctl is-active --quiet "$service_name" && is_active=true
        else
            systemctl is-active --quiet "$service_name" && is_active=true
        fi
        
        if [[ "$is_active" == true ]]; then
            log_success "Service is running properly"
        else
            log_warning "Service may have issues. Check with: ${use_sudo:+sudo }systemctl status $service_name"
        fi
    else
        log_error "Failed to start WebGCS service"
        log_error "Check the service status with: ${use_sudo:+sudo }systemctl status $service_name"
        return 1
    fi
}

# Enhanced verification with better error reporting
verify_installation() {
    log_info "Verifying installation..."
    
    local verification_errors=()
    
    # Check virtual environment Python
    local venv_python="${VENV_PATH}/bin/python"
    if [[ ! -f "$venv_python" ]]; then
        verification_errors+=("Virtual environment Python not found at: $venv_python")
    fi
    
    # Check core Python packages
    local required_packages=("flask" "flask_socketio" "pymavlink" "gevent")
    for package in "${required_packages[@]}"; do
        if ! "$venv_python" -c "import $package" 2>/dev/null; then
            verification_errors+=("Python package '$package' not found or not working")
        fi
    done
    
    # Check gevent-websocket specifically (common issue)
    if ! "$venv_python" -c "import geventwebsocket" 2>/dev/null; then
        verification_errors+=("Python package 'gevent-websocket' not found or not working")
    fi
    
    # Check main app file
    if [[ ! -f "${SCRIPT_DIR}/app.py" ]]; then
        verification_errors+=("app.py not found in script directory")
    fi
    
    # Report verification results
    if [[ ${#verification_errors[@]} -gt 0 ]]; then
        log_error "Installation verification failed with the following issues:"
        for error in "${verification_errors[@]}"; do
            log_error "  - $error"
        done
        
        log_error "Try to fix these issues manually:"
        log_error "  source venv/bin/activate"
        log_error "  pip install --upgrade flask flask-socketio pymavlink gevent gevent-websocket"
        exit 1
    fi
    
    # Run detailed verification script if available
    if [[ -f "${SCRIPT_DIR}/verify_setup.py" ]]; then
        log_info "Running detailed verification..."
        if "$venv_python" "${SCRIPT_DIR}/verify_setup.py"; then
            log_success "Detailed verification completed successfully"
        else
            log_warning "Detailed verification found some issues. Check output above."
        fi
    fi
    
    log_success "Installation verified successfully"
}

# Enhanced service instructions with better formatting
print_service_instructions() {
    local service_name="webgcs"
    
    echo
    echo "======================================================================"
    log_success "WebGCS Service Installation Complete!"
    echo "======================================================================"
    echo
    echo "🚀 Your WebGCS service is now running automatically!"
    echo
    echo "📋 Service Management Commands:"
    echo
    echo "   Check service status:"
    printf "   %bsudo systemctl status %s%b\n" "${GREEN}" "$service_name" "${NC}"
    echo
    echo "   View service logs:"
    printf "   %bsudo journalctl -u %s -f%b\n" "${BLUE}" "$service_name" "${NC}"
    echo
    echo "   Restart the service:"
    printf "   %bsudo systemctl restart %s%b\n" "${YELLOW}" "$service_name" "${NC}"
    echo
    echo "   Stop the service:"
    printf "   %bsudo systemctl stop %s%b\n" "${RED}" "$service_name" "${NC}"
    echo
    echo "   Start the service:"
    printf "   %bsudo systemctl start %s%b\n" "${GREEN}" "$service_name" "${NC}"
    echo
    echo "   Disable auto-start on boot:"
    printf "   %bsudo systemctl disable %s%b\n" "${YELLOW}" "$service_name" "${NC}"
    echo
    echo "   Enable auto-start on boot:"
    printf "   %bsudo systemctl enable %s%b\n" "${GREEN}" "$service_name" "${NC}"
    echo
    echo "🌐 Access the interface:"
    printf "   %bhttp://localhost:5000%b\n" "${BLUE}" "${NC}"
    local ip_address=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "IP_ADDRESS")
    printf "   %bhttp://%s:5000%b\n" "${BLUE}" "${ip_address}" "${NC}"
    echo
    echo "⚙️  Configuration:"
    printf "   Edit: %b%s/.env%b\n" "${BLUE}" "${SCRIPT_DIR}" "${NC}"
    printf "   After changes: %bsudo systemctl restart %s%b\n" "${YELLOW}" "$service_name" "${NC}"
    echo
    printf "📁 Project directory: %s\n" "${SCRIPT_DIR}"
    printf "📋 Service file: /etc/systemd/system/%s.service\n" "$service_name"
    echo "======================================================================"
}

# Enhanced manual instructions
print_manual_instructions() {
    echo
    echo "======================================================================"
    log_success "WebGCS Setup Complete!"
    echo "======================================================================"
    echo
    echo "Next steps:"
    echo
    echo "1. Activate the virtual environment:"
    printf "   %bsource venv/bin/activate%b\n" "${GREEN}" "${NC}"
    echo
    echo "2. (Optional) Configure your settings:"
    printf "   %bnano .env%b  # Edit with your drone's IP and settings\n" "${BLUE}" "${NC}"
    echo
    echo "3. Ensure your drone/autopilot is configured as a MAVLink TCP server"
    echo "   listening on port 5678 (or your configured port)"
    echo
    echo "4. Run the application:"
    printf "   %bpython app.py%b\n" "${GREEN}" "${NC}"
    echo
    echo "5. Open your browser to:"
    printf "   %bhttp://localhost:5000%b\n" "${BLUE}" "${NC}"
    echo
    echo "6. To stop the application, press $(printf "%bCtrl+C%b" "${YELLOW}" "${NC}")"
    echo
    echo "For troubleshooting, check the logs in the 'logs/' directory"
    echo "======================================================================"
}

# Calculate and display timing information
print_timing_summary() {
    local end_time=$(date +%s)
    local end_time_human=$(date)
    local duration=$((end_time - START_TIME))
    local hours=$((duration / 3600))
    local minutes=$(( (duration % 3600) / 60 ))
    local seconds=$((duration % 60))

    echo -e "\nInstallation timing summary:"
    echo "Started : $START_TIME_HUMAN"
    echo "Finished: $end_time_human"
    echo "Duration: ${hours}h ${minutes}m ${seconds}s"
}

# Main execution with comprehensive error handling
main() {
    echo "======================================================================"
    echo "           WebGCS Linux Desktop Setup Script v2.4"
    echo "           Optimized for Ubuntu 24.04 LTS"
    echo "======================================================================"
    echo
    
    log_info "Starting WebGCS setup in: ${SCRIPT_DIR}"
    
    # Validate environment first
    validate_environment
    
    # Check for service installation option
    local install_service=false
    if [[ "${1:-}" == "--service" ]] || [[ "${1:-}" == "-s" ]]; then
        install_service=true
        log_info "Service installation mode enabled"
    elif [[ -t 0 ]]; then  # Only prompt if interactive
        echo
        log_info "Setup modes available:"
        echo "  Manual mode: Sets up for manual running"
        echo "  Service mode: Installs and runs as system service"
        echo
        read -p "Do you want to install WebGCS as a system service? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_service=true
        fi
    else
        log_info "Non-interactive mode: defaulting to manual installation"
    fi
    
    # Execute installation steps
    check_linux
    check_ubuntu_version
    update_package_lists
    check_python_version
    check_dependencies
    create_directories
    setup_virtual_environment
    install_python_dependencies
    download_frontend_libraries
    set_permissions
    create_env_template
    verify_installation
    
    # Install service or provide manual instructions
    if [[ "$install_service" == true ]]; then
        if create_systemd_service; then
            print_service_instructions
        else
            log_error "Service installation failed. Falling back to manual mode."
            print_manual_instructions
        fi
    else
        print_manual_instructions
    fi
    
    print_timing_summary
    echo
    log_success "Setup completed successfully!"
}

# Run main function with all arguments
main "$@"
