#!/bin/bash
"""
SCons Build System Wrapper for Godot Examples Documentation
===========================================================

This script provides a convenient way to run the SCons-based build system
with proper environment setup and error handling.

Usage:
    ./scons_build.sh [options] [targets]
    
Options:
    --dry-run           Show what would be built without building
    --progress          Show real-time build progress  
    --projects-dir DIR  Specify projects directory (default: ../godot-demo-projects)
    --godot-binary PATH Specify Godot binary path (default: godot)
    --build-mode MODE   Set build mode: debug or release (default: release)
    --jobs N            Number of parallel jobs (default: auto)
    --help              Show this help message

Targets:
    build               Build game exports only
    docs                Build documentation only  
    final               Build final docs with embeds
    all                 Build everything (default)

Examples:
    ./scons_build.sh                           # Build all targets
    ./scons_build.sh --dry-run                 # Show build plan
    ./scons_build.sh --progress build          # Build exports with progress
    ./scons_build.sh --projects-dir ./projects # Use custom projects dir
"""

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Default values
DRY_RUN=false
SHOW_PROGRESS=false
PROJECTS_DIR="../godot-demo-projects"
GODOT_BINARY="godot"
BUILD_MODE="release"
JOBS=$(sysctl -n hw.ncpu 2>/dev/null || echo "4")
JOBS=$((JOBS > 1 ? JOBS - 1 : 1))  # Leave one core free
SHOW_HELP=false
SCONS_ARGS=()

# Build system directory
BUILD_SYSTEM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCONS_FILE="$BUILD_SYSTEM_DIR/SConstruct"

# Function to print colored output
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

print_header() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

# Function to show help
show_help() {
    echo "SCons Build System for Godot Examples Documentation"
    echo "=================================================="
    echo
    echo "Usage: $0 [options] [targets]"
    echo
    echo "Options:"
    echo "  --dry-run           Show what would be built without building"
    echo "  --progress          Show real-time build progress"
    echo "  --projects-dir DIR  Specify projects directory (default: $PROJECTS_DIR)"
    echo "  --godot-binary PATH Specify Godot binary path (default: $GODOT_BINARY)"
    echo "  --build-mode MODE   Set build mode: debug or release (default: $BUILD_MODE)"
    echo "  --jobs N            Number of parallel jobs (default: $JOBS)"
    echo "  --help              Show this help message"
    echo
    echo "Targets:"
    echo "  build               Build game exports only"
    echo "  docs                Build documentation only"
    echo "  final               Build final docs with embeds"
    echo "  all                 Build everything (default)"
    echo
    echo "Examples:"
    echo "  $0                           # Build all targets"
    echo "  $0 --dry-run                 # Show build plan"
    echo "  $0 --progress build          # Build exports with progress"
    echo "  $0 --projects-dir ./projects # Use custom projects dir"
}
    echo "Options:"
    echo "  -j, --jobs N           Number of parallel jobs (default: $JOBS)"
    echo "  -v, --verbose          Enable verbose output"
    echo "  -f, --force-rebuild    Force rebuild all targets"
    echo "  --target=PLATFORM      Target platform (web, linux, windows, macos)"
    echo "  --godot-binary=PATH    Path to Godot binary"
    echo "  --cache-dir=DIR        Build cache directory"
    echo "  --projects-dir=DIR     Root directory containing projects"
    echo "  -h, --help             Show this help"
    echo ""
    echo "Targets:"
    echo "  build                  Build all projects (default)"
    echo "  clean                  Clean build cache and outputs"
    echo "  test                   Run build tests"
    echo "  install                Install built documentation"
    echo ""
    echo "Examples:"
    echo "  $0                     # Build all projects"
    echo "  $0 -j 4 build          # Build with 4 parallel jobs"
    echo "  $0 --verbose build     # Build with verbose output"
    echo "  $0 clean build         # Clean then build"
    echo ""
    echo "SCons-style variables:"
    echo "  jobs=N                 Set number of parallel jobs"
    echo "  verbose=1              Enable verbose output"
    echo "  target=web             Set target platform"
    echo ""
    echo "  $0 jobs=8 verbose=1    # SCons-style arguments"
}

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%H:%M:%S')
    
    case "$level" in
        "INFO")    echo -e "${BLUE}[${timestamp}] ℹ️  $message${NC}" ;;
        "SUCCESS") echo -e "${GREEN}[${timestamp}] ✅ $message${NC}" ;;
        "ERROR")   echo -e "${RED}[${timestamp}] ❌ $message${NC}" ;;
        "WARN")    echo -e "${YELLOW}[${timestamp}] ⚠️  $message${NC}" ;;
        "STEP")    echo -e "${PURPLE}[${timestamp}] 🔄 $message${NC}" ;;
    esac
}

parse_scons_args() {
    # Parse SCons-style key=value arguments
    for arg in "$@"; do
        if [[ "$arg" == *"="* ]]; then
            key="${arg%%=*}"
            value="${arg#*=}"
            
            case "$key" in
                "jobs"|"j") JOBS="$value" ;;
                "verbose"|"v") 
                    if [[ "$value" == "1" || "$value" == "true" ]]; then
                        VERBOSE=true
                    fi
                    ;;
                "force_rebuild"|"f")
                    if [[ "$value" == "1" || "$value" == "true" ]]; then
                        FORCE_REBUILD=true
                    fi
                    ;;
                "target") TARGET="$value" ;;
                "godot_binary") GODOT_BINARY="$value" ;;
                "cache_dir") CACHE_DIR="$value" ;;
                "projects_dir") PROJECTS_DIR="$value" ;;
            esac
        fi
    done
}

