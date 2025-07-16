#!/bin/bash
# ============================================================================
# Codespace Environment Setup Script
# ============================================================================
# This script sets up a Codespace environment to match the GitHub Actions
# workflow for building Godot Examples Documentation.
#
# It reads the default Godot version from the GitHub Actions workflow and
# sets up the complete development environment.
#
# Usage:
#   ./setup-codespace.sh [GODOT_VERSION]
#
# Examples:
#   ./setup-codespace.sh              # Use default version from workflow
#   ./setup-codespace.sh 4.5-beta3    # Use specific version
#   ./setup-codespace.sh --check      # Check current environment
#   ./setup-codespace.sh --help       # Show help
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_FILE="$SCRIPT_DIR/.github/workflows/build-documentation-universal.yml"

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}" >&2
}

log_step() {
    echo -e "${CYAN}🔧 $1${NC}"
}

# Help function
show_help() {
    cat << 'EOF'
🚀 Codespace Environment Setup Script
=====================================

Sets up a complete development environment for building Godot Examples Documentation.
Automatically reads the default Godot version from the GitHub Actions workflow.

USAGE:
    ./setup-codespace.sh [OPTIONS] [GODOT_VERSION]

OPTIONS:
    --check         Check current environment status
    --help, -h      Show this help message
    --verbose, -v   Enable verbose output
    --force         Force reinstall even if already installed

ARGUMENTS:
    GODOT_VERSION   Godot version to install (defaults to workflow default)

EXAMPLES:
    ./setup-codespace.sh                    # Use default version from workflow
    ./setup-codespace.sh 4.5-beta3         # Use specific version
    ./setup-codespace.sh --check           # Check environment
    ./setup-codespace.sh --force           # Force reinstall
    ./setup-codespace.sh --verbose         # Verbose output

ENVIRONMENT:
    This script replicates the GitHub Actions workflow setup:
    1. Python 3.11 environment
    2. Python dependencies from requirements.txt
    3. Godot Engine (version from workflow or specified)
    4. Godot export templates
    5. Proper PATH configuration

EOF
}

# Function to extract default Godot version from workflow
get_default_godot_version() {
    local default_version=""
    
    if [[ -f "$WORKFLOW_FILE" ]]; then
        # Extract default version from workflow input
        default_version=$(grep -A 2 'godot_version:' "$WORKFLOW_FILE" | grep 'default:' | sed "s/.*default: *['\"]\\([^'\"]*\\)['\"].*/\\1/" | head -1)
        
        # If not found, try fallback from env section
        if [[ -z "$default_version" ]]; then
            default_version=$(grep 'GODOT_VERSION.*||' "$WORKFLOW_FILE" | sed "s/.*|| *['\"]\\([^'\"]*\\)['\"].*/\\1/" | head -1)
        fi
    fi
    
    # Fallback to 4.5-beta3 if nothing found
    if [[ -z "$default_version" ]]; then
        default_version="4.5-beta3"
    fi
    
    echo "$default_version"
}

# Function to check current environment
check_environment() {
    log_step "Checking current environment..."
    
    local issues=0
    
    # Check Python
    if command -v python3 >/dev/null 2>&1; then
        local python_version=$(python3 --version | cut -d' ' -f2)
        log_success "Python: $python_version"
    else
        log_error "Python 3 not found"
        ((issues++))
    fi
    
    # Check Godot
    if command -v godot >/dev/null 2>&1; then
        local godot_version=$(godot --version 2>/dev/null | head -1 || echo "Unknown")
        log_success "Godot: $godot_version"
    else
        log_warning "Godot not found in PATH"
        ((issues++))
    fi
    
    # Check if we have the build system
    if [[ -d "$SCRIPT_DIR/godot-ci-build-system" ]]; then
        log_success "Build system: Available"
    else
        log_error "Build system not found"
        ((issues++))
    fi
    
    # Check submodules
    if [[ -f "$SCRIPT_DIR/.gitmodules" ]]; then
        local submodule_status=$(git submodule status 2>/dev/null | grep -c "^-" || true)
        if [[ "$submodule_status" -eq 0 ]]; then
            log_success "Submodules: Initialized"
        else
            log_warning "Submodules: Not initialized ($submodule_status uninitialized)"
            ((issues++))
        fi
    fi
    
    # Check Python dependencies
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        if pip3 check >/dev/null 2>&1; then
            log_success "Python dependencies: OK"
        else
            log_warning "Python dependencies: Issues detected"
            ((issues++))
        fi
    fi
    
    echo
    if [[ $issues -eq 0 ]]; then
        log_success "Environment check passed! ✨"
        return 0
    else
        log_warning "Environment check found $issues issue(s)"
        return 1
    fi
}

# Function to setup Python environment
setup_python_environment() {
    log_step "Setting up Python environment..."
    
    # Check Python version
    local python_version=$(python3 --version | cut -d' ' -f2)
    log_info "Python version: $python_version"
    
    # Upgrade pip
    log_info "Upgrading pip..."
    python3 -m pip install --upgrade pip --user
    
    # Install requirements
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        log_info "Installing Python dependencies..."
        python3 -m pip install -r "$SCRIPT_DIR/requirements.txt" --user
        log_success "Python dependencies installed"
    else
        log_warning "requirements.txt not found"
    fi
}

