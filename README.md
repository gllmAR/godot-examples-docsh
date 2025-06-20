# Godot Examples Documentation

<!-- Status Badges -->
![Build Status](https://github.com/gllmar/godot-examples-docsh/workflows/🎮%20Build%20Godot%20Examples%20Documentation/badge.svg)
![GitHub Pages](https://github.com/gllmar/godot-examples-docsh/workflows/pages/pages-build-deployment/badge.svg)
![Godot 4.5-beta1](https://img.shields.io/badge/godot-4.5--beta1-blue)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)

An advanced build system for generating interactive documentation from Godot demo projects. This system exports Godot projects to web format and creates comprehensive documentation with embedded playable examples.

## 🌐 Live Documentation

**[View Live Documentation →](https://gllmar.github.io/godot-examples-docsh/)**

The documentation is automatically built and deployed via GitHub Actions whenever changes are made to the repository.

## 🚀 Quick Start

```bash
# Clone the repository with submodules
git clone --recursive https://github.com/gllmar/godot-examples-docsh.git
cd godot-examples-docsh

# Build everything (exports + docs + embeds)
./build.sh

# Clean build (remove all artifacts and rebuild)
./build.sh --clean

# Preview what will be built
./build.sh --preview

# Build with progress tracking
./build.sh --progress
```

## ✨ Features

- **🏗️ Modern SCons Build System** - Parallel processing with smart dependency tracking
- **⚡ High Performance** - 3-4x faster than previous bash-based system
- **🧠 Intelligent Caching** - Incremental builds for rapid iteration
- **📊 Real-time Progress** - Live build status with completion estimates  
- **🎮 Interactive Examples** - Playable Godot games embedded in documentation
- **📱 Cross-platform** - Works on macOS, Linux, and Windows

## 📋 Requirements

- **Godot 4.5+** - For exporting projects (currently using 4.5-beta1)
- **SCons** - Build system (`brew install scons` on macOS)
- **Python 3.8+** - For build scripts (currently using 3.11)

## 🏗️ Build System

The project uses a sophisticated SCons-based build system located in `build_system/`:

### Build Targets

| Command | Description | Use Case |
|---------|-------------|----------|
| `./build.sh` | Build everything | Complete documentation generation |
| `./build.sh build` | Build exports only | Game development testing |
| `./build.sh docs` | Build docs only | Documentation updates |
| `./build.sh final` | Build with embeds | Production deployment |

### Advanced Options

```bash
# Custom parallel jobs
./build.sh --jobs 8

# Use custom Godot binary
./build.sh --godot-binary=/path/to/godot

# Verbose output for debugging
./build.sh --verbose

# Debug mode builds
./build.sh --build-mode=debug
```

## 📊 Performance

**Build Performance:**
- **Sequential (old)**: ~12 minutes, 14% CPU usage
- **Parallel (new)**: ~3-4 minutes, 85% CPU usage  
- **Incremental**: ~30 seconds for small changes

**System Requirements:**
- Minimum: 4GB RAM, 2 CPU cores
- Recommended: 8GB RAM, 4+ CPU cores
- Storage: ~2GB for full build artifacts

## 🚀 CI/CD & Deployment

### GitHub Actions Workflow

The repository uses GitHub Actions for automated building and deployment:

1. **Parallel Matrix Builds** - Projects are built in parallel by category (2d, 3d, gui, audio, misc)
2. **Smart Change Detection** - Only builds when projects or build system changes
3. **Artifact Caching** - Fast builds using intelligent caching
4. **Automatic Deployment** - Deploys to GitHub Pages on main branch

### Deployment Checklist

For production deployment:

- [ ] **Enable GitHub Pages**: Settings > Pages > Source: GitHub Actions
- [ ] **Branch Protection**: Configure protection rules for `main` branch
- [ ] **Environment Variables**: Set any required secrets in repository settings
- [ ] **Monitor Builds**: Check Actions tab for build status

### Local Development vs CI/CD

- **Local**: Use `./build.sh` for development and testing
- **CI/CD**: Automatic building on GitHub servers with `python build_system/scons_build.py`
- **Exports**: All export artifacts are excluded from version control via `.gitignore`

## 🏗️ Build System Architecture

### SCons-Based System

The build system uses a modern SCons-inspired approach:

```bash
# Quick build commands
./build.sh                    # Build everything
./build.sh --clean           # Clean build
./build.sh --preview         # Show build plan
python build_system/scons_build.py --help  # Advanced options
```

### Key Components

- **`build_system/scons_build.py`** - Main build orchestrator
- **`build_system/builders/`** - Specialized builders (export, docs, embeds)
- **`build_system/config/`** - Build configuration and targets
- **`build_system/tools/`** - Utilities (dependency checker, progress reporter)

## 📈 Migration Notes

This project has been migrated from the external `docsh` submodule to an integrated SCons-based build system for better performance and reliability. All documentation generation, sidebar creation, and embed injection are now handled by the main build system.

**Key Improvements:**
- 3-4x faster build times
- Integrated documentation generation (no external dependencies)
- Intelligent dependency tracking and caching
- Better error handling and resilience
- Cross-platform compatibility
- Real-time progress monitoring
- Unified workflow for building and documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `./build.sh --preview`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

