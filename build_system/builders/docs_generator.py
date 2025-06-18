#!/usr/bin/env python3
"""
Documentation Generator Builder for SCons
=========================================

Custom SCons builder for generating documentation from Godot projects.
"""

import os
import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def docs_generator_builder(target, source, env):
    """
    SCons builder function for generating documentation from Godot projects
    
    Args:
        target: List of target files (generated docs)
        source: List of source files (Godot project files)
        env: SCons environment
    
    Returns:
        0 for success, 1 for failure
    """
    start_time = time.time()
    
    # Get build parameters
    verbose = env.get('VERBOSE', False)
    docs_template = env.get('DOCS_TEMPLATE', 'docs_template.html')
    
    # Extract paths
    project_dir = Path(str(source[0])).parent
    docs_file = Path(str(target[0]))
    
    # Ensure docs directory exists
    docs_file.parent.mkdir(parents=True, exist_ok=True)
    
    if verbose:
        print(f"📝 Generating docs for: {project_dir.name}")
    
    try:
        # Extract project information
        project_info = extract_project_info(project_dir)
        
        # Generate documentation content
        docs_content = generate_docs_content(project_info, project_dir, env)
        
        # Write documentation file
        with open(docs_file, 'w', encoding='utf-8') as f:
            f.write(docs_content)
        
        duration = time.time() - start_time
        file_size = docs_file.stat().st_size
        
        if verbose:
            print(f"✅ Docs generated: {project_dir.name} ({duration:.2f}s, {file_size} bytes)")
        
        # Report to progress reporter if available
        try:
            from tools.progress_reporter import get_progress_reporter
            reporter = get_progress_reporter()
            reporter.target_completed(f"docs-{project_dir.name}", True, duration, file_size)
        except ImportError:
            pass
        
        return 0
        
    except Exception as e:
        print(f"❌ Documentation generation failed for {project_dir.name}: {str(e)}")
        
        # Report failure to progress reporter
        try:
            from tools.progress_reporter import get_progress_reporter
            reporter = get_progress_reporter()
            reporter.target_completed(f"docs-{project_dir.name}", False, time.time() - start_time)
        except ImportError:
            pass
        
        return 1


