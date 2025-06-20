"""
Build Targets Setup for SCons Build System
"""

import os
import glob
from pathlib import Path


def setup_build_targets(env, dependency_scanner, progress_reporter):
    """Setup all build targets and their dependencies"""
    
    projects_dir = env.get('PROJECTS_DIR', '../godot-demo-projects')
    godot_binary = env.get('GODOT_BINARY', 'godot')
    
    # Find all Godot projects
    godot_projects = []
    export_targets = []
    
    if os.path.exists(projects_dir):
        # Find all project.godot files
        project_files = []
        for root, dirs, files in os.walk(projects_dir):
            if 'project.godot' in files:
                project_files.append(os.path.join(root, 'project.godot'))
        
        print(f"📋 Found {len(project_files)} Godot projects")
        
        # Create export targets for each project
        for project_file in project_files:
            project_dir = os.path.dirname(project_file)
            export_dir = os.path.join(project_dir, 'exports', 'web')
            export_target = os.path.join(export_dir, 'index.html')
            
            # Create export preset if needed
            preset_file = os.path.join(project_dir, 'export_presets.cfg')
            if not os.path.exists(preset_file):
                preset_target = env.Command(
                    target=preset_file,
                    source=project_file,
                    action=create_export_preset_action
                )
            
            # Create export target
            exported = env.Command(
                target=export_target,
                source=[project_file, preset_file] if os.path.exists(preset_file) else project_file,
                action=f'mkdir -p {export_dir} && cd {project_dir} && {godot_binary} --headless --export-release web {export_target}'
            )
            
            export_targets.append(exported)
            
            # Add dependencies on all files in the project
            project_files_glob = glob.glob(os.path.join(project_dir, '**/*'), recursive=True)
            project_sources = [f for f in project_files_glob if os.path.isfile(f) and not f.endswith('.tmp')]
            
            # Make export depend on all project files
            env.Depends(exported, project_sources[:10])  # Limit for performance
    
    # Create documentation targets
    sidebar_target = env.Command(
        target='../_sidebar.md',
        source=export_targets,
        action='cd .. && ./docsh/10_generate_sidebar.sh'
    )
    
    embed_targets = env.Command(
        target='../embed_complete.marker',
        source=export_targets,
        action='cd .. && ./docsh/20_inject_embeds.sh && touch embed_complete.marker'
    )
    
    # Create aliases
    env.Alias('godot', export_targets)
    env.Alias('docs', sidebar_target) 
    env.Alias('embeds', embed_targets)
    env.Alias('all', [export_targets, sidebar_target, embed_targets])
    
    # Test target
    test_target = env.Command(
        target='test_complete.marker',
        source=[],
        action='cd .. && ./docsh/quick_test_parallel.sh && touch build_system/test_complete.marker'
    )
    env.Alias('test', test_target)
    
    # Serve target
    serve_target = env.Command(
        target='serve_started.marker',
        source='all',
        action='cd .. && python3 -m http.server 8000 & echo $! > build_system/serve.pid && touch build_system/serve_started.marker'
    )
    env.Alias('serve', serve_target)


def create_export_preset_action(target, source, env):
    """Create web export preset for a project"""
    preset_content = """[preset.0]

name="web"
platform="Web"
runnable=true
advanced_options=false
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="exports/web/index.html"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.0.options]

custom_template/debug=""
custom_template/release=""
variant/extensions_support=false
vram_texture_compression/for_desktop=true
vram_texture_compression/for_mobile=false
html/export_icon=true
html/custom_html_shell=""
html/head_include=""
html/canvas_resize_policy=2
html/focus_canvas_on_start=true
html/experimental_virtual_keyboard=false
progressive_web_app/enabled=false
progressive_web_app/offline_page=""
progressive_web_app/display=1
progressive_web_app/orientation=0
progressive_web_app/icon_144x144=""
progressive_web_app/icon_180x180=""
progressive_web_app/icon_512x512=""
progressive_web_app/background_color=Color(0, 0, 0, 1)
"""
    
    with open(str(target[0]), 'w') as f:
        f.write(preset_content)
    
    print(f"✅ Created export preset: {target[0]}")
    return 0
