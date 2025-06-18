"""
Dependency Scanner for Smart Build Management
"""

import os
import hashlib
from pathlib import Path


class DependencyScanner:
    """Smart dependency tracking for incremental builds"""
    
    def __init__(self):
        self.cache_file = 'cache/dependencies.cache'
        self.dependencies = {}
        self.load_cache()
    
    def load_cache(self):
        """Load dependency cache from disk"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    # Simple cache format: file_path:hash
                    for line in f:
                        if ':' in line:
                            path, hash_val = line.strip().split(':', 1)
                            self.dependencies[path] = hash_val
        except Exception as e:
            print(f"⚠️  Could not load dependency cache: {e}")
    
    def save_cache(self):
        """Save dependency cache to disk"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                for path, hash_val in self.dependencies.items():
                    f.write(f"{path}:{hash_val}\n")
        except Exception as e:
            print(f"⚠️  Could not save dependency cache: {e}")
    
    def get_file_hash(self, file_path):
        """Get hash of file contents"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def has_changed(self, file_path):
        """Check if file has changed since last build"""
        current_hash = self.get_file_hash(file_path)
        if current_hash is None:
            return True
        
        cached_hash = self.dependencies.get(file_path)
        changed = cached_hash != current_hash
        
        if changed or cached_hash is None:
            self.dependencies[file_path] = current_hash
        
        return changed
    
    def scan_project_dependencies(self, project_dir):
        """Scan all dependencies for a Godot project"""
        dependencies = []
        
        # Common Godot file extensions
        extensions = ['.gd', '.cs', '.tres', '.tscn', '.png', '.jpg', '.ogg', '.wav', '.mp3']
        
        for root, dirs, files in os.walk(project_dir):
            # Skip exports directory
            if 'exports' in dirs:
                dirs.remove('exports')
            
            for file in files:
                file_path = os.path.join(root, file)
                if any(file.endswith(ext) for ext in extensions) or file == 'project.godot':
                    dependencies.append(file_path)
        
        return dependencies
    
    def project_needs_rebuild(self, project_dir):
        """Check if project needs to be rebuilt"""
        dependencies = self.scan_project_dependencies(project_dir)
        
        for dep in dependencies:
            if self.has_changed(dep):
                return True, dep
        
        return False, None
