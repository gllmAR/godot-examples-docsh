# Build System Troubleshooting Guide

## 🔧 Common Issues and Solutions

### Git Change Detection Errors

#### Error: `fatal: ambiguous argument 'HEAD~1': unknown revision or path not in the working tree`

**Cause**: Fresh repository without enough commit history.

**Solutions**:
```bash
# Option 1: Force rebuild (bypasses change detection)
python build_system/build.py build --force-rebuild

# Option 2: Use different base reference
python build_system/build.py build --base-ref HEAD

# Option 3: Create an initial commit if repository is empty
git add .
git commit -m "Initial commit"
```

**Automatic Handling**: The system now automatically detects this and falls back to first commit or force rebuild.

### Godot Export Errors

#### Error: `Export failed (code -6): terminate called after throwing an instance of 'std::system_error' what(): Invalid argument`

**Cause**: System resource exhaustion or environment issues.

**Solutions**:
```bash
# Reduce parallel jobs to lower system load
python build_system/build.py build --jobs 2

# Use maximum single-threaded for stability
python build_system/build.py build --jobs 1

# For CI/headless environments, ensure proper display setup
export DISPLAY=:0
export GODOT_DISABLE_CRASH_HANDLER=1
```

**Automatic Handling**: The system now includes retry logic with progressive delays and fallback exports.

#### Error: `Export failed (code -9): Process killed`

**Cause**: Out of memory or process timeout.

**Solutions**:
```bash
# Check available memory
python -c "import psutil; print(f'Available RAM: {psutil.virtual_memory().available / 1024**3:.1f}GB')"

# Reduce memory pressure
python build_system/build.py build --jobs 1

# Increase system virtual memory if possible
# Or close other applications
```

#### Error: `Export template not found`

**Cause**: Missing Godot export templates.

**Solutions**:
```bash
# Set up Godot environment with templates
python build_system/build.py setup --godot-version 4.5-beta1

# Verify environment
python build_system/build.py verify

# Manual template installation (if needed)
godot --headless --install-export-templates
```

### Performance Issues

#### Slow Builds Despite Multiple Cores

**Diagnostic**:
```bash
# Check current job allocation
python -c "
from build_system.tools.parallel_manager import ParallelManager
pm = ParallelManager()
print(f'CPU: {pm.cpu_count}, Memory: {pm.available_memory:.1f}GB')
print(f'Optimal jobs: {pm.get_optimal_job_count()}')
print(f'Adaptive jobs (121 projects): {pm.get_adaptive_job_count(121)}')
"
```

**Solutions**:
```bash
# Force maximum parallelism
python build_system/build.py build --jobs 0

# Override environment detection
MAX_PARALLEL_JOBS=8 python build_system/build.py build

# For CI environments
export CI=true
python build_system/build.py build
```

#### Memory Exhaustion During Large Builds

**Symptoms**:
- Process killed (-9)
- System becomes unresponsive
- "Cannot allocate memory" errors

**Solutions**:
```bash
# Progressive reduction
python build_system/build.py build --jobs 4  # Try 4 first
python build_system/build.py build --jobs 2  # Then 2
python build_system/build.py build --jobs 1  # Finally 1

# Monitor memory usage during build
watch -n 1 'free -h && ps aux | grep godot | head -5'
```

### Environment Issues

#### Headless/CI Environment Problems

**Common Issues**:
- Missing DISPLAY variable
- X11 errors
- Permission denied

**Solutions**:
```bash
# Set up virtual display
export DISPLAY=:0
Xvfb :0 -screen 0 1024x768x24 &

# Alternative: Use headless-friendly settings
export GODOT_DISABLE_CRASH_HANDLER=1
export GODOT_HEADLESS=1

# Check permissions
chmod +x /path/to/godot
```

#### Permission Errors

**Symptoms**:
- "Permission denied" when accessing files
- "Cannot create directory" errors

**Solutions**:
```bash
# Fix file permissions
find . -name "*.gd" -type f -exec chmod 644 {} \;
find . -name "project.godot" -type f -exec chmod 644 {} \;

# Fix directory permissions
find . -type d -exec chmod 755 {} \;

# Check ownership
ls -la godot-demo-projects/
```

## 🚨 Emergency Recovery

### Complete Build Failure

If all builds are failing:

```bash
# 1. Clean everything
python build_system/build.py clean

# 2. Verify environment
python build_system/build.py verify

# 3. Force rebuild with minimal parallelism
python build_system/build.py build --force-rebuild --jobs 1 --verbose

# 4. If that fails, try individual project
cd godot-demo-projects/2d/pong
godot --headless --export-release "Web" exports/web/index.html
```

### Corrupted Cache

```bash
# Clear all caches
rm -rf build_system/cache/
rm -rf build_system/.build_cache/

# Reset git if needed
git clean -fd
git reset --hard HEAD
```

## 📊 Diagnostic Commands

### System Resources
```bash
# Check CPU and memory
python -c "
import multiprocessing, psutil
print(f'CPUs: {multiprocessing.cpu_count()}')
print(f'Memory: {psutil.virtual_memory().total / 1024**3:.1f}GB total')
print(f'Available: {psutil.virtual_memory().available / 1024**3:.1f}GB')
print(f'CPU Load: {psutil.cpu_percent()}%')
"
```

### Godot Environment
```bash
# Check Godot version and capabilities
godot --version
godot --help | grep export

# Check export templates
ls ~/.local/share/godot/export_templates/
```

### Build System Status
```bash
# Quick system check
python build_system/build.py --help
python build_system/build.py verify
python build_system/build.py --preview
```

## 📈 Performance Tuning

### For Different Environments

**Local Development (Laptop/Desktop)**:
```bash
python build_system/build.py build --jobs 2
```

**High-End Workstation (16GB+ RAM, 8+ cores)**:
```bash
python build_system/build.py build --jobs 0  # Use all cores
```

**CI/CD Pipeline**:
```bash
export CI=true
python build_system/build.py final --jobs 0 --verbose
```

**Resource-Constrained (VPS, Docker)**:
```bash
python build_system/build.py build --jobs 1
```

**Memory-Limited (<8GB RAM)**:
```bash
MAX_PARALLEL_JOBS=1 python build_system/build.py build
```

This guide covers the most common issues and their solutions. The build system now includes automatic handling for many of these problems!