def extract_project_info(project_dir: Path) -> Dict:
    """Extract information from a Godot project"""
    info = {
        'name': project_dir.name,
        'path': str(project_dir),
        'description': '',
        'category': '',
        'scripts': [],
        'scenes': [],
        'assets': [],
        'readme': None
    }
    
    # Read project.godot file
    project_file = project_dir / 'project.godot'
    if project_file.exists():
        with open(project_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract project name
        for line in content.split('\n'):
            if line.startswith('config/name='):
                info['name'] = line.split('=', 1)[1].strip('"')
                break
        
        # Extract description from project settings
        for line in content.split('\n'):
            if line.startswith('config/description='):
                info['description'] = line.split('=', 1)[1].strip('"')
                break
    
    # Determine category from path
    path_parts = project_dir.parts
    if '2d' in path_parts:
        info['category'] = '2D'
    elif '3d' in path_parts:
        info['category'] = '3D'
    elif 'gui' in path_parts:
        info['category'] = 'GUI'
    elif 'audio' in path_parts:
        info['category'] = 'Audio'
    elif 'networking' in path_parts:
        info['category'] = 'Networking'
    elif 'mobile' in path_parts:
        info['category'] = 'Mobile'
    else:
        info['category'] = 'Misc'
    
    # Find scripts
    for script_file in project_dir.rglob('*.gd'):
        if not any(part.startswith('.') for part in script_file.parts):
            info['scripts'].append(str(script_file.relative_to(project_dir)))
    
    # Find scenes
    for scene_file in project_dir.rglob('*.tscn'):
        if not any(part.startswith('.') for part in scene_file.parts):
            info['scenes'].append(str(scene_file.relative_to(project_dir)))
    
    # Find assets
    asset_extensions = {'.png', '.jpg', '.jpeg', '.wav', '.ogg', '.mp3', '.ttf', '.tres', '.res'}
    for asset_file in project_dir.rglob('*'):
        if (asset_file.is_file() and 
            asset_file.suffix.lower() in asset_extensions and 
            not any(part.startswith('.') for part in asset_file.parts)):
            info['assets'].append(str(asset_file.relative_to(project_dir)))
    
    # Look for README
    readme_files = ['README.md', 'readme.md', 'README.txt', 'readme.txt']
    for readme_name in readme_files:
        readme_path = project_dir / readme_name
        if readme_path.exists():
            info['readme'] = str(readme_path.relative_to(project_dir))
            break
    
    return info


def generate_docs_content(project_info: Dict, project_dir: Path, env) -> str:
    """Generate HTML documentation content"""
    
    # Basic HTML template
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - Godot Project Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #478cbf; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .category {{ background: #f0f0f0; padding: 5px 10px; border-radius: 4px; font-size: 0.9em; }}
        .section {{ margin: 20px 0; }}
        .file-list {{ background: #f8f8f8; padding: 15px; border-radius: 4px; }}
        .file-list ul {{ margin: 0; padding-left: 20px; }}
        .play-button {{ 
            background: #478cbf; color: white; padding: 10px 20px; 
            border: none; border-radius: 4px; cursor: pointer; 
            font-size: 16px; margin: 10px 0;
        }}
        .play-button:hover {{ background: #3a7ca8; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{name}</h1>
        <span class="category">{category}</span>
        {description_html}
    </div>
    
    <div class="section">
        <h2>🎮 Play Demo</h2>
        <button class="play-button" onclick="playDemo()">Play in Browser</button>
        <p><em>Click to play the exported Godot project</em></p>
    </div>
    
    {readme_html}
    
    <div class="section">
        <h2>📁 Project Structure</h2>
        {structure_html}
    </div>
    
    <div class="section">
        <h2>🔧 Technical Details</h2>
        <p><strong>Project Path:</strong> <code>{path}</code></p>
        <p><strong>Scripts:</strong> {script_count}</p>
        <p><strong>Scenes:</strong> {scene_count}</p>
        <p><strong>Assets:</strong> {asset_count}</p>
    </div>
    
    <script>
        function playDemo() {{
            const demoUrl = '../build/{name}/{name}.html';
            window.open(demoUrl, '_blank');
        }}
    </script>
</body>
</html>"""
    
    # Format description
    description_html = f"<p>{project_info['description']}</p>" if project_info['description'] else ""
    
    # Format README content
    readme_html = ""
    if project_info['readme']:
        readme_path = project_dir / project_info['readme']
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            readme_html = f"""
            <div class="section">
                <h2>📖 README</h2>
                <div class="file-list">
                    <pre>{readme_content}</pre>
                </div>
            </div>"""
    
    # Format project structure
    structure_parts = []
    
    if project_info['scripts']:
        scripts_list = '\n'.join([f"<li>{script}</li>" for script in project_info['scripts'][:10]])
        if len(project_info['scripts']) > 10:
            scripts_list += f"<li><em>... and {len(project_info['scripts']) - 10} more</em></li>"
        structure_parts.append(f"""
        <div class="file-list">
            <h3>🐍 Scripts ({len(project_info['scripts'])})</h3>
            <ul>{scripts_list}</ul>
        </div>""")
    
    if project_info['scenes']:
        scenes_list = '\n'.join([f"<li>{scene}</li>" for scene in project_info['scenes'][:10]])
        if len(project_info['scenes']) > 10:
            scenes_list += f"<li><em>... and {len(project_info['scenes']) - 10} more</em></li>"
        structure_parts.append(f"""
        <div class="file-list">
            <h3>🎬 Scenes ({len(project_info['scenes'])})</h3>
            <ul>{scenes_list}</ul>
        </div>""")
    
    if project_info['assets']:
        assets_list = '\n'.join([f"<li>{asset}</li>" for asset in project_info['assets'][:10]])
        if len(project_info['assets']) > 10:
            assets_list += f"<li><em>... and {len(project_info['assets']) - 10} more</em></li>"
        structure_parts.append(f"""
        <div class="file-list">
            <h3>🎨 Assets ({len(project_info['assets'])})</h3>
            <ul>{assets_list}</ul>
        </div>""")
    
    structure_html = '\n'.join(structure_parts)
    
    # Fill template
    return html_template.format(
        name=project_info['name'],
        category=project_info['category'],
        description_html=description_html,
        readme_html=readme_html,
        structure_html=structure_html,
        path=project_info['path'],
        script_count=len(project_info['scripts']),
        scene_count=len(project_info['scenes']),
        asset_count=len(project_info['assets'])
    )


def docs_generator_emitter(target, source, env):
    """
    SCons emitter function to determine target files for docs generation
    """
    # Get project directory
    project_file = source[0]
    project_dir = Path(str(project_file)).parent
    project_name = project_dir.name
    
    # Determine docs directory
    docs_dir = Path(env.get('DOCS_DIR', 'docs'))
    
    # Create docs target
    docs_target = docs_dir / f"{project_name}.html"
    
    return [str(docs_target)], source


def create_docs_builder():
    """Create the documentation generator builder for SCons"""
    from SCons.Builder import Builder
    
    return Builder(
        action=docs_generator_builder,
        emitter=docs_generator_emitter,
        suffix='.html',
        src_suffix='.godot'
    )


def add_docs_builder(env):
    """Add the documentation generator builder to a SCons environment"""
    env['BUILDERS']['GenerateDocs'] = create_docs_builder()
    
    # Set default values
    env.SetDefault(
        DOCS_DIR='docs',
        DOCS_TEMPLATE='docs_template.html'
    )
