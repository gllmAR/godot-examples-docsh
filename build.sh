#!/bin/bash
# Universal Godot Build System Wrapper
# Simple bash wrapper for the Python-based build system

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_SYSTEM_DIR="$SCRIPT_DIR/godot-ci-build-system"

# Function to check dependencies
check_dependencies() {
    echo -e "${BLUE}🔍 Checking system dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is required but not found${NC}"
        return 1
    fi
    
    # Run the Python dependency checker
    if python3 "$BUILD_SYSTEM_DIR/tools/dependency_checker.py" "$@"; then
        echo -e "${GREEN}✅ All dependencies satisfied!${NC}"
        return 0
    else
        echo -e "${RED}❌ Dependency check failed!${NC}"
        echo -e "${YELLOW}💡 Tip: Run with --auto-install to attempt automatic installation${NC}"
        return 1
    fi
}

# Check if build system directory exists
if [[ ! -d "$BUILD_SYSTEM_DIR" ]]; then
    echo -e "${RED}❌ Build system directory not found: $BUILD_SYSTEM_DIR${NC}"
    exit 1
fi

# Function to show help
show_help() {
    cat << 'EOF'
Godot Examples Documentation Build System
========================================

Simple wrapper for the Universal Godot Build System.
This script provides an easy interface to build the Godot Examples documentation.

Usage:
    ./build.sh [options]

Options:
    --help              Show this help message
    --check-deps        Check system dependencies and show installation guide
    --auto-install      Check dependencies and attempt to auto-install missing packages
    --skip-deps         Skip dependency checking (not recommended)
    --clean             Clean all build artifacts and perform fresh build
    --preview           Show what would be built without building
    --progress          Show real-time build progress  
    --verbose           Enable verbose output
    --jobs N            Number of parallel jobs (default: auto-detect)
    --godot-binary PATH Path to Godot binary (default: godot)
    --godot-version VER Expected Godot version (for validation)
    --build-mode MODE   Build mode: debug or release (default: release)
    --sync-submodules   Update Git submodules to latest versions

Build Targets:
    build               Build all game exports
    docs                Build documentation 
    final               Build final docs with embeds
    add-markers         Add embed markers to README files
    inject-embeds       Inject actual embeds into README files  
    all                 Build everything (default)
    sync-submodules     Update Git submodules (alias for --sync-submodules)

Examples:
    ./build.sh                          # Build everything
    ./build.sh --check-deps             # Check system dependencies
    ./build.sh --auto-install           # Check deps and auto-install missing packages
    ./build.sh --clean                  # Clean build artifacts and rebuild
    ./build.sh --preview               # Show build plan
    ./build.sh --progress build        # Build with progress, exports only
    ./build.sh --jobs 4 --verbose      # Build with 4 jobs, verbose output
    ./build.sh --sync-submodules        # Update submodules to latest versions
    ./build.sh sync-submodules --verbose # Update submodules with verbose output
EOF
    exit 0
}

# Function to perform clean build
clean_build() {
    echo -e "${YELLOW}🧹 Performing clean build...${NC}"
    
    # Remove all export directories from Godot projects
    echo -e "${YELLOW}🗑️  Removing all export directories...${NC}"
    find "$SCRIPT_DIR/godot-demo-projects" -name "exports" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Clean build cache and temporary files
    echo -e "${YELLOW}🧽 Cleaning build cache and temporary files...${NC}"
    rm -rf "$BUILD_SYSTEM_DIR/.build_cache" 2>/dev/null || true
    rm -rf "$BUILD_SYSTEM_DIR/cache" 2>/dev/null || true
    rm -rf "$BUILD_SYSTEM_DIR/build" 2>/dev/null || true
    
    # Clean any .godot directories from export paths
    echo -e "${YELLOW}🧼 Cleaning temporary .godot directories...${NC}"
    find "$SCRIPT_DIR/godot-demo-projects" -name ".godot" -type d -path "*/exports/*" -exec rm -rf {} + 2>/dev/null || true
    
    echo -e "${GREEN}✅ Clean completed!${NC}"
}

