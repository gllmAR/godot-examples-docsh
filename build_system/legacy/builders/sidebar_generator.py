#!/usr/bin/env python3
"""
Sidebar Generator for Godot Examples Documentation
==================================================

Generates navigation sidebar for the documentation website by scanning
project directories and README files.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional


class SidebarGenerator:
    """Generates navigation sidebar for documentation"""
    
    def __init__(self, projects_dir: Path, output_file: Optional[Path] = None, base_url: str = "/godot-demo-projects", verbose: bool = False):
        self.projects_dir = Path(projects_dir)
        self.output_file = output_file or Path("_sidebar.md")
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.excluded_dirs = {".git", "node_modules", "__pycache__", ".vscode", "docsh", "exports", "screenshots"}
    
    def log(self, message: str) -> None:
        """Print message if verbose mode is enabled"""
        if self.verbose:
            print(message)
        
    def extract_title_from_readme(self, readme_path: Path) -> str:
        """Extract the title from a README.md file"""
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('# '):
                        return line[2:].strip()
            # Fallback to directory name if no title found
            return readme_path.parent.name.replace('_', ' ').title()
        except Exception as e:
            self.log(f"Warning: Could not read {readme_path}: {e}")
            return readme_path.parent.name.replace('_', ' ').title()
    
    def should_exclude_directory(self, dir_path: Path) -> bool:
        """Check if a directory should be excluded from sidebar generation"""
        return dir_path.name in self.excluded_dirs
    
    def generate_sidebar_content(self, directory: Path, indent: str = "", base_path: str = "") -> List[str]:
        """Recursively generate sidebar content for a directory"""
        lines = []
        
        # Check for README.md in current directory
        readme_path = directory / "README.md"
        if readme_path.exists():
            title = self.extract_title_from_readme(readme_path)
            
            # Generate the relative path for the link
            if base_path:
                link_path = f"{self.base_url}/{base_path}/"
            else:
                # For root directory
                rel_path = directory.relative_to(self.projects_dir.parent)
                link_path = f"/{rel_path}/"
            
            # Add the sidebar entry
            lines.append(f"{indent}* [{title}]({link_path})")
            self.log(f"Added: {link_path} with title '{title}'")
        else:
            self.log(f"Skipped directory (no README.md): {directory}")
            return lines
        
        # Recursively process subdirectories
        try:
            subdirectories = sorted([d for d in directory.iterdir() 
                                   if d.is_dir() and not self.should_exclude_directory(d)])
            
            for subdir in subdirectories:
                sub_base_path = f"{base_path}/{subdir.name}" if base_path else subdir.name
                sub_indent = "  " + indent
                sub_lines = self.generate_sidebar_content(subdir, sub_indent, sub_base_path)
                lines.extend(sub_lines)
                
        except PermissionError as e:
            self.log(f"Permission denied accessing {directory}: {e}")
        
        return lines
    
    def generate_sidebar(self, include_build_system: bool = True) -> str:
        """Generate the complete sidebar content"""
        lines = []
        
        # Add build system documentation if requested
        if include_build_system:
            build_system_dir = self.projects_dir.parent / "build_system"
            if (build_system_dir / "README.md").exists():
                title = self.extract_title_from_readme(build_system_dir / "README.md")
                lines.append(f"* [{title}]({self.base_url}/build_system/)")
                self.log(f"Added: {self.base_url}/build_system/ with title '{title}'")
        
        # Process the main projects directory
        if self.projects_dir.exists():
            project_lines = self.generate_sidebar_content(self.projects_dir)
            lines.extend(project_lines)
        else:
            self.log(f"Warning: Projects directory {self.projects_dir} does not exist")
        
        return '\n'.join(lines) + '\n'
    
    def write_sidebar(self, content: str) -> None:
        """Write sidebar content to file"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.log(f"✅ Sidebar written to: {self.output_file}")
        except Exception as e:
            self.log(f"❌ Error writing sidebar to {self.output_file}: {e}")
            raise


def main():
    """Command line interface for sidebar generation"""
    parser = argparse.ArgumentParser(description='Generate documentation sidebar')
    parser.add_argument('--projects-dir', '-p', type=str, default='godot-demo-projects',
                        help='Path to the projects directory (default: godot-demo-projects)')
    parser.add_argument('--output', '-o', type=str, default='_sidebar.md',
                        help='Output file path (default: _sidebar.md)')
    parser.add_argument('--base-url', '-b', type=str, default='/godot-demo-projects',
                        help='Base URL for links (default: /godot-demo-projects)')
    parser.add_argument('--no-build-system', action='store_true',
                        help='Exclude build system documentation from sidebar')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    try:
        generator = SidebarGenerator(
            projects_dir=Path(args.projects_dir),
            output_file=Path(args.output),
            base_url=args.base_url,
            verbose=args.verbose
        )
        
        content = generator.generate_sidebar(include_build_system=not args.no_build_system)
        generator.write_sidebar(content)
        
        if args.verbose:
            print(f"✅ Sidebar generation completed successfully!")
            
    except Exception as e:
        print(f"❌ Sidebar generation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
