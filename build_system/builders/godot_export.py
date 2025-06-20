#!/usr/bin/env python3
"""
Godot Project Export Builder for SCons
=====================================

Custom SCons builder for exporting Godot projects to web format.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def validate_export_templates(godot_binary='godot', verbose=False):
    """
    Validate that Godot can find export templates
    
    Args:
        godot_binary: Path to Godot executable
        verbose: Enable verbose output
    
    Returns:
        bool: True if templates are valid, False otherwise
    """
    try:
        # Test if Godot can list export templates
        result = subprocess.run(
            [godot_binary, '--headless', '--quit', '--list-export-templates'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if verbose:
            print(f"🔍 Template validation output:")
            print(f"   Return code: {result.returncode}")
            if result.stdout:
                print(f"   Stdout: {result.stdout}")
            if result.stderr:
                print(f"   Stderr: {result.stderr}")
        
        # Look for Web export in the output
        if result.stdout and 'Web' in result.stdout:
            if verbose:
                print("✅ Web export templates found and available")
            return True
        elif verbose:
            print("⚠️ Web export templates not found in template list")
            
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        if verbose:
            print(f"❌ Template validation failed: {e}")
    
    return False


def godot_export_builder(target, source, env):
    """
    SCons builder function for exporting Godot projects
    
    Args:
        target: List of target files (exported game files)
        source: List of source files (project.godot file)
        env: SCons environment
    
    Returns:
        0 for success, 1 for failure
    """
    start_time = time.time()
    
    # Get build parameters
    godot_binary = env.get('GODOT_BINARY', 'godot')
    export_preset = env.get('EXPORT_PRESET', 'Web')
    verbose = env.get('VERBOSE', False)
    
    # Extract paths
    project_file = str(source[0])
    export_file = str(target[0])
    project_dir = Path(project_file).parent
    export_path = Path(export_file)
    
    # Ensure export directory exists
    export_path.parent.mkdir(parents=True, exist_ok=True)
    
    if verbose:
        print(f"🔄 Exporting Godot project: {project_dir.name}")
        print(f"   Source: {project_file}")
        print(f"   Target: {export_file}")
    
    # Validate export templates before attempting export
    if not validate_export_templates(godot_binary, verbose):
        print(f"❌ Export templates validation failed for {project_dir.name}")
        print("   Make sure Godot export templates are properly installed")
        return 1
    
    try:
        # Build Godot export command
        cmd = [
            godot_binary,
            '--headless',
            '--path', str(project_dir),
            '--export-release', export_preset, str(export_path)
        ]
        
        if verbose:
            print(f"   Command: {' '.join(cmd)}")
        
        # Execute Godot export
        result = subprocess.run(
            cmd,
            capture_output=not verbose,
            text=True,
            timeout=300  # 5 minute timeout per project
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            # Check if output file was created
            if export_path.exists():
                file_size = export_path.stat().st_size
                if verbose:
                    print(f"✅ Export successful: {project_dir.name} ({duration:.2f}s, {file_size} bytes)")
                
                # Report to progress reporter if available
                try:
                    from tools.progress_reporter import get_progress_reporter
                    reporter = get_progress_reporter()
                    reporter.target_completed(project_dir.name, True, duration, file_size)
                except ImportError:
                    pass
                
                return 0
            else:
                print(f"❌ Export failed: Output file not created for {project_dir.name}")
                return 1
        else:
            print(f"❌ Godot export failed for {project_dir.name}")
            if verbose and result.stderr:
                print(f"   Error: {result.stderr}")
            
            # Report failure to progress reporter
            try:
                from tools.progress_reporter import get_progress_reporter
                reporter = get_progress_reporter()
                reporter.target_completed(project_dir.name, False, duration)
            except ImportError:
                pass
            
            return 1
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout: Godot export exceeded 5 minutes for {project_dir.name}")
        return 1
    except Exception as e:
        print(f"💥 Exception during export of {project_dir.name}: {str(e)}")
        return 1


def godot_export_emitter(target, source, env):
    """
    SCons emitter function to determine target files for Godot export
    
    Args:
        target: Initial target list
        source: Source files (project.godot)
        env: SCons environment
    
    Returns:
        Tuple of (targets, sources) with updated file lists
    """
    # Get project directory
    project_file = source[0]
    project_dir = Path(str(project_file)).parent
    project_name = project_dir.name
    
    # Determine export directory
    export_preset = env.get('EXPORT_PRESET', 'Web')
    build_dir = Path(env.get('BUILD_DIR', 'build'))
    
    if export_preset.lower() == 'web':
        # Web export produces multiple files
        export_dir = build_dir / project_name
        targets = [
            export_dir / f"{project_name}.html",
            export_dir / f"{project_name}.js",
            export_dir / f"{project_name}.wasm",
            export_dir / f"{project_name}.pck"
        ]
    else:
        # Other platforms typically produce a single executable
        if export_preset.lower() == 'linux':
            target_file = build_dir / project_name / f"{project_name}.x86_64"
        elif export_preset.lower() == 'windows':
            target_file = build_dir / project_name / f"{project_name}.exe"
        elif export_preset.lower() == 'macos':
            target_file = build_dir / project_name / f"{project_name}.app"
        else:
            target_file = build_dir / project_name / project_name
        
        targets = [target_file]
    
    # Convert to strings for SCons
    target_strings = [str(t) for t in targets]
    
    return target_strings, source


# SCons Builder configuration
def create_godot_builder():
    """Create the Godot export builder for SCons"""
    from SCons.Builder import Builder
    
    return Builder(
        action=godot_export_builder,
        emitter=godot_export_emitter,
        suffix='.html',  # Default suffix for web builds
        src_suffix='.godot'
    )


def add_godot_builder(env):
    """Add the Godot export builder to a SCons environment"""
    env['BUILDERS']['GodotExport'] = create_godot_builder()
    
    # Set default values
    env.SetDefault(
        GODOT_BINARY='godot',
        EXPORT_PRESET='Web',
        BUILD_DIR='build'
    )


# Additional helper functions for batch operations
def find_godot_projects(root_dir: Path) -> List[Path]:
    """Find all Godot projects in a directory tree"""
    projects = []
    
    for project_file in root_dir.rglob('project.godot'):
        # Skip certain directories
        project_dir = project_file.parent
        skip_dirs = {'.git', 'build', 'export', '.godot', '.import'}
        
        if not any(skip in project_dir.parts for skip in skip_dirs):
            projects.append(project_file)
    
    return sorted(projects)


def create_export_targets(env, projects_dir: str, build_dir: Optional[str] = None) -> List:
    """Create SCons targets for all Godot projects in a directory"""
    projects_path = Path(projects_dir)
    
    if not projects_path.exists():
        print(f"⚠️  Projects directory not found: {projects_dir}")
        return []
    
    # Find all Godot projects
    project_files = find_godot_projects(projects_path)
    
    if not project_files:
        print(f"⚠️  No Godot projects found in: {projects_dir}")
        return []
    
    print(f"📁 Found {len(project_files)} Godot projects")
    
    # Create SCons targets
    targets = []
    for project_file in project_files:
        # Export directly to each project's exports/web/ directory
        project_dir = project_file.parent
        export_dir = project_dir / 'exports' / 'web'
        export_target = export_dir / 'index.html'
        
        # Create the export target
        target = env.GodotExport(
            target=str(export_target),
            source=str(project_file)
        )
        targets.extend(target)
    
    return targets
