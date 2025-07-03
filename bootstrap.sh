#!/bin/bash

set -e

# Configuration
GITHUB_REPO="AnswerrocketKW/mcp-test"
GITHUB_BRANCH="main"
TEMP_DIR="/tmp/answerrocket-mcp-installer-$$"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cleanup function
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        log_info "Cleaning up temporary files..."
        rm -rf "$TEMP_DIR"
    fi
}

# Set up cleanup on exit
trap cleanup EXIT

# Main bootstrap function
main() {
    echo "AnswerRocket MCP Server Bootstrap Installer"
    echo "==========================================="
    echo
    
    # Check if git is available
    if ! command -v git &> /dev/null; then
        log_error "Git is required but not installed. Please install git first."
        exit 1
    fi
    
    # Create temporary directory
    log_info "Creating temporary directory: $TEMP_DIR"
    mkdir -p "$TEMP_DIR"
    
    # Clone the repository
    log_info "Cloning repository from GitHub..."
    git clone -b "$GITHUB_BRANCH" "https://github.com/$GITHUB_REPO.git" "$TEMP_DIR"
    
    # Change to the repository directory
    cd "$TEMP_DIR"
    
    # Make install script executable
    chmod +x install.sh
    
    # Run the installer with all passed arguments
    log_info "Running installer..."
    ./install.sh "$@"
    
    log_success "Bootstrap installation completed!"
}

# Run main function with all arguments
main "$@" 