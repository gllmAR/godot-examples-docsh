#!/usr/bin/env python3
"""
Embed Injector Builder for SCons
================================

Custom SCons builder for injecting game embeds into documentation pages.
"""

import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def embed_injector_builder(target, source, env):
    """
    SCons builder function for injecting game embeds into documentation
    
    Args:
        target: List of target files (updated docs with embeds)
        source: List of source files (original docs and game files)
        env: SCons environment
    
    Returns:
        0 for success, 1 for failure
    """
    start_time = time.time()
    
    # Get build parameters
    verbose = env.get('VERBOSE', False)
    embed_width = env.get('EMBED_WIDTH', '800')
    embed_height = env.get('EMBED_HEIGHT', '600')
    
    # Extract paths
    docs_file = Path(str(source[0]))  # Original docs file
    game_file = Path(str(source[1]))  # Game HTML file
    target_file = Path(str(target[0]))  # Updated docs file
    
    if verbose:
        print(f"🔗 Injecting embed for: {docs_file.stem}")
    
    try:
        # Read original documentation
        with open(docs_file, 'r', encoding='utf-8') as f:
            docs_content = f.read()
        
        # Generate embed HTML
        embed_html = generate_embed_html(game_file, embed_width, embed_height, env)
        
        # Inject embed into documentation
        updated_content = inject_embed(docs_content, embed_html, docs_file.stem)
        
        # Write updated documentation
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        duration = time.time() - start_time
        file_size = target_file.stat().st_size
        
        if verbose:
            print(f"✅ Embed injected: {docs_file.stem} ({duration:.2f}s, {file_size} bytes)")
        
        # Report to progress reporter if available
        try:
            from tools.progress_reporter import get_progress_reporter
            reporter = get_progress_reporter()
            reporter.target_completed(f"embed-{docs_file.stem}", True, duration, file_size)
        except ImportError:
            pass
        
        return 0
        
    except Exception as e:
        print(f"❌ Embed injection failed for {docs_file.stem}: {str(e)}")
        
        # Report failure to progress reporter
        try:
            from tools.progress_reporter import get_progress_reporter
            reporter = get_progress_reporter()
            reporter.target_completed(f"embed-{docs_file.stem}", False, time.time() - start_time)
        except ImportError:
            pass
        
        return 1


def generate_embed_html(game_file: Path, width: str, height: str, env) -> str:
    """Generate HTML embed code for a Godot game"""
    
    # Get relative path from docs to game exports
    # For GitHub Pages, we need the path relative to the site root
    # game_file is like: /path/to/godot-demo-projects/2d/bullet_shower/exports/web/index.html
    # We want: godot-demo-projects/2d/bullet_shower/exports/web/index.html
    
    # Extract the project path from the game_file
    parts = game_file.parts
    try:
        # Find the godot-demo-projects part
        godot_idx = parts.index('godot-demo-projects')
        # Build path from godot-demo-projects onwards
        game_url = '/'.join(parts[godot_idx:])
    except ValueError:
        # Fallback to relative path
        game_url = f"../exports/{game_file.parent.name}/{game_file.name}"
    
    # Generate responsive embed HTML
    embed_html = f"""
    <div class="game-embed">
        <div class="embed-container" style="position: relative; width: 100%; max-width: {width}px; margin: 20px auto;">
            <iframe 
                src="{game_url}" 
                width="{width}" 
                height="{height}"
                frameborder="0"
                allowfullscreen
                style="width: 100%; height: {height}px; border: 2px solid #478cbf; border-radius: 8px;">
            </iframe>
            <div class="embed-controls" style="text-align: center; margin-top: 10px;">
                <button onclick="toggleFullscreen()" class="control-btn">⛶ Fullscreen</button>
                <button onclick="reloadGame()" class="control-btn">🔄 Reload</button>
                <a href="{game_url}" target="_blank" class="control-btn">🔗 Open in New Tab</a>
            </div>
        </div>
    </div>
    
    <style>
        .game-embed {{
            margin: 20px 0;
            text-align: center;
        }}
        .embed-container {{
            background: #f0f0f0;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .control-btn {{
            background: #478cbf;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 0 5px;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
        }}
        .control-btn:hover {{
            background: #3a7ca8;
        }}
        @media (max-width: 768px) {{
            .embed-container {{
                padding: 10px;
            }}
            .embed-container iframe {{
                height: 400px;
            }}
        }}
    </style>
    
    <script>
        function toggleFullscreen() {{
            const iframe = document.querySelector('.game-embed iframe');
            if (iframe.requestFullscreen) {{
                iframe.requestFullscreen();
            }} else if (iframe.webkitRequestFullscreen) {{
                iframe.webkitRequestFullscreen();
            }} else if (iframe.msRequestFullscreen) {{
                iframe.msRequestFullscreen();
            }}
        }}
        
        function reloadGame() {{
            const iframe = document.querySelector('.game-embed iframe');
            iframe.src = iframe.src;
        }}
    </script>
    """
    
    return embed_html


