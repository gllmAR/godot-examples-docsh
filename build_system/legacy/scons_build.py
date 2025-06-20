#!/usr/bin/env python3
"""
SCons-like build system for Godot Examples Documentation
Inspired by Godot's own SCons build system approach
"""

import os
import sys
import subprocess
import multiprocessing
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import hashlib
from dataclasses import dataclass, field

@dataclass
class ExportTarget:
    """Represents a Godot project export target"""
    project_path: Path
    export_path: Path
    preset_name: str = "web"
    dependencies: List[Path] = field(default_factory=list)

@dataclass
class BuildResult:
    """Result of a build operation"""
    target: ExportTarget
    success: bool
    duration: float
    output: str
    file_size: Optional[int] = None
    error: Optional[str] = None

class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    PURPLE = '\033[0;35m'
    NC = '\033[0m'  # No Color

class BuildEnvironment:
    """SCons-like build environment for Godot projects"""
    
    def __init__(self, **kwargs):
        self.options = {
            'jobs': kwargs.get('jobs', multiprocessing.cpu_count() - 1),
            'verbose': kwargs.get('verbose', False),
            'godot_binary': kwargs.get('godot_binary', 'godot'),
            'cache_dir': Path(kwargs.get('cache_dir', '.build_cache')),
            'force_rebuild': kwargs.get('force_rebuild', False),
            'target_platform': kwargs.get('target_platform', 'web'),
            'export_preset': kwargs.get('export_preset', 'web'),
            'expected_version': kwargs.get('expected_version', None),
        }
        
        self.targets: List[ExportTarget] = []
        self.build_cache: Dict[str, dict] = {}
        self.start_time = time.time()
        
        # Create cache directory
        self.options['cache_dir'].mkdir(exist_ok=True)
        self._load_cache()
        
        # Verify Godot installation
        self._verify_godot()
        
    def _verify_godot(self):
        """Verify Godot binary is available"""
        try:
            result = subprocess.run(
                [self.options['godot_binary'], '--version'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self._log('INFO', f"Found Godot: {version}")
                
                # Check if version meets minimum requirements
                if self._check_godot_version(version):
                    return
                else:
                    self._log('WARN', f"Godot version {version} may not be compatible")
            else:
                raise FileNotFoundError("Godot binary check failed")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Try common Godot paths
            common_paths = [
                '/Applications/Godot.app/Contents/MacOS/Godot',
                '/usr/local/bin/godot',
                '/opt/godot/godot',
                f'{os.path.expanduser("~")}/.local/bin/godot',
                'godot4',
                'godot-4'
            ]
            
            for path in common_paths:
                try:
                    result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        self.options['godot_binary'] = path
                        version = result.stdout.strip()
                        self._log('INFO', f"Found Godot at {path}: {version}")
                        return
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            raise FileNotFoundError("Godot binary not found in common locations")
    
    def _check_godot_version(self, version_str: str) -> bool:
        """Check if Godot version meets minimum requirements"""
        import re
        
        # Extract version number (e.g., "4.4.1.stable.official" -> "4.4.1")
        version_match = re.match(r'(\d+)\.(\d+)\.(\d+)', version_str)
        if not version_match:
            return False
        
        major, minor, patch = map(int, version_match.groups())
        
        # Require Godot 4.0 or higher
        if major < 4:
            self._log('ERROR', f"Godot {major}.{minor}.{patch} is too old. Requires Godot 4.0+")
            return False
        
        # Warn about very new versions that might not be tested
        if major > 4 or (major == 4 and minor > 5):
            self._log('WARN', f"Godot {major}.{minor}.{patch} is newer than tested. May have issues.")
        
        return True
    
    def _load_cache(self):
        """Load build cache from disk"""
        cache_file = self.options['cache_dir'] / 'build_cache.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.build_cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.build_cache = {}
    
    def _save_cache(self):
        """Save build cache to disk"""
        cache_file = self.options['cache_dir'] / 'build_cache.json'
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.build_cache, f, indent=2)
        except IOError:
            self._log('WARN', "Failed to save build cache")
    
    def _log(self, level: str, message: str):
        """Log a message with color coding"""
        timestamp = time.strftime('%H:%M:%S')
        color_map = {
            'INFO': Colors.BLUE,
            'SUCCESS': Colors.GREEN,
            'ERROR': Colors.RED,
            'WARN': Colors.YELLOW,
            'STEP': Colors.PURPLE,
            'PROGRESS': Colors.CYAN
        }
        
        color = color_map.get(level, Colors.NC)
        icon_map = {
            'INFO': 'ℹ️',
            'SUCCESS': '✅',
            'ERROR': '❌',
            'WARN': '⚠️',
            'STEP': '🔄',
            'PROGRESS': '📊'
        }
        
        icon = icon_map.get(level, '•')
        print(f"{color}[{timestamp}] {icon} {message}{Colors.NC}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file"""
        if not file_path.exists():
            return ""
        
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except IOError:
            return ""
    
    def _needs_rebuild(self, target: ExportTarget) -> bool:
        """Check if target needs to be rebuilt based on dependencies"""
        if self.options['force_rebuild']:
            return True
        
        # Check if target exists (use absolute path)
        absolute_export_path = target.project_path / target.export_path
        if not absolute_export_path.exists():
            return True
        
        target_key = str(target.project_path)
        if target_key not in self.build_cache:
            return True
        
        cache_entry = self.build_cache[target_key]
        
        # Check project.godot file
        project_file = target.project_path / 'project.godot'
        if not project_file.exists():
            return True
        
        current_hash = self._get_file_hash(project_file)
        if cache_entry.get('project_hash') != current_hash:
            return True
        
        # Check dependencies
        for dep in target.dependencies:
            if not dep.exists():
                return True
            
            dep_hash = self._get_file_hash(dep)
            if cache_entry.get('dependencies', {}).get(str(dep)) != dep_hash:
                return True
        
        return False
    
    def _update_cache(self, target: ExportTarget, result: BuildResult):
        """Update build cache for target"""
        target_key = str(target.project_path)
        project_file = target.project_path / 'project.godot'
        
        cache_entry = {
            'project_hash': self._get_file_hash(project_file),
            'dependencies': {
                str(dep): self._get_file_hash(dep) for dep in target.dependencies
            },
            'build_time': time.time(),
            'success': result.success,
            'duration': result.duration
        }
        
        self.build_cache[target_key] = cache_entry
    
    def _create_export_preset(self, project_path: Path):
        """Create web export preset for project"""
        preset_file = project_path / 'export_presets.cfg'
        
        if not preset_file.exists():
            # Create completely new preset file
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
            try:
                with open(preset_file, 'w') as f:
                    f.write(preset_content)
            except IOError:
                self._log('WARN', f"Failed to create export preset for {project_path}")
        else:
            # Check if web preset exists in existing file
            try:
                with open(preset_file, 'r') as f:
                    content = f.read()
                
                # Check if there's already a web preset
                if 'platform="Web"' in content or 'name="web"' in content:
                    return  # Web preset already exists
                
                # Find the highest preset number
                import re
                preset_numbers = re.findall(r'\[preset\.(\d+)\]', content)
                next_preset = max([int(n) for n in preset_numbers], default=-1) + 1
                
                # Append web preset
                web_preset = f"""
[preset.{next_preset}]

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

[preset.{next_preset}.options]

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
                
                with open(preset_file, 'a') as f:
                    f.write(web_preset)
                    
                self._log('INFO', f"Added web export preset to {project_path.name}")
                
            except IOError:
                self._log('WARN', f"Failed to modify export preset for {project_path}")
    
    def _export_project(self, target: ExportTarget) -> BuildResult:
        """Export a single Godot project"""
        start_time = time.time()
        
        # Create export preset
        self._create_export_preset(target.project_path)
        
        # Ensure export directory exists (use absolute path)
        try:
            export_dir = target.project_path / target.export_path.parent
            export_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created export directory: {export_dir}")
            print(f"📄 Export target: {target.project_path / target.export_path}")
            print(f"🏠 Working directory: {os.getcwd()}")
            print(f"📦 Project path: {target.project_path}")
        except Exception as e:
            print(f"❌ Failed to create export directory: {e}")
            return BuildResult(target, False, time.time() - start_time, f"Directory creation failed: {e}")
        
        # Run Godot export
        cmd = [
            self.options['godot_binary'],
            '--headless',
            '--export-release',
            target.preset_name,
            str(target.export_path)
        ]
        
        print(f"🚀 Running command: {' '.join(cmd)}")
        print(f"📂 In directory: {target.project_path}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=target.project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            # Check if export was successful (use absolute paths)
            absolute_export_path = target.project_path / target.export_path
            wasm_path = absolute_export_path.with_suffix('.wasm')
            success = absolute_export_path.exists() and wasm_path.exists()
            
            file_size = None
            if success and wasm_path.exists():
                file_size = wasm_path.stat().st_size
            
            return BuildResult(
                target=target,
                success=success,
                duration=duration,
                output=result.stdout + result.stderr,
                file_size=file_size,
                error=None if success else result.stderr
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return BuildResult(
                target=target,
                success=False,
                duration=duration,
                output="",
                error="Export timeout after 5 minutes"
            )
        except Exception as e:
            duration = time.time() - start_time
            return BuildResult(
                target=target,
                success=False,
                duration=duration,
                output="",
                error=str(e)
            )
    
    def AddTarget(self, project_path: str, **kwargs) -> ExportTarget:
        """Add a build target (SCons-like interface)"""
        project_path_obj = Path(project_path)
        
        # Default export path (relative to project directory)
        export_path = Path("exports") / "web" / "index.html"
        if 'export_path' in kwargs:
            export_path = Path(kwargs['export_path'])
        
        # Dependencies
        dependencies = []
        if 'dependencies' in kwargs:
            dependencies = [Path(dep) for dep in kwargs['dependencies']]
        
        # Add project.godot as implicit dependency
        project_file = project_path_obj / 'project.godot'
        if project_file.exists():
            dependencies.append(project_file)
        
        target = ExportTarget(
            project_path=project_path_obj,
            export_path=export_path,
            preset_name=kwargs.get('preset_name', self.options['export_preset']),
            dependencies=dependencies
        )
        
        self.targets.append(target)
        return target
    
    def ScanForProjects(self, root_dir: str = "godot-demo-projects") -> List[ExportTarget]:
        """Scan for Godot projects and add them as targets"""
        root_path = Path(root_dir)
        targets = []
        
        if not root_path.exists():
            self._log('ERROR', f"Project directory not found: {root_dir}")
            return targets
        
        # Find all project.godot files
        project_files = list(root_path.rglob('project.godot'))
        
        for project_file in project_files:
            project_dir = project_file.parent
            target = self.AddTarget(str(project_dir))
            targets.append(target)
        
        self._log('INFO', f"Found {len(targets)} Godot projects")
        return targets
    
    def Build(self, targets: Optional[List[ExportTarget]] = None) -> bool:
        """Build all targets using parallel processing"""
        if targets is None:
            targets = self.targets
        
        if not targets:
            self._log('WARN', "No targets to build")
            return True
        
        self._log('STEP', f"Building {len(targets)} targets with {self.options['jobs']} parallel jobs")
        
        # Filter targets that need rebuilding
        targets_to_build = []
        skipped_count = 0
        
        for target in targets:
            if self._needs_rebuild(target):
                targets_to_build.append(target)
            else:
                skipped_count += 1
        
        if skipped_count > 0:
            self._log('INFO', f"Skipping {skipped_count} up-to-date targets")
        
        if not targets_to_build:
            self._log('SUCCESS', "All targets are up-to-date")
            return True
        
        # Build targets in parallel
        successful_builds = 0
        failed_builds = 0
        
        with ThreadPoolExecutor(max_workers=self.options['jobs']) as executor:
            # Submit all build jobs
            future_to_target = {
                executor.submit(self._export_project, target): target 
                for target in targets_to_build
            }
            
            # Process completed builds
            for future in as_completed(future_to_target):
                result = future.result()
                target = result.target
                
                # Update cache
                self._update_cache(target, result)
                
                # Log result
                project_name = target.project_path.name
                relative_path = str(target.project_path).replace('godot-demo-projects/', '')
                
                if result.success:
                    successful_builds += 1
                    size_mb = f"{result.file_size / (1024*1024):.1f}MB" if result.file_size else "unknown"
                    self._log('SUCCESS', f"{relative_path} ({result.duration:.1f}s) - WASM: {size_mb}")
                else:
                    failed_builds += 1
                    error_msg = result.error or "Unknown error"
                    self._log('ERROR', f"{relative_path} ({result.duration:.1f}s) - {error_msg}")
                    
                    if self.options['verbose'] and result.output:
                        print(f"Output: {result.output[:200]}...")
                
                # Show progress
                completed = successful_builds + failed_builds
                total = len(targets_to_build)
                progress = (completed * 100) // total
                success_rate = (successful_builds * 100) // completed if completed > 0 else 100
                
                self._log('PROGRESS', 
                    f"{completed}/{total} ({progress}%) | ✅ {successful_builds} | ❌ {failed_builds} | Success: {success_rate}%")
        
        # Save cache
        self._save_cache()
        
        # Summary
        total_time = time.time() - self.start_time
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)
        
        print(f"\n{Colors.CYAN}🎯 Build Summary{Colors.NC}")
        print("="*50)
        print(f"📊 Total targets: {len(targets_to_build)}")
        print(f"{Colors.GREEN}✅ Successful: {successful_builds}{Colors.NC}")
        if failed_builds > 0:
            print(f"{Colors.RED}❌ Failed: {failed_builds}{Colors.NC}")
        print(f"⏱️  Total time: {minutes}m {seconds}s")
        print(f"🚀 Parallel efficiency: ~{self.options['jobs']}x speedup")
        
        return failed_builds == 0

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SCons-like build system for Godot Examples")
    parser.add_argument('-j', '--jobs', type=int, default=multiprocessing.cpu_count() - 1,
                        help='Number of parallel jobs')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')
    parser.add_argument('--godot-binary', default='godot',
                        help='Path to Godot binary')
    parser.add_argument('--godot-version', 
                        help='Expected Godot version (for validation)')
    parser.add_argument('--force-rebuild', action='store_true',
                        help='Force rebuild all targets')
    parser.add_argument('--cache-dir', default='.build_cache',
                        help='Build cache directory')
    parser.add_argument('--projects-dir', default='godot-demo-projects',
                        help='Root directory containing Godot projects')
    parser.add_argument('--add-embed-markers', action='store_true',
                        help='Add embed markers to README files after building')
    parser.add_argument('--inject-embeds', action='store_true',
                        help='Inject actual embeds into README files (replaces markers)')
    parser.add_argument('--generate-docs', action='store_true',
                        help='Generate documentation sidebar and embed processing')
    parser.add_argument('--docs-output', default='_sidebar.md',
                        help='Output file for generated sidebar (default: _sidebar.md)')
    parser.add_argument('--continue-on-error', action='store_true',
                        help='Continue and create website even if some projects fail to build')
    
    args = parser.parse_args()
    
    try:
        # Create build environment
        env = BuildEnvironment(
            jobs=args.jobs,
            verbose=args.verbose,
            godot_binary=args.godot_binary,
            force_rebuild=args.force_rebuild,
            cache_dir=args.cache_dir,
            expected_version=args.godot_version
        )
        
        # Scan for projects and build
        targets = env.ScanForProjects(args.projects_dir)
        success = env.Build(targets)
        
        # Post-build processing
        if success and (args.add_embed_markers or args.inject_embeds or args.generate_docs):
            from pathlib import Path
            import subprocess
            
            # Generate documentation sidebar if requested
            if args.generate_docs:
                print(f"{Colors.BLUE}📚 Generating documentation sidebar...{Colors.NC}")
                sidebar_script = Path(__file__).parent / 'builders' / 'sidebar_generator.py'
                result = subprocess.run([
                    sys.executable, str(sidebar_script),
                    '--projects-dir', args.projects_dir,
                    '--output', args.docs_output,
                    '--verbose' if args.verbose else '--quiet'
                ], capture_output=not args.verbose)
                
                if result.returncode == 0:
                    print(f"{Colors.GREEN}✅ Documentation sidebar generated: {args.docs_output}{Colors.NC}")
                else:
                    print(f"{Colors.YELLOW}⚠️  Documentation generation completed with warnings{Colors.NC}")
                
                # When generating docs, also add embed markers and inject embeds
                embed_script = Path(__file__).parent / 'builders' / 'embed_injector.py'
                
                print(f"{Colors.BLUE}🔗 Adding embed markers to README files...{Colors.NC}")
                result = subprocess.run([
                    sys.executable, str(embed_script), 'add-markers',
                    '--projects-dir', args.projects_dir,
                    '--verbose' if args.verbose else '--quiet'
                ], capture_output=not args.verbose)
                
                if result.returncode == 0:
                    print(f"{Colors.GREEN}✅ Embed markers added{Colors.NC}")
                else:
                    print(f"{Colors.YELLOW}⚠️  Embed marker addition completed with warnings{Colors.NC}")
                
                print(f"{Colors.BLUE}🎮 Injecting embeds into README files...{Colors.NC}")
                result = subprocess.run([
                    sys.executable, str(embed_script),
                    '--projects-dir', args.projects_dir,
                    '--in-place',
                    '--verbose' if args.verbose else '--quiet'
                ], capture_output=not args.verbose)
                
                if result.returncode == 0:
                    print(f"{Colors.GREEN}✅ Embeds injected successfully{Colors.NC}")
                else:
                    print(f"{Colors.YELLOW}⚠️  Embed injection completed with warnings{Colors.NC}")
            
            # Separate embed processing (when not part of docs generation)
            if not args.generate_docs:
                embed_script = Path(__file__).parent / 'builders' / 'embed_injector.py'
                
                if args.add_embed_markers:
                    print(f"{Colors.BLUE}🔗 Adding embed markers to README files...{Colors.NC}")
                    result = subprocess.run([
                        sys.executable, str(embed_script), 'add-markers',
                        '--projects-dir', args.projects_dir,
                        '--verbose' if args.verbose else '--quiet'
                    ], capture_output=not args.verbose)
                    
                    if result.returncode != 0:
                        print(f"{Colors.YELLOW}⚠️  Embed marker addition completed with warnings{Colors.NC}")
                
                if args.inject_embeds:
                    print(f"{Colors.BLUE}🎮 Injecting embeds into README files...{Colors.NC}")
                    result = subprocess.run([
                        sys.executable, str(embed_script),
                        '--projects-dir', args.projects_dir,
                        '--in-place',
                        '--verbose' if args.verbose else '--quiet'
                    ], capture_output=not args.verbose)
                    
                    if result.returncode != 0:
                        print(f"{Colors.YELLOW}⚠️  Embed injection completed with warnings{Colors.NC}")
        
        # Exit with appropriate code
        if args.continue_on_error:
            # Always exit successfully when continue-on-error is set
            if not success:
                print(f"{Colors.YELLOW}⚠️  Some builds failed but continuing due to --continue-on-error flag{Colors.NC}")
            sys.exit(0)
        else:
            # Traditional behavior: fail if any builds failed
            sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Build interrupted by user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Build failed: {e}{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
