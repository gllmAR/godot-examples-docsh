"""
Parallel Processing Manager for Optimal Job Scheduling
"""

import os
import multiprocessing
import psutil


class ParallelManager:
    """Intelligent parallel processing management"""
    
    def __init__(self):
        self.cpu_count = multiprocessing.cpu_count()
        self.available_memory = self.get_available_memory()
        
    def get_available_memory(self):
        """Get available system memory in GB"""
        try:
            return psutil.virtual_memory().available / (1024**3)
        except:
            return 8.0  # Fallback assumption
    
    def get_optimal_job_count(self):
        """Calculate optimal number of parallel jobs"""
        # Start with CPU count minus 1 (leave one core free)
        base_jobs = max(1, self.cpu_count - 1)
        
        # Adjust based on memory (Godot exports can be memory intensive)
        # Assume each Godot export needs ~2GB RAM
        memory_limited_jobs = max(1, int(self.available_memory / 2))
        
        # Use the more conservative estimate
        optimal_jobs = min(base_jobs, memory_limited_jobs)
        
        # Override with environment variable if set
        env_jobs = os.environ.get('MAX_PARALLEL_JOBS')
        if env_jobs:
            try:
                return max(1, int(env_jobs))
            except ValueError:
                pass
        
        return optimal_jobs
    
    def estimate_build_time(self, num_projects, jobs=None):
        """Estimate build time based on project count and parallelism"""
        if jobs is None:
            jobs = self.get_optimal_job_count()
        
        # Rough estimates based on testing
        avg_project_time = 8  # seconds per project
        
        # Sequential time
        sequential_time = num_projects * avg_project_time
        
        # Parallel time (with some overhead)
        parallel_time = (num_projects / jobs) * avg_project_time * 1.1
        
        return {
            'sequential_minutes': sequential_time / 60,
            'parallel_minutes': parallel_time / 60,
            'speedup': sequential_time / parallel_time if parallel_time > 0 else 1,
            'jobs': jobs
        }