def inject_embed(docs_content: str, embed_html: str, project_name: str) -> str:
    """Inject embed HTML into documentation content"""
    
    # Look for existing play button and replace it
    play_button_pattern = r'<div class="section">\s*<h2>🎮 Play Demo</h2>.*?</div>'
    
    if re.search(play_button_pattern, docs_content, re.DOTALL):
        # Replace existing play section with embed
        new_play_section = f"""
        <div class="section">
            <h2>🎮 Play Demo</h2>
            <p>Play the game directly in your browser:</p>
            {embed_html}
        </div>"""
        
        updated_content = re.sub(
            play_button_pattern, 
            new_play_section, 
            docs_content, 
            flags=re.DOTALL
        )
    else:
        # Insert embed after header
        header_end = docs_content.find('</div>', docs_content.find('class="header"'))
        if header_end != -1:
            header_end += 6  # Length of '</div>'
            
            embed_section = f"""
            
            <div class="section">
                <h2>🎮 Play Demo</h2>
                <p>Play the game directly in your browser:</p>
                {embed_html}
            </div>"""
            
            updated_content = (
                docs_content[:header_end] + 
                embed_section + 
                docs_content[header_end:]
            )
        else:
            # Fallback: append to end of body
            body_end = docs_content.rfind('</body>')
            if body_end != -1:
                embed_section = f"""
                <div class="section">
                    <h2>🎮 Play Demo</h2>
                    <p>Play the game directly in your browser:</p>
                    {embed_html}
                </div>
                """
                updated_content = (
                    docs_content[:body_end] + 
                    embed_section + 
                    docs_content[body_end:]
                )
            else:
                updated_content = docs_content + embed_html
    
    return updated_content


def embed_injector_emitter(target, source, env):
    """
    SCons emitter function to determine target files for embed injection
    """
    # Get docs file path
    docs_file = Path(str(source[0]))
    
    # Create target in final docs directory
    final_docs_dir = Path(env.get('FINAL_DOCS_DIR', 'final_docs'))
    target_file = final_docs_dir / docs_file.name
    
    return [str(target_file)], source


def create_embed_injector_builder():
    """Create the embed injector builder for SCons"""
    from SCons.Builder import Builder
    
    return Builder(
        action=embed_injector_builder,
        emitter=embed_injector_emitter,
        suffix='.html',
        src_suffix='.html'
    )


def add_embed_injector_builder(env):
    """Add the embed injector builder to a SCons environment"""
    env['BUILDERS']['InjectEmbed'] = create_embed_injector_builder()
    
    # Set default values
    env.SetDefault(
        FINAL_DOCS_DIR='final_docs',
        EMBED_WIDTH='800',
        EMBED_HEIGHT='600'
    )


