#!/bin/bash
#
# Submodule Sync Script for CI Environments
# ==========================================
#
# This script updates Git submodules to their latest versions and optionally
# creates a pull request with the changes.
#
# Usage:
#   ./sync_submodules.sh [OPTIONS]
#
# Options:
#   --no-commit     Don't commit the changes (just update locally)
#   --create-pr     Create a pull request with the updates
#   --branch NAME   Use specific branch name for PR
#   --verbose       Enable verbose output
#   --help          Show this help message
#
# Environment Variables:
#   GITHUB_TOKEN    GitHub token for authentication (required for --create-pr)
#

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR" && pwd)"

# Default options
COMMIT_CHANGES=true
CREATE_PR=false
BRANCH_NAME=""
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Help function
show_help() {
    cat << EOF
Submodule Sync Script for CI Environments

This script updates Git submodules to their latest versions and optionally
creates a pull request with the changes.

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --no-commit     Don't commit the changes (just update locally)
    --create-pr     Create a pull request with the updates
    --branch NAME   Use specific branch name for PR (auto-generated if not provided)
    --verbose       Enable verbose output
    --help          Show this help message

ENVIRONMENT VARIABLES:
    GITHUB_TOKEN    GitHub token for authentication (required for --create-pr)

EXAMPLES:
    # Update submodules and commit changes
    $0

    # Update submodules but don't commit
    $0 --no-commit

    # Update submodules and create a pull request
    $0 --create-pr

    # Update with custom branch name and verbose output
    $0 --create-pr --branch "update-godot-demos" --verbose

CI USAGE:
    # In GitHub Actions
    - name: Sync submodules
      run: ./sync_submodules.sh --create-pr
      env:
        GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}

    # In GitLab CI
    sync_submodules:
      script:
        - ./sync_submodules.sh --create-pr
      variables:
        GITHUB_TOKEN: \$GITHUB_TOKEN

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-commit)
            COMMIT_CHANGES=false
            shift
            ;;
        --create-pr)
            CREATE_PR=true
            shift
            ;;
        --branch)
            BRANCH_NAME="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

# Validate environment
log_info "Validating environment..."

# Check if we're in a git repository
if [[ ! -d ".git" ]]; then
    log_error "Not in a Git repository root"
    exit 1
fi

# Check for required tools
if ! command -v git >/dev/null 2>&1; then
    log_error "Git is not installed"
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    log_error "Python 3 is not installed"
    exit 1
fi

# Check GitHub CLI if creating PR
if [[ "$CREATE_PR" == "true" ]]; then
    if ! command -v gh >/dev/null 2>&1; then
        log_error "GitHub CLI (gh) is not installed but --create-pr was specified"
        log_info "Install GitHub CLI: https://cli.github.com/"
        exit 1
    fi
    
    # Check authentication
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        log_warning "GITHUB_TOKEN environment variable not set"
        log_info "Attempting to use existing gh authentication..."
        
        if ! gh auth status >/dev/null 2>&1; then
            log_error "GitHub CLI is not authenticated"
            log_info "Run 'gh auth login' or set GITHUB_TOKEN environment variable"
            exit 1
        fi
    else
        log_info "Using GITHUB_TOKEN for authentication"
        export GH_TOKEN="$GITHUB_TOKEN"
    fi
fi

# Build Python command
PYTHON_CMD="python3 ${SCRIPT_DIR}/build_system/tools/submodule_sync.py"
PYTHON_CMD+=" --repo-root ."

if [[ "$COMMIT_CHANGES" == "false" ]]; then
    PYTHON_CMD+=" --no-commit"
fi

if [[ "$CREATE_PR" == "true" ]]; then
    PYTHON_CMD+=" --create-pr"
fi

if [[ -n "$BRANCH_NAME" ]]; then
    PYTHON_CMD+=" --branch-name \"$BRANCH_NAME\""
fi

if [[ "$VERBOSE" == "true" ]]; then
    PYTHON_CMD+=" --verbose"
fi

# Display configuration
log_info "Configuration:"
log_info "  Repository: $(pwd)"
log_info "  Commit changes: $COMMIT_CHANGES"
log_info "  Create PR: $CREATE_PR"
if [[ -n "$BRANCH_NAME" ]]; then
    log_info "  Branch name: $BRANCH_NAME"
fi
log_info "  Verbose: $VERBOSE"
echo

# Run the sync
log_info "Starting submodule synchronization..."
if eval "$PYTHON_CMD"; then
    log_success "Submodule synchronization completed successfully!"
    
    if [[ "$CREATE_PR" == "true" ]]; then
        log_info "A pull request has been created for the submodule updates."
        log_info "Please review and merge when ready."
    elif [[ "$COMMIT_CHANGES" == "true" ]]; then
        log_info "Changes have been committed to the current branch."
        log_info "Don't forget to push the changes if needed."
    else
        log_info "Submodules updated locally but not committed."
        log_info "Use 'git status' to see the changes."
    fi
else
    log_error "Submodule synchronization failed!"
    exit 1
fi
