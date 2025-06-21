#!/usr/bin/env python3
"""
Universal Build System Entry Point
==================================

Main entry point for the Godot Build System that can be used across
different repository structures and configurations.
"""

import sys
import argparse
import subprocess
from pathlib import Path

# Add build_system to path for imports
build_system_path = Path(__file__).parent
sys.path.insert(0, str(build_system_path))

from project_config import BuildSystemConfig, setup_build_system
from modern_build_env import ModernBuildEnvironment
from tools.environment_manager import setup_godot_environment
from tools.artifact_manager import ArtifactManager
from tools.change_detector import detect_changes
from tools.progress_reporter import ProgressReporter


def create_argument_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='Universal Godot Build System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Build everything with default config
  %(prog)s --config custom.json     # Use custom configuration file
  %(prog)s --projects-dir examples  # Override projects directory
  %(prog)s --dry-run                # Show what would be built
  %(prog)s build                    # Build exports only
  %(prog)s docs                     # Generate docs only
  %(prog)s final                    # Build with embeds (production)
        """
    )
    
    # Configuration options
    parser.add_argument(
        '--config', '-c',
        type=Path,
        help='Configuration file to use (JSON format)'
    )
    
    parser.add_argument(
        '--projects-dir',
        help='Directory containing Godot projects'
    )
    
    parser.add_argument(
        '--godot-version',
        help='Godot version to use'
    )
    
    parser.add_argument(
        '--jobs', '-j',
        type=int,
        help='Number of parallel jobs'
    )
    
    # Build mode options
    parser.add_argument(
        'target',
        nargs='?',
        default='all',
        choices=['all', 'build', 'docs', 'final', 'clean', 'setup', 'verify', 'artifact'],
        help='Build target (default: all)'
    )
    
    # Environment setup options
    parser.add_argument(
        '--setup-godot',
        action='store_true',
        help='Set up Godot environment (download and install)'
    )
    
    parser.add_argument(
        '--verify-environment',
        action='store_true',
        help='Verify Godot environment is properly set up'
    )
    
    # Change detection options
    parser.add_argument(
        '--force-rebuild',
        action='store_true',
        help='Force rebuild all projects'
    )
    
    parser.add_argument(
        '--base-ref',
        default='HEAD~1',
        help='Base reference for change detection (default: HEAD~1)'
    )
    
    parser.add_argument(
        '--no-change-detection',
        action='store_true',
        help='Skip change detection and build everything'
    )
    
    # Artifact management options
    parser.add_argument(
        '--prepare-artifact',
        action='store_true',
        help='Prepare deployment artifact'
    )
    
    parser.add_argument(
        '--artifact-output',
        type=Path,
        help='Output directory for artifacts'
    )
    
    # Behavioral flags
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be built without actually building'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable build caching'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean build artifacts before building'
    )
    
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview build plan without executing'
    )
    
    parser.add_argument(
        '--progress',
        action='store_true',
        help='Show detailed progress information'
    )
    
    return parser


def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Determine project root
    project_root = Path.cwd()
    
    # Create progress reporter
    progress = ProgressReporter(verbose=args.verbose)
    
    # Load configuration
    if args.config and args.config.exists():
        config = BuildSystemConfig.from_json_file(args.config)
    else:
        # Try to load from default location or create new
        default_config_path = project_root / "build_config.json"
        if default_config_path.exists():
            config = BuildSystemConfig.from_json_file(default_config_path)
        else:
            config = setup_build_system(project_root)
    
    # Override configuration with command line arguments
    if args.projects_dir:
        config.structure.projects_dir = args.projects_dir
    
    if args.godot_version:
        config.godot_version = args.godot_version
    
    if args.jobs:
        config.max_parallel_jobs = args.jobs
    
    if args.verbose:
        config.verbose_output = True
    
    if args.dry_run or args.preview:
        config.dry_run_mode = True
    
    if args.no_cache:
        config.enable_caching = False
    
    try:
        # Handle environment setup targets first
        if args.target == 'setup' or args.setup_godot:
            progress.info("🎮 Setting up Godot environment...")
            success = setup_godot_environment(
                config.godot_version,
                force_reinstall=args.force_rebuild,
                progress_reporter=progress
            )
            return 0 if success else 1
        
        if args.target == 'verify' or args.verify_environment:
            progress.info("🔍 Verifying Godot environment...")
            from tools.environment_manager import GodotEnvironmentManager
            manager = GodotEnvironmentManager(progress, config)
            verification = manager.verify_installation(config.godot_version)
            
            all_good = all(verification.values())
            if all_good:
                progress.success("✅ Environment verification passed")
                return 0
            else:
                progress.error("❌ Environment verification failed")
                for component, status in verification.items():
                    status_icon = "✅" if status else "❌"
                    progress.info(f"  {status_icon} {component.replace('_', ' ').title()}")
                return 1
        
        # Handle artifact preparation
        if args.target == 'artifact' or args.prepare_artifact:
            progress.info("📦 Preparing deployment artifact...")
            artifact_manager = ArtifactManager(progress)
            
            projects_dir = project_root / config.structure.projects_dir
            output_dir = args.artifact_output or project_root / "deployment_artifact"
            
            artifact_dir = artifact_manager.prepare_documentation_artifact(
                project_root, projects_dir, output_dir
            )
            
            # Validate artifact with tolerance for partial failures
            issues = artifact_manager.validate_for_deployment(artifact_dir, config)
            if issues:
                # Check if failures are within acceptable limits
                allow_partial = (hasattr(config, 'deployment') and 
                               getattr(config.deployment, 'allow_partial_failures', False))
                
                if allow_partial:
                    progress.warning(f"⚠️ Artifact has {len(issues)} issues but partial failures are allowed")
                    progress.success(f"✅ Deployment artifact ready at: {artifact_dir}")
                    return 0
                else:
                    progress.error(f"❌ Artifact validation failed: {len(issues)} critical issues")
                    return 1
            else:
                progress.success(f"✅ Deployment artifact ready at: {artifact_dir}")
                return 0
        
        # Handle cleaning
        if args.clean or args.target == 'clean':
            progress.info("🧹 Cleaning build artifacts...")
            
            # Clean cache directory
            import shutil
            cache_dir = project_root / config.structure.cache_dir
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Clean project artifacts
            projects_dir = project_root / config.structure.projects_dir
            if projects_dir.exists():
                artifact_manager = ArtifactManager(progress)
                cleaned_count = artifact_manager.clean_build_artifacts(projects_dir)
                progress.success(f"✅ Cleaned {cleaned_count} artifacts")
            
            if args.target == 'clean':
                return 0
        
        # Detect changes (unless disabled)
        changed_projects = set()
        if not args.no_change_detection and not args.force_rebuild:
            progress.info("🔍 Detecting changes...")
            changes = detect_changes(
                project_root,
                args.base_ref,
                args.force_rebuild,
                use_git=True,
                progress_reporter=progress
            )
            
            if not changes.build_system_changed and not changes.docs_changed and not changes.changed_projects:
                progress.success("✅ No changes detected - skipping build")
                return 0
            
            changed_projects = changes.changed_projects
        
        # Determine Godot binary name - prefer system Godot if available
        import shutil
        if shutil.which("godot"):
            godot_binary = "godot"
        elif config.godot_version:
            godot_binary = f"godot-{config.godot_version}"
        else:
            godot_binary = "godot"
        
        # Create build environment
        env = ModernBuildEnvironment(
            godot_binary=godot_binary,
            projects_dir=project_root / config.structure.projects_dir,
            max_parallel_jobs=config.max_parallel_jobs,
            show_progress=args.progress,
            enable_caching=config.enable_caching,
            verbose=config.verbose_output,
            dry_run=config.dry_run_mode
        )
        
        # Apply configuration to environment
        env_dict = {}
        config.apply_to_environment(env_dict)
        for key, value in env_dict.items():
            setattr(env, key.lower(), value)
        
        if args.preview:
            progress.info("📋 Build Plan Preview:")
            # For preview mode, just scan the directory for projects
            projects_dir = project_root / config.structure.projects_dir
            project_files = list(projects_dir.rglob("project.godot"))
            
            if changed_projects:
                # Filter to only changed projects
                filtered_files = []
                for project_file in project_files:
                    project_rel = str(project_file.parent.relative_to(projects_dir))
                    if any(project_rel.startswith(changed) for changed in changed_projects):
                        filtered_files.append(project_file)
                project_files = filtered_files
            
            progress.info(f"Found {len(project_files)} projects to build:")
            for project_file in project_files[:10]:  # Show first 10
                progress.info(f"  - {project_file.parent.name}")
            if len(project_files) > 10:
                progress.info(f"  ... and {len(project_files) - 10} more")
            return 0
        
        # Perform the actual build
        if args.target in ['all', 'build', 'docs', 'final']:
            if args.target in ['build', 'all', 'final']:
                progress.info("🎮 Building Godot projects...")
                
                # Import the real Godot exporter
                try:
                    from .tools.godot_exporter import GodotExporter, create_fallback_export
                    from .tools.parallel_manager import ParallelManager
                except ImportError:
                    # Fallback for CLI execution
                    import sys
                    tools_path = Path(__file__).parent / "tools"
                    if str(tools_path) not in sys.path:
                        sys.path.insert(0, str(tools_path))
                    from godot_exporter import GodotExporter, create_fallback_export
                    from parallel_manager import ParallelManager
                
                # Find all Godot projects
                projects_dir = project_root / config.structure.projects_dir
                project_files = list(projects_dir.rglob("project.godot"))
                
                if not project_files:
                    progress.warning("⚠️ No Godot projects found in {}".format(projects_dir))
                else:
                    progress.info(f"📦 Found {len(project_files)} projects to process")
                    
                    if args.dry_run:
                        progress.info("🔍 Would export {} projects using Godot".format(len(project_files)))
                    else:
                        # Initialize real Godot exporter
                        exporter = GodotExporter(
                            godot_binary=godot_binary,  # Use the detected system binary
                            progress_reporter=progress
                        )
                        
                        # Verify Godot binary is available
                        if not exporter.verify_godot_binary():
                            progress.error(f"❌ Godot binary not found or not working: {env.config['godot_binary']}")
                            progress.info("💡 Run 'python build_system/build.py setup --godot-version 4.5-beta1' to install Godot")
                            
                            # Create fallback exports instead
                            progress.info("🔄 Creating fallback HTML exports...")
                            for project_file in project_files:
                                project_dir = project_file.parent
                                export_dir = project_dir / "exports" / "web"
                                export_dir.mkdir(parents=True, exist_ok=True)
                                create_fallback_export(project_dir, export_dir)
                            
                            progress.warning("⚠️ Created fallback exports. Install Godot for real game exports.")
                        else:
                            # Use parallel export with real Godot
                            parallel_manager = ParallelManager()
                            optimal_jobs = min(parallel_manager.get_optimal_job_count(), 3)  # Limit to 3 for Godot exports
                            progress.info(f"⚡ Using {optimal_jobs} parallel Godot export jobs")
                            
                            # Export projects in parallel
                            results = exporter.export_projects_parallel(
                                project_files,
                                max_workers=optimal_jobs,
                                force_rebuild=args.force_rebuild
                            )
                            
                            # Generate summary
                            summary = exporter.get_export_summary(results)
                            
                            if summary['failed'] > 0:
                                progress.error(f"❌ {summary['failed']} exports failed: {summary['failed_projects']}")
                                
                                # Create fallback exports for failed projects
                                for result in results:
                                    if not result.success:
                                        export_dir = result.project_path / "exports" / "web"
                                        export_dir.mkdir(parents=True, exist_ok=True)
                                        create_fallback_export(result.project_path, export_dir)
                                
                                if summary['successful'] > 0:
                                    progress.warning(f"⚠️ {summary['successful']} succeeded, {summary['failed']} failed with fallbacks")
                                else:
                                    return 1
                            else:
                                progress.success(f"✅ Successfully exported {summary['successful']} projects")
                                progress.info(f"📊 Total size: {summary['total_export_size']:,} bytes, "
                                            f"avg time: {summary['average_export_time']:.1f}s per project")
            
            # Generate documentation and sidebar
            if args.target in ['docs', 'all', 'final']:
                progress.info("📚 Generating documentation and sidebar...")
                
                # Use improved sidebar generation
                sidebar_output = project_root / "_sidebar.md"
                projects_dir = project_root / config.structure.projects_dir
                
                if args.dry_run:
                    progress.info(f"🔍 Would generate sidebar: {sidebar_output}")
                else:
                    # Import and use improved sidebar generator
                    try:
                        from tools.sidebar_generator import generate_sidebar
                        
                        sidebar_content, errors = generate_sidebar(
                            projects_dir, config, validate=True, verbose=args.verbose
                        )
                        
                        if errors:
                            progress.warning(f"⚠️  Sidebar generated with {len(errors)} warnings:")
                            for error in errors[:3]:  # Show first 3 errors
                                progress.warning(f"   - {error}")
                            if len(errors) > 3:
                                progress.warning(f"   ... and {len(errors) - 3} more")
                        
                        sidebar_output.write_text(sidebar_content)
                        progress.success(f"✅ Documentation sidebar generated: {sidebar_output}")
                        
                    except ImportError:
                        # Fallback to basic generation if improved generator not available
                        progress.warning("⚠️  Using fallback sidebar generation")
                        
                        # Generate basic sidebar content (without title for Docsify compatibility)
                        sidebar_content = ""
                        
                        # Find all projects and create sidebar entries
                        project_files = list(projects_dir.rglob("project.godot"))
                        
                        if project_files:
                            # Group by category (subdirectory)
                            categories = {}
                            for project_file in project_files:
                                project_dir = project_file.parent
                                relative_path = project_dir.relative_to(projects_dir)
                                
                                # Get category (first level directory)
                                parts = relative_path.parts
                                if parts and len(parts) > 0:
                                    category = parts[0]
                                    project_name = parts[-1] if len(parts) > 1 else parts[0]
                                    
                                    if category not in categories:
                                        categories[category] = []
                                    categories[category].append((project_name, relative_path))
                            
                            # Build sidebar content in Docsify format
                            for category, projects in sorted(categories.items()):
                                sidebar_content += f"- {category.upper()}\n\n"
                                for project_name, path in sorted(projects):
                                    sidebar_content += f"  - [{project_name}](/{config.structure.projects_dir}/{path}/README.md)\n"
                                sidebar_content += "\n"
                        else:
                            sidebar_content += "No projects found.\n"
                        
                        sidebar_output.write_text(sidebar_content)
                        progress.success(f"✅ Documentation sidebar generated: {sidebar_output}")
            
            # Inject embeds for final/production builds
            if args.target == 'final':
                progress.info("🔗 Injecting game embeds into documentation...")
                
                if args.dry_run:
                    progress.info("🔍 Would inject game embeds into documentation")
                else:
                    # Basic embed injection - add placeholder embeds to README files
                    projects_dir = project_root / config.structure.projects_dir
                    project_files = list(projects_dir.rglob("project.godot"))
                    
                    for project_file in project_files:
                        project_dir = project_file.parent
                        readme_file = project_dir / "README.md"
                        
                        if readme_file.exists():
                            content = readme_file.read_text()
                            
                            # Add embed placeholder if not already present
                            embed_marker = "<!-- GAME_EMBED -->"
                            if embed_marker not in content:
                                embed_html = f"""
{embed_marker}
<div class="game-embed">
    <iframe src="./exports/index.html" width="800" height="600" frameborder="0">
        <p>Your browser does not support iframes. <a href="./exports/index.html">Click here to play the game</a>.</p>
    </iframe>
</div>
<!-- /GAME_EMBED -->
"""
                                content = content + "\n" + embed_html
                                readme_file.write_text(content)
                    
                    progress.success("✅ Game embeds injected into documentation")
            
            # Post-build verification
            if not config.dry_run_mode:
                progress.info("🔍 Verifying build results...")
                artifact_manager = ArtifactManager(progress)
                projects_dir = project_root / config.structure.projects_dir
                verification = artifact_manager.verify_build_results(projects_dir)
                
                if verification['success_rate'] == 100:
                    progress.success(f"✅ All {verification['total_projects']} projects built successfully!")
                else:
                    progress.warning(f"⚠️  {verification['complete_exports']}/{verification['total_projects']} projects built ({verification['success_rate']:.1f}% success rate)")
        
        progress.success("✅ Build completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        progress.error("\n⚠️ Build interrupted by user")
        return 130
    except Exception as e:
        progress.error(f"❌ Build failed: {e}")
        if config.verbose_output:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