# Function to setup Godot environment
setup_godot_environment() {
    local godot_version="$1"
    local force_install="$2"
    
    log_step "Setting up Godot $godot_version environment..."
    
    # Create local bin directory
    mkdir -p "$HOME/.local/bin"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        export PATH="$HOME/.local/bin:$PATH"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        log_info "Added ~/.local/bin to PATH"
    fi
    
    # Check if Godot is already installed
    if command -v godot >/dev/null 2>&1 && [[ "$force_install" != "true" ]]; then
        local current_version=$(godot --version 2>/dev/null | head -1 || echo "Unknown")
        log_info "Godot already installed: $current_version"
        
        # Still run setup to ensure export templates are available
        log_info "Ensuring export templates are available..."
    fi
    
    # Use the build system to setup Godot
    log_info "Running build system Godot setup..."
    
    # Create a temporary Python script to handle the installation
    cat > /tmp/setup_godot.py << EOF
import sys
import os
from pathlib import Path

# Add the build system to Python path
sys.path.insert(0, '$SCRIPT_DIR/godot-ci-build-system')

try:
    from tools.environment_manager import GodotEnvironmentManager
    from tools.progress_reporter import ProgressReporter
    
    # Create progress reporter
    progress = ProgressReporter(verbose=True)
    
    # Create environment manager
    manager = GodotEnvironmentManager(progress)
    
    # Install Godot to user directory
    user_bin_path = Path.home() / '.local/bin/godot'
    
    try:
        # Check if Godot is already working
        if user_bin_path.exists():
            progress.info(f"Godot binary already exists at: {user_bin_path}")
        else:
            # Install binary to user directory
            progress.info(f"Installing Godot binary to: {user_bin_path}")
            godot_path = manager.install_godot_binary('$godot_version', user_bin_path)
            if not godot_path:
                progress.error("Failed to install Godot binary")
                sys.exit(1)
        
        # Install export templates
        progress.info("Installing export templates...")
        success = manager.install_export_templates('$godot_version')
        if success:
            progress.success("✅ Export templates installed")
        else:
            progress.error("❌ Failed to install export templates")
            sys.exit(1)
            
    except Exception as e:
        progress.error(f"❌ Error during Godot setup: {e}")
        sys.exit(1)
        
except ImportError as e:
    print(f"❌ Failed to import build system: {e}")
    print("💡 Make sure submodules are initialized")
    sys.exit(1)
EOF
    
    # Run the setup
    if python3 /tmp/setup_godot.py; then
        log_success "Godot environment setup completed"
    else
        log_error "Godot environment setup failed"
        return 1
    fi
    
    # Clean up
    rm -f /tmp/setup_godot.py
}

# Function to initialize submodules
setup_submodules() {
    log_step "Setting up submodules..."
    
    if [[ -f "$SCRIPT_DIR/.gitmodules" ]]; then
        cd "$SCRIPT_DIR"
        
        # Initialize and update submodules
        git submodule update --init --recursive
        
        log_success "Submodules initialized"
    else
        log_warning "No .gitmodules file found"
    fi
}

# Function to verify setup
verify_setup() {
    local godot_version="$1"
    
    log_step "Verifying setup..."
    
    # Use the build system verify command
    if python3 "$SCRIPT_DIR/godot-ci-build-system/build.py" verify --godot-version "$godot_version" --verbose; then
        log_success "Setup verification passed! 🎉"
        return 0
    else
        log_error "Setup verification failed"
        return 1
    fi
}

# Main setup function
main() {
    local godot_version=""
    local check_only=false
    local force_install=false
    local verbose=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --check)
                check_only=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            --verbose|-v)
                verbose=true
                shift
                ;;
            --force)
                force_install=true
                shift
                ;;
            -*)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                godot_version="$1"
                shift
                ;;
        esac
    done
    
    # If no version specified, get default from workflow
    if [[ -z "$godot_version" ]]; then
        godot_version=$(get_default_godot_version)
    fi
    
    echo -e "${CYAN}🚀 Codespace Environment Setup${NC}"
    echo -e "${CYAN}================================${NC}"
    echo
    log_info "Godot version: $godot_version (from workflow default)"
    log_info "Script directory: $SCRIPT_DIR"
    echo
    
    # Check environment if requested
    if [[ "$check_only" == "true" ]]; then
        check_environment
        exit $?
    fi
    
    # Perform setup steps
    log_info "🏁 Starting environment setup..."
    echo
    
    # Step 1: Setup submodules
    setup_submodules
    echo
    
    # Step 2: Setup Python environment
    setup_python_environment
    echo
    
    # Step 3: Setup Godot environment
    setup_godot_environment "$godot_version" "$force_install"
    echo
    
    # Step 4: Verify setup
    verify_setup "$godot_version"
    echo
    
    # Final instructions
    echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
    echo
    echo -e "${CYAN}Next steps:${NC}"
    echo "1. Restart your terminal or run: source ~/.bashrc"
    echo "2. Test the build system: ./build.sh --check-deps"
    echo "3. Run a build: ./build.sh --preview"
    echo "4. Or build everything: ./build.sh"
    echo
    echo -e "${CYAN}Useful commands:${NC}"
    echo "- Check environment: ./setup-codespace.sh --check"
    echo "- Build with progress: ./build.sh --progress --verbose"
    echo "- Sync submodules: ./build.sh --sync-submodules"
    echo
}

# Run main function
main "$@"