build_target() {
    log "STEP" "Starting SCons-like build process"
    
    # Set environment variables for our build system
    export MAX_PARALLEL_JOBS="$JOBS"
    export VERBOSE="$VERBOSE"
    
    # Choose build method
    if command -v python3 >/dev/null 2>&1; then
        log "INFO" "Using Python-based SCons-like build system"
        
        # Run our Python build system
        python3 docsh/scons_build.py \
            --jobs "$JOBS" \
            ${VERBOSE:+--verbose} \
            ${FORCE_REBUILD:+--force-rebuild} \
            --godot-binary "$GODOT_BINARY" \
            --cache-dir "$CACHE_DIR" \
            --projects-dir "$PROJECTS_DIR"
        
    else
        log "INFO" "Python not available, using enhanced parallel build"
        
        # Fallback to our bash-based system
        if [ "$FORCE_REBUILD" = true ]; then
            clean_target
        fi
        
        # Run enhanced parallel build
        ./docsh/05_build_godot_projects_parallel_enhanced.sh
    fi
}

clean_target() {
    log "STEP" "Cleaning build cache and outputs"
    
    # Clean build cache
    if [ -d "$CACHE_DIR" ]; then
        rm -rf "$CACHE_DIR"
        log "SUCCESS" "Removed build cache: $CACHE_DIR"
    fi
    
    # Clean exports
    if [ -d "$PROJECTS_DIR" ]; then
        find "$PROJECTS_DIR" -type d -name "exports" -exec rm -rf {} + 2>/dev/null || true
        find "$PROJECTS_DIR" -name "export_presets.cfg" -delete 2>/dev/null || true
        log "SUCCESS" "Cleaned project exports"
    fi
    
    # Clean documentation files
    rm -f _sidebar.md _subnav.md 2>/dev/null || true
    log "SUCCESS" "Cleaned generated documentation files"
}

test_target() {
    log "STEP" "Running build system tests"
    
    # Run quick parallel test
    if [ -f "docsh/quick_test_parallel.sh" ]; then
        ./docsh/quick_test_parallel.sh
    else
        log "WARN" "Test script not found"
        return 1
    fi
}

install_target() {
    log "STEP" "Installing documentation"
    
    # This would copy built files to installation directory
    # For now, just run the complete build process
    ./docsh/build.sh
}

performance_target() {
    log "STEP" "Running performance comparison"
    
    if [ -f "docsh/performance_comparison.sh" ]; then
        chmod +x docsh/performance_comparison.sh
        ./docsh/performance_comparison.sh
    else
        log "WARN" "Performance comparison script not found"
    fi
}

main() {
    local targets=()
    local show_help_flag=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -j|--jobs)
                JOBS="$2"
                shift 2
                ;;
            -j*)
                JOBS="${1#-j}"
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -f|--force-rebuild)
                FORCE_REBUILD=true
                shift
                ;;
            --target=*)
                TARGET="${1#*=}"
                shift
                ;;
            --godot-binary=*)
                GODOT_BINARY="${1#*=}"
                shift
                ;;
            --cache-dir=*)
                CACHE_DIR="${1#*=}"
                shift
                ;;
            --projects-dir=*)
                PROJECTS_DIR="${1#*=}"
                shift
                ;;
            -h|--help)
                show_help_flag=true
                shift
                ;;
            *=*)
                # SCons-style argument, will be parsed later
                shift
                ;;
            *)
                # Target
                targets+=("$1")
                shift
                ;;
        esac
    done
    
    # Parse SCons-style arguments
    parse_scons_args "$@"
    
    if [ "$show_help_flag" = true ]; then
        show_help
        exit 0
    fi
    
    # Default target if none specified
    if [ ${#targets[@]} -eq 0 ]; then
        targets=("build")
    fi
    
    # Show banner
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║          🛠️  SCons-like Godot Examples Build            ║"
    echo "║             Inspired by Godot's build system            ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Show configuration
    echo -e "${CYAN}🔧 Build Configuration:${NC}"
    echo "   Jobs: $JOBS"
    echo "   Verbose: $VERBOSE"
    echo "   Target: $TARGET"
    echo "   Godot: $GODOT_BINARY"
    echo "   Cache: $CACHE_DIR"
    echo "   Projects: $PROJECTS_DIR"
    echo ""
    
    # Execute targets
    local start_time=$(date +%s)
    local success=true
    
    for target in "${targets[@]}"; do
        case "$target" in
            "build"|"all")
                if ! build_target; then
                    success=false
                    break
                fi
                ;;
            "clean")
                clean_target
                ;;
            "test")
                if ! test_target; then
                    success=false
                    break
                fi
                ;;
            "install")
                if ! install_target; then
                    success=false
                    break
                fi
                ;;
            "performance"|"perf")
                performance_target
                ;;
            *)
                log "ERROR" "Unknown target: $target"
                echo ""
                show_help
                exit 1
                ;;
        esac
    done
    
    # Show summary
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    echo ""
    if [ "$success" = true ]; then
        log "SUCCESS" "All targets completed successfully"
    else
        log "ERROR" "Some targets failed"
    fi
    
    echo -e "${CYAN}⏱️  Total build time: ${minutes}m ${seconds}s${NC}"
    echo -e "${CYAN}🚀 Used $JOBS parallel jobs${NC}"
    
    exit $([ "$success" = true ] && echo 0 || echo 1)
}

# Run main function
main "$@"
