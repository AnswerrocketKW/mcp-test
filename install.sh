#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "\n${BLUE}🔄 $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check requirements
check_requirements() {
    print_step "Checking system requirements..."
    
    if ! command_exists curl; then
        print_error "curl is required but not installed. Please install curl and try again."
        exit 1
    fi
    
    if ! command_exists git; then
        print_error "git is required but not installed. Please install git and try again."
        exit 1
    fi
    
    # Check for Python
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python is required but not installed. Please install Python 3.8+ and try again."
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    if ! $PYTHON_CMD -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        print_error "Python 3.8 or higher is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "All requirements satisfied (Python $PYTHON_VERSION)"
}

# Get user input
get_user_input() {
    print_step "Setting up AnswerRocket MCP Server..."
    echo
    
    # Get AnswerRocket URL
    while true; do
        echo -n "Please enter your AnswerRocket URL (e.g., https://your-instance.answerrocket.com): "
        read -r AR_URL </dev/tty
        
        if [[ -z "$AR_URL" ]]; then
            print_warning "URL cannot be empty. Please try again."
            continue
        fi
        
        # Remove trailing slash if present
        AR_URL=$(echo "$AR_URL" | sed 's|/$||')
        
        # Basic URL validation
        if [[ ! "$AR_URL" =~ ^https?:// ]]; then
            print_warning "Please enter a valid URL starting with http:// or https://"
            continue
        fi
        
        break
    done
    
    print_success "AnswerRocket URL: $AR_URL"
    echo
    
    # Instructions for getting API key
    print_info "To get your API key:"
    echo "1. Open this URL in your browser: ${AR_URL}/apps/chat/topics?panel=user-info"
    echo "2. Click 'Generate' under 'Client API Key'"
    echo "3. Copy the generated API key"
    echo
    
    # Get API Token
    while true; do
        echo -n "Please paste your AnswerRocket API token: "
        read -r AR_TOKEN </dev/tty
        
        if [[ -z "$AR_TOKEN" ]]; then
            print_warning "API token cannot be empty. Please try again."
            continue
        fi
        
        break
    done
    
    print_success "API token received"
}

# Setup project
setup_project() {
    print_step "Setting up project directory..."
    
    # Create project directory
    PROJECT_DIR="$HOME/answerrocket-mcp-server"
    
    if [[ -d "$PROJECT_DIR" ]]; then
        print_warning "Directory $PROJECT_DIR already exists."
        echo -n "Do you want to remove it and reinstall? (y/N): "
        read -r CONFIRM </dev/tty
        if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
            print_info "Removed existing directory"
        else
            print_error "Installation cancelled"
            exit 1
        fi
    fi
    
    # Clone the repository
    print_info "Cloning repository..."
    git clone https://github.com/AnswerrocketKW/mcp-test.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    print_success "Repository cloned to $PROJECT_DIR"
}

# Setup Python environment
setup_python_env() {
    print_step "Setting up Python virtual environment..."
    
    # Create virtual environment
    $PYTHON_CMD -m venv .venv
    
    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        source .venv/Scripts/activate
    else
        # Unix/Linux/macOS
        source .venv/bin/activate
    fi
    
    print_success "Virtual environment created and activated"
    
    # Install dependencies
    print_info "Installing dependencies..."
    
    # Install mcp[cli] directly instead of editable installation
    pip install "mcp[cli]"
    print_success "Installed mcp[cli]"
    
    # Install answerrocket-client
    print_info "Installing answerrocket-client..."
    pip install answerrocket-client
    print_success "answerrocket-client installed"
}

# Install MCP server
install_mcp_server() {
    print_step "Installing MCP server..."
    
    # Check if mcp command is available
    if ! command_exists mcp; then
        print_error "mcp command not found. Please ensure mcp[cli] is properly installed."
        exit 1
    fi
    
    # Install the server with environment variables
    mcp install server.py -v "AR_URL=$AR_URL" -v "AR_TOKEN=$AR_TOKEN"
    
    print_success "MCP server installed successfully!"
}

# Main installation function
main() {
    echo "🚀 AnswerRocket MCP Server Installer"
    echo "===================================="
    
    check_requirements
    get_user_input
    setup_project
    setup_python_env
    install_mcp_server
    
    echo
    print_success "Installation completed successfully! 🎉"
    echo
    print_info "Your MCP server is now installed and ready to use."
    print_info "You can start using it with MCP-compatible clients like Claude Desktop."
    echo
    print_info "Project location: $PROJECT_DIR"
    print_info "Configuration: AR_URL=$AR_URL"
    echo
    print_warning "Keep your API token secure and never share it publicly!"
}

# Run main function
main "$@" 