# Parse arguments
PYTHON_ARGS=()
BUILD_TARGET=""
CLEAN_BUILD=false
CHECK_DEPS_ONLY=false
AUTO_INSTALL=false
SKIP_DEPS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            ;;
        --check-deps)
            CHECK_DEPS_ONLY=true
            shift
            ;;
        --auto-install)
            AUTO_INSTALL=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --clean)
            CLEAN_BUILD=true
            PYTHON_ARGS+=("--clean")
            shift
            ;;
        --preview)
            PYTHON_ARGS+=("--preview")
            shift
            ;;
        --progress)
            PYTHON_ARGS+=("--progress")
            shift
            ;;
        --verbose|-v)
            PYTHON_ARGS+=("--verbose")
            shift
            ;;
        --jobs|-j)
            PYTHON_ARGS+=("--jobs" "$2")
            shift 2
            ;;
        --godot-version)
            PYTHON_ARGS+=("--godot-version" "$2")
            shift 2
            ;;
        --dry-run)
            PYTHON_ARGS+=("--dry-run")
            shift
            ;;
        --force-rebuild)
            PYTHON_ARGS+=("--force-rebuild")
            shift
            ;;
        --no-change-detection)
            PYTHON_ARGS+=("--no-change-detection")
            shift
            ;;
        --sync-submodules)
            echo -e "${BLUE}🔄 Syncing submodules to latest versions...${NC}"
            "$SCRIPT_DIR/sync_submodules.sh" --verbose
            exit $?
            ;;
        build|docs|final|all|setup|verify|artifact|sync-submodules)
            if [[ "$1" == "sync-submodules" ]]; then
                echo -e "${BLUE}🔄 Syncing submodules to latest versions...${NC}"
                shift
                # Pass remaining arguments to sync script
                "$SCRIPT_DIR/sync_submodules.sh" "$@"
                exit $?
            else
                BUILD_TARGET="$1"
                shift
            fi
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Add build target if specified
if [[ -n "$BUILD_TARGET" ]]; then
    PYTHON_ARGS+=("$BUILD_TARGET")
else
    PYTHON_ARGS+=("all")
fi

# Print header
echo -e "${BLUE}🚀 Godot Examples Documentation Build System${NC}"
echo -e "${BLUE}=============================================${NC}"

# Handle dependency checking
if [[ "$CHECK_DEPS_ONLY" == true ]]; then
    # Only check dependencies and exit
    if [[ "$AUTO_INSTALL" == true ]]; then
        check_dependencies --auto-install
    else
        check_dependencies
    fi
    exit $?
elif [[ "$SKIP_DEPS" != true ]]; then
    # Check dependencies as part of normal build process
    echo -e "${BLUE}🔍 Checking dependencies before build...${NC}"
    if [[ "$AUTO_INSTALL" == true ]]; then
        if ! check_dependencies --auto-install; then
            echo -e "${RED}❌ Dependency check failed. Cannot proceed with build.${NC}"
            echo -e "${YELLOW}💡 Try running: ./build.sh --check-deps${NC}"
            exit 1
        fi
    else
        if ! check_dependencies; then
            echo -e "${RED}❌ Dependency check failed. Cannot proceed with build.${NC}"
            echo -e "${YELLOW}💡 Try running: ./build.sh --auto-install${NC}"
            echo -e "${YELLOW}💡 Or skip with: ./build.sh --skip-deps (not recommended)${NC}"
            exit 1
        fi
    fi
    echo ""
fi

# Print build info
echo -e "${GREEN}📁 Project Root:${NC} $SCRIPT_DIR"
echo -e "${GREEN}⚙️  Build Arguments:${NC} ${PYTHON_ARGS[*]}"

# Run the new Python-based build system
echo -e "\n${GREEN}🏃 Starting build...${NC}"
cd "$SCRIPT_DIR"
if python3 "$BUILD_SYSTEM_DIR/build.py" "${PYTHON_ARGS[@]}"; then
    echo -e "\n${GREEN}✅ Build completed successfully!${NC}"
else
    echo -e "\n${RED}❌ Build failed!${NC}"
    exit 1
fi