def create_embed_targets(env, docs_targets: List, game_targets: List) -> List:
    """Create SCons targets for embed injection"""
    embed_targets = []
    
    # Create a mapping of project names to game files
    game_map = {}
    for game_target in game_targets:
        game_path = Path(str(game_target))
        project_name = game_path.parent.name
        if game_path.name.endswith('.html'):
            game_map[project_name] = game_target
    
    # Create embed targets for each docs file
    for docs_target in docs_targets:
        docs_path = Path(str(docs_target))
        project_name = docs_path.stem
        
        if project_name in game_map:
            # Create embed injection target
            embed_target = env.InjectEmbed(
                source=[docs_target, game_map[project_name]]
            )
            embed_targets.extend(embed_target)
    
    return embed_targets


def main():
    """Command-line interface for embed injection"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Inject game embeds into README.md files')
    parser.add_argument('--projects-dir', default='godot-demo-projects',
                       help='Directory containing Godot projects')
    parser.add_argument('--output-dir', default='docs/generated',
                       help='Output directory for processed documentation')
    parser.add_argument('--in-place', action='store_true',
                       help='Update README.md files in place instead of creating new files')
    parser.add_argument('--subset', 
                       help='Only process projects matching this subset pattern')
    parser.add_argument('--width', default='800',
                       help='Embed width in pixels')
    parser.add_argument('--height', default='600',
                       help='Embed height in pixels')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    projects_dir = Path(args.projects_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not projects_dir.exists():
        print(f"❌ Projects directory not found: {projects_dir}")
        sys.exit(1)
    
    # Find all README.md files in Godot projects
    readme_files = []
    for readme_path in projects_dir.rglob('README.md'):
        # Check if this is a Godot project (has project.godot)
        project_dir = readme_path.parent
        if (project_dir / 'project.godot').exists():
            # Check subset filter
            if args.subset:
                category = project_dir.parts[-2] if len(project_dir.parts) > 1 else 'misc'
                if args.subset not in category and args.subset != 'all':
                    continue
            readme_files.append(readme_path)
    
    if args.verbose:
        print(f"📝 Found {len(readme_files)} README.md files to process")
    
    processed = 0
    for readme_path in readme_files:
        project_dir = readme_path.parent
        project_name = project_dir.name
        
        # Look for exported game
        exports_dir = project_dir / 'exports' / 'web'
        game_file = exports_dir / 'index.html'
        
        if not game_file.exists():
            if args.verbose:
                print(f"⏭️  Skipping {project_name}: no web export found")
            continue
        
        try:
            # Read original README
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            # Generate embed HTML
            embed_html = generate_embed_html(game_file, args.width, args.height, {})
            
            # Generate project path for marker
            project_path = str(project_dir.relative_to(projects_dir))
            embed_marker = f"<!-- embed-{{{project_path}}} -->"
            
            # Inject embed (for Markdown, we'll add the marker and HTML)
            if embed_marker in readme_content:
                # Replace existing embed marker with actual embed
                updated_content = readme_content.replace(embed_marker, embed_html)
            elif '<!-- embed-{$PATH}' in readme_content:
                # Replace $PATH placeholder with actual embed
                updated_content = readme_content.replace('<!-- embed-{$PATH} -->', embed_html)
            elif '<!-- embed-{' in readme_content:
                # Replace any existing embed marker with actual embed
                import re
                embed_pattern = r'<!-- embed-\{[^}]+\} -->'
                updated_content = re.sub(embed_pattern, embed_html, readme_content)
            elif '<!-- AUTO-GENERATED EMBED MARKER' in readme_content:
                # Replace the auto-generated marker section
                import re
                auto_pattern = r'<!-- AUTO-GENERATED EMBED MARKER[^>]*-->.*?<!-- END AUTO-GENERATED EMBED MARKER -->'
                updated_content = re.sub(auto_pattern, embed_html, readme_content, flags=re.DOTALL)
            else:
                # Add embed marker after first heading
                lines = readme_content.split('\n')
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith('# '):
                        insert_idx = i + 1
                        # Skip empty lines after title
                        while insert_idx < len(lines) and lines[insert_idx].strip() == '':
                            insert_idx += 1
                        break
                
                # Insert the embed marker
                lines.insert(insert_idx, f"\n{embed_marker}\n")
                updated_content = '\n'.join(lines)
            
            # Write to output directory or update in place
            if args.in_place:
                # Update the original README file
                output_file = readme_path
            else:
                # Write to output directory
                output_file = output_dir / f"{project_name}_README.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            processed += 1
            if args.verbose:
                print(f"✅ Processed {project_name}")
                
        except Exception as e:
            print(f"❌ Failed to process {project_name}: {e}")
    
    print(f"🎯 Processed {processed}/{len(readme_files)} README files")


def add_embed_markers():
    """Command-line interface for adding embed markers to README.md files"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Add embed markers to README.md files')
    parser.add_argument('--projects-dir', default='godot-demo-projects',
                       help='Directory containing Godot projects')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without making changes')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    projects_dir = Path(args.projects_dir)
    
    if not projects_dir.exists():
        print(f"❌ Projects directory not found: {projects_dir}")
        sys.exit(1)
    
    # Find all README.md files in Godot projects
    readme_files = []
    for readme_path in projects_dir.rglob('README.md'):
        # Check if this is a Godot project (has project.godot)
        project_dir = readme_path.parent
        if (project_dir / 'project.godot').exists():
            readme_files.append(readme_path)
    
    if args.verbose:
        print(f"📝 Found {len(readme_files)} README.md files to process")
    
    processed = 0
    for readme_path in readme_files:
        project_dir = readme_path.parent
        project_name = project_dir.name
        
        try:
            # Read original README
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            # Generate project path for marker
            project_path = str(project_dir.relative_to(projects_dir))
            embed_marker = f"<!-- embed-{{{project_path}}} -->"
            
            # Check if marker already exists (check for various formats)
            if (embed_marker in readme_content or 
                '<!-- embed-{' in readme_content or
                '<!-- AUTO-GENERATED EMBED MARKER' in readme_content):
                if args.verbose:
                    print(f"⏭️  Skipping {project_name}: embed marker already exists")
                continue
            
            # Add embed marker after first heading
            lines = readme_content.split('\n')
            insert_idx = 0
            title_found = False
            
            for i, line in enumerate(lines):
                if line.startswith('# '):
                    insert_idx = i + 1
                    title_found = True
                    # Skip empty lines after title
                    while insert_idx < len(lines) and lines[insert_idx].strip() == '':
                        insert_idx += 1
                    break
            
            if not title_found:
                if args.verbose:
                    print(f"⚠️  Skipping {project_name}: no title found")
                continue
            
            # Insert the embed marker
            lines.insert(insert_idx, f"\n{embed_marker}\n")
            updated_content = '\n'.join(lines)
            
            if args.dry_run:
                print(f"🔍 Would add marker to {project_name}: {embed_marker}")
            else:
                # Write updated README
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                processed += 1
                if args.verbose:
                    print(f"✅ Added marker to {project_name}")
                    
        except Exception as e:
            print(f"❌ Failed to process {project_name}: {e}")
    
    if args.dry_run:
        print(f"🔍 Would add markers to {len([r for r in readme_files if not ('<!-- embed-{' in open(r).read())])} README files")
    else:
        print(f"🎯 Added markers to {processed}/{len(readme_files)} README files")


if __name__ == '__main__':
    import sys
    
    # Check if we're being called to add markers
    if len(sys.argv) > 1 and sys.argv[1] == 'add-markers':
        # Remove the 'add-markers' argument and call the marker function
        sys.argv.pop(1)
        add_embed_markers()
    else:
        main()
