# Legacy Build System Archive

This directory contains the legacy SCons-based build system that was used before the universal build system was implemented.

## Contents

- **`SConstruct`** - Original SCons build script (313 lines)
- **`scons_build.py`** - SCons-compatible build implementation (719 lines)  
- **`scons_types.py`** - Type stubs for SCons functions (27 lines)
- **`builders/`** - SCons builders for different build tasks:
  - `docs_generator.py` - Documentation generation builder
  - `embed_injector.py` - Embed marker injection builder  
  - `godot_export.py` - Godot project export builder
  - `sidebar_generator.py` - Sidebar generation builder
- **`config/`** - SCons configuration modules:
  - `build_config.py` - Build configuration for SCons
  - `targets.py` - Build targets setup for SCons

## Migration Notes

The legacy SCons system was replaced with the universal build system (`build_system/build.py`) on June 20, 2025. The new system provides:

- Better dependency management
- Improved parallel processing
- Enhanced progress reporting
- Cross-platform compatibility
- Simplified configuration

## Usage (Legacy - Not Recommended)

If you need to use the legacy system for debugging purposes:

```bash
# From the build_system/legacy directory
scons                    # Build all targets
scons --preview          # Show what would be built
scons --progress         # Show real-time progress
```

## Note

This legacy system is kept for reference only. Use the modern `build_system/build.py` for all new development and builds.
