"""
Build Configuration for SCons Build System
"""

import os
import multiprocessing


class BuildConfig:
    """Build configuration management"""
    
    def __init__(self):
        self.godot_binary = os.environ.get('GODOT_BINARY', 'godot')
        self.projects_dir = os.environ.get('PROJECTS_DIR', '../godot-demo-projects')
        self.max_parallel_jobs = int(os.environ.get('MAX_PARALLEL_JOBS', multiprocessing.cpu_count() - 1))
        self.verbose = os.environ.get('BUILD_VERBOSE', 'false').lower() == 'true'
        self.enable_caching = os.environ.get('ENABLE_CACHING', 'true').lower() == 'true'
        
    def apply_to_environment(self, env):
        """Apply configuration to SCons environment"""
        env['GODOT_BINARY'] = self.godot_binary
        env['PROJECTS_DIR'] = self.projects_dir
        env['MAX_PARALLEL_JOBS'] = self.max_parallel_jobs
        env['VERBOSE'] = self.verbose
        env['ENABLE_CACHING'] = self.enable_caching
        
        # Set default values
        env['BUILD_MODE'] = 'dev'
        env['SHOW_PROGRESS'] = False
        env['DRY_RUN'] = False
