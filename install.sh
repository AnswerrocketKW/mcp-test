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

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        OS="windows"
    else
        print_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
}

# Install uv package manager
install_uv() {
    print_step "Installing uv package manager..."
    
    detect_os
    
    if command_exists uv; then
        print_info "uv is already installed"
        UV_VERSION=$(uv --version 2>/dev/null || echo "unknown")
        print_success "uv version: $UV_VERSION"
        return
    fi
    
    case $OS in
        "macos"|"linux")
            print_info "Installing uv for $OS..."
            curl -LsSf https://astral.sh/uv/install.sh | sh
            # Add uv to PATH for current session
            export PATH="$HOME/.cargo/bin:$PATH"
            ;;
        "windows")
            print_info "Installing uv for Windows..."
            powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
            ;;
    esac
    
    # Verify installation
    if command_exists uv; then
        UV_VERSION=$(uv --version)
        print_success "uv installed successfully: $UV_VERSION"
    else
        print_error "Failed to install uv. Please install manually and try again."
        print_info "Visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
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
    
    print_success "System requirements satisfied"
}

# Setup Python with uv
setup_python() {
    print_step "Setting up Python 3.10.7 with uv..."
    
    # Install Python 3.10.7 if not available
    print_info "Installing Python 3.10.7..."
    uv python install 3.10.7
    
    # Verify Python installation
    PYTHON_VERSION=$(uv python list | grep "3.10.7" | head -1 | awk '{print $1}')
    if [[ -z "$PYTHON_VERSION" ]]; then
        print_error "Failed to install Python 3.10.7"
        exit 1
    fi
    
    print_success "Python 3.10.7 installed successfully"
    PYTHON_CMD="uv run python"
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
    
    # Copy selector scripts if they exist in the current directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    SCRIPTS_COPIED=0
    
    if [[ -f "$SCRIPT_DIR/select_copilots_interactive.py" ]]; then
        cp "$SCRIPT_DIR/select_copilots_interactive.py" "$PROJECT_DIR/"
        SCRIPTS_COPIED=1
    fi
    if [[ -f "$SCRIPT_DIR/select_copilots.py" ]]; then
        cp "$SCRIPT_DIR/select_copilots.py" "$PROJECT_DIR/"
        SCRIPTS_COPIED=1
    fi
    if [[ -f "$SCRIPT_DIR/select_copilots_simple.py" ]]; then
        cp "$SCRIPT_DIR/select_copilots_simple.py" "$PROJECT_DIR/"
        SCRIPTS_COPIED=1
    fi
    
    if [[ $SCRIPTS_COPIED -eq 1 ]]; then
        print_info "Copied copilot selector scripts"
    fi
    
    cd "$PROJECT_DIR"
    
    print_success "Repository cloned to $PROJECT_DIR"
}

# Setup Python environment with uv
setup_python_env() {
    print_step "Setting up Python virtual environment with uv..."
    
    # Initialize uv project if pyproject.toml doesn't exist
    if [[ ! -f "pyproject.toml" ]]; then
        print_info "Initializing uv project..."
        uv init --python 3.10.7
    fi
    
    # Create virtual environment with uv
    print_info "Creating virtual environment..."
    uv venv --python 3.10.7
    
    print_success "Virtual environment created with Python 3.10.7"
    
    # Install dependencies using uv
    print_info "Installing dependencies with uv..."
    
    # Install mcp[cli] using uv
    print_info "Installing MCP with CLI support..."
    uv add "mcp[cli]"
    print_success "Installed mcp[cli]"
    
    # Install answerrocket-client from git repository
    print_info "Installing answerrocket-client from git repository..."
    uv add "git+ssh://git@github.com/answerrocket/answerrocket-python-client.git@get-copilots-for-mcp"
    print_success "AnswerRocket client installed from git repository"
}

# Get copilot metadata
get_copilot_metadata() {
    print_step "Getting copilot metadata..."
    
    # Use the existing get_copilots.py script
    COPILOT_JSON=$(uv run python get_copilots.py "$AR_URL" "$AR_TOKEN")
    
    if [[ $? -ne 0 ]]; then
        print_error "Failed to get copilot metadata"
        exit 1
    fi
    
    # Store the full JSON for later use
    COPILOT_COUNT=$(echo "$COPILOT_JSON" | uv run python -c "import sys, json; print(len(json.load(sys.stdin)))")
    print_success "Found $COPILOT_COUNT copilots"
}

