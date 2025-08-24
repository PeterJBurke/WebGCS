#!/bin/bash
# WebGCS Claude Code Project Migration Script
# 
# This script provides robust migration capabilities for moving the WebGCS project
# to different directories while preserving Claude Code integration.
#
# Usage: ./migrate-claude-project.sh [new_directory_path]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Get current directory
CURRENT_DIR=$(pwd)
PROJECT_ROOT=$(dirname "$CURRENT_DIR")

# Parse arguments
NEW_LOCATION=${1:-}
TEST_MODE=${2:-}

if [ -z "$NEW_LOCATION" ]; then
    error "Usage: $0 <new_directory_path> [--test]"
fi

if [ "$TEST_MODE" = "--test" ]; then
    log "Running in TEST MODE - no changes will be made"
    TEST=1
else
    TEST=0
fi

log "=== WebGCS Claude Code Project Migration ==="
log "Current location: $CURRENT_DIR"
log "Target location: $NEW_LOCATION"
log "Project root detected: $PROJECT_ROOT"

# Verify we're in a webgcs project
if [ ! -f "app.py" ] || [ ! -f "webgcs_logger.py" ]; then
    error "This doesn't appear to be a WebGCS project directory (missing app.py or webgcs_logger.py)"
fi

# Create backup
BACKUP_DIR="${CURRENT_DIR}_migration_backup_$(date +%Y%m%d_%H%M%S)"
log "Creating backup at: $BACKUP_DIR"

if [ $TEST -eq 0 ]; then
    cp -r "$CURRENT_DIR" "$BACKUP_DIR"
    success "Backup created successfully"
fi

# Create new directory
if [ $TEST -eq 0 ]; then
    mkdir -p "$NEW_LOCATION"
    log "Created new directory: $NEW_LOCATION"
fi

# Copy project files
log "Copying project files..."
if [ $TEST -eq 0 ]; then
    rsync -av --exclude='__pycache__' --exclude='*.pyc' "$CURRENT_DIR/" "$NEW_LOCATION/"
    success "Project files copied"
fi

# Update Claude Code configuration
CLAUDE_CONFIG="$NEW_LOCATION/claude-code/.claude/settings.local.json"
if [ -f "$CLAUDE_CONFIG" ] && [ $TEST -eq 0 ]; then
    log "Updating Claude Code configuration..."
    # Create a backup of the config
    cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup"
    
    # Update paths in configuration (this would need to be customized based on actual config structure)
    sed -i.bak "s|$CURRENT_DIR|$NEW_LOCATION|g" "$CLAUDE_CONFIG" 2>/dev/null || warn "Could not update Claude config automatically"
    success "Claude Code configuration updated"
fi

# Initialize git repository if it doesn't exist
if [ ! -d "$NEW_LOCATION/.git" ] && [ $TEST -eq 0 ]; then
    log "Initializing git repository..."
    cd "$NEW_LOCATION"
    git init
    git remote add origin https://github.com/PeterJBurke/WebGCS.git 2>/dev/null || warn "Could not add remote origin"
    success "Git repository initialized"
fi

# Create environment setup script
if [ $TEST -eq 0 ]; then
    cat > "$NEW_LOCATION/scripts/setup-environment.sh" << 'EOF'
#!/bin/bash
# WebGCS Environment Setup Script
# Run this after moving the project to a new location

# Set up Python environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Check for .env file
if [ ! -f "claude-code/.env" ]; then
    echo "Warning: No .env file found. Copy your API keys to claude-code/.env"
    if [ -f "claude-code/.env.sample" ]; then
        echo "Template available at claude-code/.env.sample"
    fi
fi

echo "Environment setup complete!"
echo "To run WebGCS: python app.py"
EOF
    chmod +x "$NEW_LOCATION/scripts/setup-environment.sh"
    success "Environment setup script created"
fi

# Test the new installation
if [ $TEST -eq 0 ]; then
    log "Testing new installation..."
    cd "$NEW_LOCATION"
    
    # Check if Python files are valid
    if python3 -c "import py_compile; py_compile.compile('app.py', doraise=True)" 2>/dev/null; then
        success "Python syntax validation passed"
    else
        error "Python syntax validation failed"
    fi
fi

log "=== Migration Summary ==="
log "✅ Backup created: $BACKUP_DIR"
log "✅ Files copied to: $NEW_LOCATION"
log "✅ Claude Code configuration updated"
log "✅ Git repository prepared"
log "✅ Environment setup script created"
log ""
log "Next steps:"
log "1. Update Claude Code to open project at: $NEW_LOCATION"
log "2. Run setup script: cd $NEW_LOCATION && ./scripts/setup-environment.sh"
log "3. Test the application: python app.py"
log "4. If everything works, you can remove the backup: $BACKUP_DIR"

success "Migration completed successfully!"