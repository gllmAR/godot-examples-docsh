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
        # Check if we're in CI environment (more aggressive)
        is_ci = any(var in os.environ for var in ['CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS_URL', 'BUILDKITE'])
        
        if is_ci:
            # In CI, use all cores more aggressively
            base_jobs = self.cpu_count
        else:
            # Local development, leave one core free
            base_jobs = max(1, self.cpu_count - 1)
        
        # Adjust based on memory (Godot exports can be memory intensive)
        # Assume each Godot export needs ~1.5GB RAM (reduced from 2GB for better utilization)
        memory_limited_jobs = max(1, int(self.available_memory / 1.5))
        
        # Use the more conservative estimate
        optimal_jobs = min(base_jobs, memory_limited_jobs)
        
        # Override with environment variable if set
        env_jobs = os.environ.get('MAX_PARALLEL_JOBS')
        if env_jobs:
            try:
                return max(1, int(env_jobs))
            except ValueError:
                pass
        
        # Ensure we use at least 2 jobs if we have resources
        return max(2, optimal_jobs) if self.cpu_count >= 2 else 1
    
    def get_dynamic_job_count(self, current_load=None):
        """Get dynamic job count based on current system load"""
        base_jobs = self.get_optimal_job_count()
        
        if current_load is None:
            try:
                current_load = psutil.cpu_percent(interval=0.1)
            except:
                current_load = 50  # Assume moderate load
        
        # Reduce jobs if system is under high load
        if current_load > 80:
            return max(1, base_jobs // 2)
        elif current_load > 60:
            return max(1, int(base_jobs * 0.75))
        else:
            return base_jobs
    
    def get_memory_efficient_job_count(self, project_count):
        """Optimize job count based on number of projects to avoid memory issues"""
        base_jobs = self.get_optimal_job_count()
        
        # Check if we're in CI environment (be more aggressive)
        is_ci = any(var in os.environ for var in ['CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS_URL', 'BUILDKITE'])
        
        if is_ci:
            # In CI, be more aggressive with large builds
            if project_count > 100:
                return min(base_jobs, 4)  # Still conservative but higher than local
            elif project_count > 50:
                return min(base_jobs, 6)  # More aggressive for medium builds
            else:
                return base_jobs  # Full parallelism for small builds
        else:
            # Local development, more conservative
            if project_count > 100:
                return min(base_jobs, 2)  # Very conservative for large builds
            elif project_count > 50:
                return min(base_jobs, 3)  # Moderate for medium builds
            else:
                return base_jobs  # Full parallelism for small builds
    
    def get_adaptive_job_count(self, project_count=None, current_load=None):
        """Get the most appropriate job count considering all factors"""
        memory_jobs = self.get_memory_efficient_job_count(project_count) if project_count else self.get_optimal_job_count()
        dynamic_jobs = self.get_dynamic_job_count(current_load)
        
        # Use the most conservative estimate
        return min(memory_jobs, dynamic_jobs)
    
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