# Select copilots using TUI
select_copilots() {
    print_step "Select copilots to install..."
    echo
    
    # Create temporary file for copilot data
    TEMP_JSON=$(mktemp)
    echo "$COPILOT_JSON" > "$TEMP_JSON"
    
    # Debug: Check if we have a TTY
    if [[ -t 0 ]] && [[ -t 1 ]]; then
        print_info "Interactive terminal detected"
    else
        print_warning "Non-interactive environment detected"
    fi
    
    # Try the new robust selector first
    if [[ -f "select_copilots_interactive.py" ]]; then
        chmod +x select_copilots_interactive.py
        print_info "Launching interactive copilot selector..."
        
        # Create a temporary file for output
        TEMP_OUTPUT=$(mktemp)
        
        # Run the interactive selector with proper terminal handling
        if uv run python select_copilots_interactive.py "$TEMP_JSON" > "$TEMP_OUTPUT" 2>/tmp/select_error.log; then
            SELECTED_COPILOTS=$(cat "$TEMP_OUTPUT")
            SELECTION_STATUS=0
        else
            SELECTION_STATUS=$?
            print_warning "Interactive selector encountered an issue"
            # Show error details if available
            if [[ -f /tmp/select_error.log ]] && [[ -s /tmp/select_error.log ]]; then
                print_info "Error details: $(cat /tmp/select_error.log | head -1)"
            fi
        fi
        
        # Clean up temporary output file
        rm -f "$TEMP_OUTPUT"
    else
        # Try legacy selector
        if [[ -f "select_copilots.py" ]]; then
            chmod +x select_copilots.py
            print_info "Launching legacy interactive copilot selector..."
            
            # Force terminal allocation for the Python script
            SELECTED_COPILOTS=$(script -q /dev/null uv run python select_copilots.py "$TEMP_JSON" 2>/tmp/select_error.log | grep -v "Script")
            SELECTION_STATUS=$?
            
            if [[ $SELECTION_STATUS -ne 0 ]]; then
                print_warning "Legacy selector failed, trying simple selector..."
            fi
        fi
    fi
    
    # Fallback to simple selector if interactive failed
    if [[ $SELECTION_STATUS -ne 0 ]] || [[ -z "$SELECTED_COPILOTS" ]]; then
        if [[ -f "select_copilots_simple.py" ]]; then
            chmod +x select_copilots_simple.py
            print_info "Using simple selection mode..."
            SELECTED_COPILOTS=$(uv run python select_copilots_simple.py "$TEMP_JSON")
            SELECTION_STATUS=$?
        else
            print_error "No fallback selector found"
            rm -f "$TEMP_JSON"
            exit 1
        fi
    fi
    
    # Clean up temp file
    rm -f "$TEMP_JSON"
    
    if [[ $SELECTION_STATUS -ne 0 ]] || [[ -z "$SELECTED_COPILOTS" ]]; then
        print_error "No copilots selected. Installation cancelled."
        exit 1
    fi
    
    # Parse the selected copilots to get IDs and names
    COPILOT_DATA=$(echo "$SELECTED_COPILOTS" | uv run python -c "
import sys, json
data = json.load(sys.stdin)
for copilot in data:
    print(f\"{copilot['copilot_id']}|{copilot['name']}\")
")
    
    SELECTED_COUNT=$(echo "$COPILOT_DATA" | wc -l)
    print_success "Selected $SELECTED_COUNT copilots for installation"
}

# Install MCP servers for selected copilots
install_mcp_servers() {
    print_step "Installing MCP servers for selected copilots..."
    
    # Check if mcp command is available through uv
    if ! uv run mcp --help > /dev/null 2>&1; then
        print_error "mcp command not found in uv environment. Please ensure mcp[cli] is properly installed."
        exit 1
    fi
    
    # Install a server for each copilot
    INSTALLED_SERVERS=()
    while IFS='|' read -r copilot_id copilot_name; do
        if [[ -n "$copilot_id" ]]; then
            print_info "Installing MCP server for copilot: $copilot_name ($copilot_id)"
            
            # Create safe server name from copilot name
            # Remove special characters and spaces, convert to lowercase
            SAFE_COPILOT_NAME=$(echo "$copilot_name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')
            SERVER_NAME="${SAFE_COPILOT_NAME}-Assistant"
            
            if uv run mcp install server.py -n "$SERVER_NAME" -v "AR_URL=$AR_URL" -v "AR_TOKEN=$AR_TOKEN" -v "COPILOT_ID=$copilot_id" --with "git+ssh://git@github.com/answerrocket/answerrocket-python-client.git@get-copilots-for-mcp"; then
                print_success "Installed MCP server: $SERVER_NAME"
                INSTALLED_SERVERS+=("$SERVER_NAME ($copilot_name)")
            else
                print_warning "Failed to install MCP server for copilot: $copilot_name"
            fi
        fi
    done <<< "$COPILOT_DATA"
    
    if [[ ${#INSTALLED_SERVERS[@]} -eq 0 ]]; then
        print_error "No MCP servers were successfully installed"
        exit 1
    fi
    
    print_success "Successfully installed ${#INSTALLED_SERVERS[@]} MCP servers"
}

# Main installation function
main() {
    echo "🚀 AnswerRocket Multi-Copilot MCP Server Installer"
    echo "================================================="
    
    check_requirements
    install_uv
    get_user_input
    setup_project
    setup_python
    setup_python_env
    get_copilot_metadata
    select_copilots
    install_mcp_servers
    
    echo
    print_success "Installation completed successfully! 🎉"
    echo
    print_info "Your MCP servers are now installed and ready to use."
    print_info "Each copilot has its own dedicated MCP server:"
    echo
    for server in "${INSTALLED_SERVERS[@]}"; do
        echo "  - $server"
    done
    echo
    print_info "You can use these servers with MCP-compatible clients like Claude Desktop."
    echo
    print_info "Project location: $PROJECT_DIR"
    print_info "Configuration: AR_URL=$AR_URL"
    echo
    print_warning "Keep your API token secure and never share it publicly!"
}

# Run main function
main "$@" 