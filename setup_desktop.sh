#!/bin/bash

# ==============================================================================
# WebGCS Linux Desktop Setup Script
# ==============================================================================
#
# Automated setup script for WebGCS on Linux systems.
# Creates Python virtual environment, installs dependencies, and downloads
# required frontend libraries.
#
# Requirements: Linux OS, Python 3.7+, curl, git
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

# Script configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly VENV_PATH="${SCRIPT_DIR}/venv"
readonly STATIC_LIB_DIR="${SCRIPT_DIR}/static/lib"
readonly MIN_PYTHON_VERSION="3.7"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check if running on Linux
check_linux() {
    if [[ "$(uname)" != "Linux" ]]; then
        log_error "This script is designed for Linux systems only."
        log_error "For other operating systems, please use manual installation:"
        log_error "  python3 -m venv venv"
        log_error "  source venv/bin/activate"
        log_error "  pip install -r requirements.txt"
        exit 1
    fi
}

# Check Python version
check_python_version() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.7+ and try again."
        log_error "On Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
        log_error "On CentOS/RHEL: sudo yum install python3 python3-pip"
        log_error "On Arch: sudo pacman -S python python-pip"
        exit 1
    fi

    local python_version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
        log_error "Python ${python_version} detected. WebGCS requires Python ${MIN_PYTHON_VERSION}+."
        log_error "Please upgrade Python and try again."
        exit 1
    fi
    
    log_success "Python ${python_version} detected"
}

# Check required system dependencies
check_dependencies() {
    local missing_deps=()
    
    # Check for curl
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    # Check for git
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi
    
    # Check for python3-venv (on some systems it's separate)
    if ! python3 -m venv --help &> /dev/null; then
        missing_deps+=("python3-venv")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_error "Please install them first:"
        log_error "  Ubuntu/Debian: sudo apt install ${missing_deps[*]}"
        log_error "  CentOS/RHEL: sudo yum install ${missing_deps[*]}"
        log_error "  Arch: sudo pacman -S ${missing_deps[*]}"
        exit 1
    fi
    
    log_success "All system dependencies found"
}

# Create directory structure
create_directories() {
    log_info "Creating directory structure..."
    
    mkdir -p "${SCRIPT_DIR}/templates"
    mkdir -p "${SCRIPT_DIR}/static/css"
    mkdir -p "${STATIC_LIB_DIR}"
    mkdir -p "${SCRIPT_DIR}/logs"
    
    log_success "Directories created"
}

# Setup Python virtual environment
setup_virtual_environment() {
    if [[ -d "${VENV_PATH}" ]]; then
        log_warning "Virtual environment already exists at ${VENV_PATH}"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Removing existing virtual environment..."
            rm -rf "${VENV_PATH}"
        else
            log_info "Using existing virtual environment"
            return 0
        fi
    fi
    
    log_info "Creating Python virtual environment..."
    python3 -m venv "${VENV_PATH}"
    
    # Activate and upgrade pip
    source "${VENV_PATH}/bin/activate"
    pip install --upgrade pip
    
    log_success "Virtual environment created at ${VENV_PATH}"
}

# Install Python dependencies
install_python_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Check if requirements.txt exists
    if [[ -f "${SCRIPT_DIR}/requirements.txt" ]]; then
        log_info "Installing from requirements.txt..."
        "${VENV_PATH}/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt"
    else
        log_warning "requirements.txt not found, installing core dependencies..."
        "${VENV_PATH}/bin/pip" install \
            Flask==3.0.2 \
            Flask-SocketIO==5.3.6 \
            gevent==23.9.1 \
            gevent-websocket==0.10.1 \
            pymavlink==2.4.39 \
            python-dotenv==1.0.1 \
            python-engineio==4.9.0 \
            python-socketio==5.11.1
    fi
    
    log_success "Python dependencies installed"
}

# Download frontend libraries
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
            if curl -fsSL "$url" -o "$filepath"; then
                log_success "Downloaded ${filename}"
            else
                log_error "Failed to download ${filename}"
                exit 1
            fi
        fi
    done
}

# Set proper permissions
set_permissions() {
    log_info "Setting file permissions..."
    
    # Make Python scripts executable
    find "${SCRIPT_DIR}" -name "*.py" -type f -exec chmod +x {} \;
    
    # Make sure the virtual environment is accessible
    chmod -R u+rwX "${VENV_PATH}"
    
    log_success "Permissions set"
}

# Create .env file template
create_env_template() {
    local env_file="${SCRIPT_DIR}/.env.example"
    
    if [[ ! -f "$env_file" ]]; then
        log_info "Creating .env.example file..."
        cat > "$env_file" << 'EOF'
# WebGCS Configuration Example
# Copy this file to .env and modify as needed

# Drone Connection Settings
DRONE_TCP_ADDRESS=192.168.1.247
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
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Check if virtual environment works
    if ! "${VENV_PATH}/bin/python" -c "import flask, flask_socketio, pymavlink" 2>/dev/null; then
        log_error "Installation verification failed. Some Python packages may not be installed correctly."
        exit 1
    fi
    
    # Check if main app exists
    if [[ ! -f "${SCRIPT_DIR}/app.py" ]]; then
        log_warning "app.py not found. Make sure you have all the project files."
    fi
    
    log_success "Installation verified successfully"
}

# Print final instructions
print_instructions() {
    echo
    echo "======================================================================"
    log_success "WebGCS Setup Complete!"
    echo "======================================================================"
    echo
    echo "Next steps:"
    echo
    echo "1. Activate the virtual environment:"
    echo "   ${GREEN}source venv/bin/activate${NC}"
    echo
    echo "2. (Optional) Configure your settings:"
    echo "   ${BLUE}cp .env.example .env${NC}"
    echo "   ${BLUE}nano .env${NC}  # Edit with your drone's IP and settings"
    echo
    echo "3. Ensure your drone/autopilot is configured as a MAVLink TCP server"
    echo "   listening on port 5678 (or your configured port)"
    echo
    echo "4. Run the application:"
    echo "   ${GREEN}python app.py${NC}"
    echo
    echo "5. Open your browser to:"
    echo "   ${BLUE}http://localhost:5000${NC}"
    echo
    echo "6. To stop the application, press ${YELLOW}Ctrl+C${NC}"
    echo
    echo "For troubleshooting, check the logs in the 'logs/' directory"
    echo "======================================================================"
}

# Main execution
main() {
    echo "======================================================================"
    echo "           WebGCS Linux Desktop Setup Script v1.4"
    echo "======================================================================"
    echo
    
    log_info "Starting WebGCS setup in: ${SCRIPT_DIR}"
    
    check_linux
    check_python_version
    check_dependencies
    create_directories
    setup_virtual_environment
    install_python_dependencies
    download_frontend_libraries
    set_permissions
    create_env_template
    verify_installation
    print_instructions
    
    echo
    log_success "Setup completed successfully!"
}

# Run main function
main "$@"
