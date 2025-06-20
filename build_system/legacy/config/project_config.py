#!/usr/bin/env python3
"""
Build System Configuration Interface
====================================

Provides a clean interface for configuring the Godot build system
for different repository structures and requirements.
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict, field


@dataclass
class ProjectStructure:
    """Defines the expected project structure for the build system"""
    # Source directories
    projects_dir: str = "godot-demo-projects"  # Where Godot projects are located
    docs_dir: str = "docs"                     # Generated documentation output
    cache_dir: str = ".build_cache"            # Build cache location
    
    # Documentation website structure  
    site_root: str = "."                       # Root for documentation site
    sidebar_file: str = "_sidebar.md"          # Sidebar configuration
    index_file: str = "index.html"             # Main index file
    
    # Output structure
    exports_subdir: str = "exports/web"        # Subdirectory for web exports within each project
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod 
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectStructure':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class LoggingConfig:
    """Logging configuration for the build system"""
    verbose_downloads: bool = False       # Show detailed download progress
    progress_updates: bool = True         # Show progress bars
    ci_mode: bool = False                # Enable CI-friendly logging
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod 
    def from_dict(cls, data: Dict[str, Any]) -> 'LoggingConfig':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class BuildSystemConfig:
    """Main configuration for the build system"""
    # Project identification
    project_name: str = "Godot Examples"
    project_url: str = ""
    
    # Build settings
    godot_version: str = "4.5-beta1"
    python_version: str = "3.11"
    max_parallel_jobs: Optional[int] = None
    
    # Feature flags
    enable_web_exports: bool = True
    enable_documentation_generation: bool = True
    enable_embed_injection: bool = True
    enable_sidebar_generation: bool = True
    enable_caching: bool = True
    
    # Advanced settings
    verbose_output: bool = False
    dry_run_mode: bool = False
    
    # Project structure
    structure: ProjectStructure = field(default_factory=ProjectStructure)
    
    # Logging configuration
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Custom patterns and filters
    project_include_patterns: Optional[List[str]] = None
    project_exclude_patterns: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.max_parallel_jobs is None:
            import multiprocessing
            self.max_parallel_jobs = max(1, multiprocessing.cpu_count() - 1)
        
        if self.project_include_patterns is None:
            self.project_include_patterns = ["**/project.godot"]
        
        if self.project_exclude_patterns is None:
            self.project_exclude_patterns = [
                "**/.*",  # Hidden directories
                "**/addons/godot-git-plugin/**",  # Git plugin
                "**/exports/**",  # Existing exports
            ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['structure'] = self.structure.to_dict()
        data['logging'] = self.logging.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BuildSystemConfig':
        """Create from dictionary"""
        if 'structure' in data:
            data['structure'] = ProjectStructure.from_dict(data['structure'])
        if 'logging' in data:
            data['logging'] = LoggingConfig.from_dict(data['logging'])
        return cls(**data)
    
    def save_to_file(self, config_path: Path):
        """Save configuration to JSON file"""
        with open(config_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, config_path: Path) -> 'BuildSystemConfig':
        """Load configuration from JSON file"""
        with open(config_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def load_from_environment(cls) -> 'BuildSystemConfig':
        """Load configuration from environment variables"""
        config = cls()
        
        # Override with environment variables
        if 'GODOT_VERSION' in os.environ:
            config.godot_version = os.environ['GODOT_VERSION']
        
        if 'PYTHON_VERSION' in os.environ:
            config.python_version = os.environ['PYTHON_VERSION']
        
        if 'MAX_PARALLEL_JOBS' in os.environ:
            config.max_parallel_jobs = int(os.environ['MAX_PARALLEL_JOBS'])
        
        if 'PROJECTS_DIR' in os.environ:
            config.structure.projects_dir = os.environ['PROJECTS_DIR']
        
        if 'BUILD_VERBOSE' in os.environ:
            config.verbose_output = os.environ['BUILD_VERBOSE'].lower() == 'true'
        
        if 'ENABLE_CACHING' in os.environ:
            config.enable_caching = os.environ['ENABLE_CACHING'].lower() == 'true'
        
        return config
    
    def apply_to_environment(self, env_dict: Dict[str, Any]):
        """Apply configuration to a build environment dictionary"""
        env_dict.update({
            'PROJECT_NAME': self.project_name,
            'PROJECT_URL': self.project_url,
            'GODOT_VERSION': self.godot_version,
            'PYTHON_VERSION': self.python_version,
            'MAX_PARALLEL_JOBS': self.max_parallel_jobs,
            'PROJECTS_DIR': self.structure.projects_dir,
            'DOCS_DIR': self.structure.docs_dir,
            'CACHE_DIR': self.structure.cache_dir,
            'SITE_ROOT': self.structure.site_root,
            'SIDEBAR_FILE': self.structure.sidebar_file,
            'INDEX_FILE': self.structure.index_file,
            'EXPORTS_SUBDIR': self.structure.exports_subdir,
            'ENABLE_WEB_EXPORTS': self.enable_web_exports,
            'ENABLE_DOCUMENTATION_GENERATION': self.enable_documentation_generation,
            'ENABLE_EMBED_INJECTION': self.enable_embed_injection,
            'ENABLE_SIDEBAR_GENERATION': self.enable_sidebar_generation,
            'ENABLE_CACHING': self.enable_caching,
            'VERBOSE': self.verbose_output,
            'DRY_RUN': self.dry_run_mode,
            'PROJECT_INCLUDE_PATTERNS': self.project_include_patterns,
            'PROJECT_EXCLUDE_PATTERNS': self.project_exclude_patterns,
        })


def create_default_config(project_root: Path) -> BuildSystemConfig:
    """Create a default configuration for a new project"""
    config = BuildSystemConfig()
    
    # Auto-detect project structure
    if (project_root / "godot-demo-projects").exists():
        config.structure.projects_dir = "godot-demo-projects"
    elif (project_root / "projects").exists():
        config.structure.projects_dir = "projects"
    elif (project_root / "examples").exists():
        config.structure.projects_dir = "examples"
    
    # Auto-detect project name from directory
    config.project_name = project_root.name.replace("-", " ").replace("_", " ").title()
    
    return config


def setup_build_system(project_root: Path, config: Optional[BuildSystemConfig] = None) -> BuildSystemConfig:
    """
    Set up the build system for a project
    
    Args:
        project_root: Root directory of the project
        config: Optional existing configuration
        
    Returns:
        BuildSystemConfig: The configuration used
    """
    if config is None:
        config_file = project_root / "build_config.json"
        if config_file.exists():
            config = BuildSystemConfig.load_from_file(config_file)
        else:
            config = create_default_config(project_root)
            config.save_to_file(config_file)
    
    # Ensure required directories exist
    for dir_name in [config.structure.docs_dir, config.structure.cache_dir]:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return config


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    else:
        project_root = Path.cwd()
    
    print(f"Setting up build system for: {project_root}")
    config = setup_build_system(project_root)
    print(f"Configuration:")
    print(json.dumps(config.to_dict(), indent=2))
