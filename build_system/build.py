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

from config.project_config import BuildSystemConfig, setup_build_system
from scons_build import BuildEnvironment
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
        config = BuildSystemConfig.load_from_file(args.config)
    else:
        # Try to load from default location or create new
        default_config_path = project_root / "build_config.json"
        if default_config_path.exists():
            config = BuildSystemConfig.load_from_file(default_config_path)
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
            manager = GodotEnvironmentManager(progress)
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
            
            # Validate artifact
            issues = artifact_manager.validate_for_deployment(artifact_dir)
            if issues:
                progress.error(f"❌ Artifact validation failed: {len(issues)} issues")
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
        
        # Create build environment
        env = BuildEnvironment(
            godot_binary=f"godot-{config.godot_version}" if config.godot_version else "godot",
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
            # Scan for projects to show what would be built
            targets = env.ScanForProjects(config.structure.projects_dir)
            if changed_projects:
                # Filter to only changed projects
                filtered_targets = []
                for target in targets:
                    project_rel = str(target.project_path.relative_to(project_root / config.structure.projects_dir))
                    if any(project_rel.startswith(changed) for changed in changed_projects):
                        filtered_targets.append(target)
                targets = filtered_targets
            
            progress.info(f"Found {len(targets)} projects to build:")
            for target in targets[:10]:  # Show first 10
                progress.info(f"  - {target.project_path.name}")
            if len(targets) > 10:
                progress.info(f"  ... and {len(targets) - 10} more")
            return 0
        
        # Perform the actual build
        if args.target in ['all', 'build', 'docs', 'final']:
            if args.target in ['build', 'all', 'final']:
                progress.info("🎮 Building Godot projects...")
                targets = env.ScanForProjects(config.structure.projects_dir)
                
                # Filter targets if we have specific changed projects
                if changed_projects and not args.force_rebuild:
                    original_count = len(targets)
                    filtered_targets = []
                    for target in targets:
                        project_rel = str(target.project_path.relative_to(project_root / config.structure.projects_dir))
                        if any(project_rel.startswith(changed) for changed in changed_projects):
                            filtered_targets.append(target)
                    targets = filtered_targets
                    progress.info(f"🎯 Building {len(targets)} changed projects (out of {original_count} total)")
                
                success = env.Build(targets)
                
                if not success:
                    progress.error("❌ Some builds failed")
                    return 1
            
            # Generate documentation and sidebar
            if args.target in ['docs', 'all', 'final']:
                progress.info("📚 Generating documentation and sidebar...")
                
                # Generate sidebar
                sidebar_script = project_root / "build_system" / "builders" / "sidebar_generator.py"
                sidebar_output = project_root / "_sidebar.md"
                
                result = subprocess.run([
                    sys.executable, str(sidebar_script),
                    '--projects-dir', str(project_root / config.structure.projects_dir),
                    '--output', str(sidebar_output),
                    '--verbose' if config.verbose_output else '--quiet'
                ], capture_output=not config.verbose_output)
                
                if result.returncode == 0:
                    progress.success(f"✅ Documentation sidebar generated: {sidebar_output}")
                else:
                    progress.warning("⚠️  Documentation generation completed with warnings")
            
            # Inject embeds for final/production builds
            if args.target == 'final':
                progress.info("🔗 Injecting game embeds into documentation...")
                
                # Add embed markers first
                result = subprocess.run([
                    sys.executable, str(project_root / "build_system" / "scons_build.py"),
                    '--add-embed-markers',
                    '--projects-dir', str(project_root / config.structure.projects_dir),
                    '--verbose' if config.verbose_output else ''
                ], capture_output=not config.verbose_output)
                
                if result.returncode == 0:
                    progress.success("✅ Embed markers added to project READMEs")
                    
                    # Inject actual embeds
                    result = subprocess.run([
                        sys.executable, str(project_root / "build_system" / "scons_build.py"),
                        '--inject-embeds',
                        '--projects-dir', str(project_root / config.structure.projects_dir),
                        '--verbose' if config.verbose_output else ''
                    ], capture_output=not config.verbose_output)
                    
                    if result.returncode == 0:
                        progress.success("✅ Game embeds injected into documentation")
                    else:
                        progress.warning("⚠️  Embed injection completed with warnings")
                else:
                    progress.warning("⚠️  Embed marker addition completed with warnings")
            
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
