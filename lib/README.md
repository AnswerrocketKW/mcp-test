# Library Structure

This directory contains modular bash libraries that support the AnswerRocket MCP Server installation.

## File Structure

```
lib/
├── README.md           # This file
├── common.sh          # Common utilities (logging, OS detection, user input)
├── deps.sh            # Dependency installation (uv, Python, packages)
├── project.sh         # Project setup (cloning, environment setup)
└── copilots.sh        # Copilot management (fetching, selection, MCP installation)
```

## Library Overview

### `common.sh`
- **Purpose**: Common utilities and functions used across all scripts
- **Functions**:
  - `log_error()`, `log_success()`, `log_info()`, `log_warning()`, `log_step()` - Colored logging functions
  - `command_exists()` - Check if a command is available
  - `detect_os()` - Detect operating system (macOS, Linux, Windows)
  - `check_requirements()` - Verify system requirements (curl, git)
  - `get_ar_url()` - Get AnswerRocket URL from user or arguments
  - `get_ar_token()` - Get AnswerRocket API token from user or arguments

### `deps.sh`
- **Purpose**: Handle all dependency installation
- **Functions**:
  - `install_uv()` - Install uv package manager
  - `setup_python()` - Install Python with uv
  - `setup_python_env()` - Create virtual environment and install dependencies

### `project.sh`
- **Purpose**: Manage project setup and repository operations
- **Functions**:
  - `setup_project()` - Setup project directory (local or clone from GitHub)
  - `copy_selector_scripts()` - Copy copilot selector scripts
  - `validate_connection()` - Validate connection to AnswerRocket instance

### `copilots.sh`
- **Purpose**: Handle copilot-specific operations
- **Functions**:
  - `get_copilot_metadata()` - Fetch available copilots from AnswerRocket
  - `select_copilots()` - Interactive copilot selection with fallback
  - `install_mcp_servers()` - Install MCP servers for selected copilots

## Usage

These libraries are sourced by the main `install.sh` script:

```bash
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/deps.sh"
source "$SCRIPT_DIR/lib/project.sh"
source "$SCRIPT_DIR/lib/copilots.sh"
```

## Benefits of This Structure

1. **Modularity**: Each library has a specific responsibility
2. **Maintainability**: Easy to update specific functionality without affecting others
3. **Reusability**: Functions can be used in other scripts
4. **Readability**: Main script is much shorter and clearer
5. **Testing**: Individual libraries can be tested in isolation

## Error Handling

All library functions use the common logging functions and follow bash best practices:
- Use `local` variables for function parameters
- Return appropriate exit codes
- Use `unset VIRTUAL_ENV` to avoid path mismatch warnings where needed
- Proper error messages with context 