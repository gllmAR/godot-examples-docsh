#!/bin/bash
# Godot Examples Documentation Build System
# Simple wrapper for the SCons-based build system

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_SYSTEM_DIR="$SCRIPT_DIR/build_system"

# Function to check dependencies
check_dependencies() {
    echo -e "${BLUE}🔍 Checking system dependencies...${NC}"
    
    # Run the Python dependency checker
    if command -v python3 &> /dev/null; then
        if python3 "$BUILD_SYSTEM_DIR/tools/dependency_checker.py" "$@"; then
            echo -e "${GREEN}✅ All dependencies satisfied!${NC}"
            return 0
        else
            echo -e "${RED}❌ Dependency check failed!${NC}"
            echo -e "${YELLOW}💡 Tip: Run with --auto-install to attempt automatic installation${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Python 3 not found!${NC}"
        echo -e "${YELLOW}Please install Python 3.6+ first:${NC}"
        case "$OSTYPE" in
            darwin*)
                echo "  brew install python3"
                ;;
            linux*)
                echo "  sudo apt install python3  # Debian/Ubuntu"
                echo "  sudo dnf install python3  # Fedora"
                echo "  sudo pacman -S python     # Arch"
                ;;
            msys*|cygwin*)
                echo "  Download from: https://www.python.org/downloads/"
                ;;
        esac
        return 1
    fi
}

# Legacy SCons check (kept for compatibility)
legacy_scons_check() {
    if ! command -v scons &> /dev/null; then
        echo -e "${RED}❌ SCons not found!${NC}"
        echo "Please install SCons using: brew install scons"
        return 1
    fi
    return 0
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

Simple wrapper for the SCons-based build system.
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

Build Targets:
    build               Build all game exports
    docs                Build documentation 
    final               Build final docs with embeds
    add-markers         Add embed markers to README files
    inject-embeds       Inject actual embeds into README files  
    all                 Build everything (default)

Examples:
    ./build.sh                          # Build everything
    ./build.sh --check-deps             # Check system dependencies
    ./build.sh --auto-install           # Check deps and auto-install missing packages
    ./build.sh --clean                  # Clean build artifacts and rebuild
    ./build.sh --preview               # Show build plan
    ./build.sh --progress build        # Build with progress, exports only
    ./build.sh --jobs 4 --verbose      # Build with 4 jobs, verbose output
EOF
    exit 0
}

# Function to perform clean build
clean_build() {
    echo -e "${YELLOW}🧹 Performing clean build...${NC}"
    
    # Remove all export directories from Godot projects
    echo -e "${YELLOW}🗑️  Removing all export directories...${NC}"
    find "$SCRIPT_DIR/godot-demo-projects" -name "exports" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Clean SCons cache and build files
    echo -e "${YELLOW}🧽 Cleaning SCons cache and build files...${NC}"
    rm -rf "$BUILD_SYSTEM_DIR/.scons_cache" 2>/dev/null || true
    rm -f "$BUILD_SYSTEM_DIR/.sconsign.dblite" 2>/dev/null || true
    rm -rf "$BUILD_SYSTEM_DIR/build" 2>/dev/null || true
    
    # Clean any .godot directories from export paths
    echo -e "${YELLOW}🧼 Cleaning temporary .godot directories...${NC}"
    find "$SCRIPT_DIR/godot-demo-projects" -name ".godot" -type d -path "*/exports/*" -exec rm -rf {} + 2>/dev/null || true
    
    echo -e "${GREEN}✅ Clean completed!${NC}"
}

# Parse arguments
SCONS_ARGS=()
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
            shift
            ;;
        --preview)
            SCONS_ARGS+=("--preview")
            shift
            ;;
        --progress)
            SCONS_ARGS+=("--progress")
            shift
            ;;
        --verbose|-v)
            SCONS_ARGS+=("verbose=1")
            shift
            ;;
        --jobs|-j)
            SCONS_ARGS+=("-j$2")
            shift 2
            ;;
        --godot-binary)
            SCONS_ARGS+=("--godot-binary=$2")
            shift 2
            ;;
        --godot-version)
            SCONS_ARGS+=("--godot-version=$2")
            shift 2
            ;;
        --build-mode)
            SCONS_ARGS+=("--build-mode=$2")
            shift 2
            ;;
        build|docs|final|add-markers|inject-embeds|all)
            BUILD_TARGET="$1"
            shift
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
    SCONS_ARGS+=("$BUILD_TARGET")
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

# Perform clean if requested
if [[ "$CLEAN_BUILD" == true ]]; then
    clean_build
    echo ""
fi

# Handle special build targets
if [[ "$BUILD_TARGET" == "add-markers" ]]; then
    echo -e "\n${GREEN}🔗 Adding embed markers to README files...${NC}"
    cd "$SCRIPT_DIR"
    python build_system/builders/embed_injector.py add-markers --projects-dir godot-demo-projects --verbose
    exit $?
elif [[ "$BUILD_TARGET" == "inject-embeds" ]]; then
    echo -e "\n${GREEN}🎮 Injecting embeds into README files...${NC}"
    cd "$SCRIPT_DIR" 
    python build_system/builders/embed_injector.py --projects-dir godot-demo-projects --verbose
    exit $?
elif [[ "$BUILD_TARGET" == "final" ]]; then
    # Build everything then inject embeds
    SCONS_ARGS+=("all")
    echo -e "\n${GREEN}🏃 Building projects first...${NC}"
    if scons "${SCONS_ARGS[@]}"; then
        echo -e "\n${GREEN}🎮 Now injecting embeds...${NC}"
        cd "$SCRIPT_DIR"
        python build_system/builders/embed_injector.py --projects-dir godot-demo-projects --verbose
        if [[ $? -eq 0 ]]; then
            echo -e "\n${GREEN}✅ Final build with embeds completed successfully!${NC}"
        else
            echo -e "\n${YELLOW}⚠️  Build completed but embed injection had warnings${NC}"
        fi
    else
        echo -e "\n${RED}❌ Build failed!${NC}"
        exit 1
    fi
    exit 0
fi

# Change to build system directory
cd "$BUILD_SYSTEM_DIR"

# Print build info
echo -e "${GREEN}📁 Build System:${NC} $BUILD_SYSTEM_DIR"
echo -e "${GREEN}⚙️  SCons Arguments:${NC} ${SCONS_ARGS[*]}"

# Run SCons
echo -e "\n${GREEN}🏃 Starting build...${NC}"
if scons "${SCONS_ARGS[@]}"; then
    echo -e "\n${GREEN}✅ Build completed successfully!${NC}"
else
    echo -e "\n${RED}❌ Build failed!${NC}"
    exit 1
fi
