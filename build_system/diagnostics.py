#!/usr/bin/env python3
"""
Godot Build System Diagnostics
=============================

This script helps diagnose common issues with the Godot build system.
"""

import os
import sys
import subprocess
import resource
import psutil
from pathlib import Path


def check_godot_binary():
    """Check if Godot binary is available and working"""
    print("🔍 Checking Godot binary...")
    
    try:
        result = subprocess.run(
            ["godot", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ Godot found: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Godot error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Godot binary not found in PATH")
        return False
    except Exception as e:
        print(f"❌ Godot check failed: {e}")
        return False


def check_system_resources():
    """Check system resources and limits"""
    print("\n💻 Checking system resources...")
    
    # CPU and Memory
    cpu_count = os.cpu_count()
    memory = psutil.virtual_memory()
    
    print(f"   CPU cores: {cpu_count}")
    print(f"   Total memory: {memory.total / (1024**3):.1f}GB")
    print(f"   Available memory: {memory.available / (1024**3):.1f}GB")
    print(f"   Memory usage: {memory.percent}%")
    
    # File descriptor limits
    try:
        soft_fd, hard_fd = resource.getrlimit(resource.RLIMIT_NOFILE)
        print(f"   File descriptor limit: {soft_fd} (soft) / {hard_fd} (hard)")
        
        if soft_fd < 1024:
            print("   ⚠️  Low file descriptor limit, consider: ulimit -n 4096")
    except:
        print("   ❌ Could not check file descriptor limits")
    
    # Process limits
    try:
        soft_proc, hard_proc = resource.getrlimit(resource.RLIMIT_NPROC)
        print(f"   Process limit: {soft_proc} (soft) / {hard_proc} (hard)")
    except:
        print("   ❌ Could not check process limits")


def check_git_repository():
    """Check git repository status"""
    print("\n📂 Checking git repository...")
    
    try:
        # Check if we're in a git repo
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("❌ Not in a git repository")
            return False
        
        print("✅ Git repository detected")
        
        # Check HEAD~1 reference
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD~1"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ HEAD~1 reference available")
        else:
            print("⚠️  HEAD~1 not available (single commit repo)")
        
        return True
        
    except Exception as e:
        print(f"❌ Git check failed: {e}")
        return False


def check_project_structure():
    """Check project structure"""
    print("\n📁 Checking project structure...")
    
    godot_projects = Path("godot-demo-projects")
    if godot_projects.exists():
        project_count = len(list(godot_projects.rglob("project.godot")))
        print(f"✅ Found {project_count} Godot projects")
        
        if project_count > 100:
            print("   ℹ️  Large build - consider using --jobs 2-4 for stability")
        
        return True
    else:
        print("❌ godot-demo-projects directory not found")
        return False


def recommend_job_count():
    """Recommend optimal job count"""
    print("\n⚡ Job count recommendations...")
    
    try:
        sys.path.append("build_system")
        from tools.parallel_manager import ParallelManager
        
        pm = ParallelManager()
        optimal = pm.get_optimal_job_count()
        memory_efficient = pm.get_memory_efficient_job_count(121)  # Assume 121 projects
        
        print(f"   Optimal jobs (general): {optimal}")
        print(f"   Memory efficient (121 projects): {memory_efficient}")
        print(f"   Recommendation: Use --jobs {memory_efficient}")
        
        if memory_efficient < optimal:
            print("   ℹ️  Conservative setting due to large project count")
            
    except Exception as e:
        print(f"   ❌ Could not calculate recommendations: {e}")


def test_single_export():
    """Test exporting a single project"""
    print("\n🎮 Testing single project export...")
    
    pong_path = Path("godot-demo-projects/2d/pong")
    if not pong_path.exists():
        print("❌ Pong project not found for testing")
        return False
    
    try:
        sys.path.append("build_system")
        from tools.godot_exporter import GodotExporter
        
        exporter = GodotExporter()
        result = exporter.export_project_with_retry(pong_path, max_retries=1)
        
        if result.success:
            print("✅ Single export test successful")
            return True
        else:
            print(f"❌ Single export test failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Export test failed: {e}")
        return False


def main():
    """Run all diagnostic checks"""
    print("🏗️ Godot Build System Diagnostics")
    print("=" * 40)
    
    checks = [
        check_godot_binary,
        check_system_resources,
        check_git_repository,
        check_project_structure,
        recommend_job_count,
        test_single_export
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Check failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print(f"📊 Summary: {sum(r for r in results if r is not None)}/{len([r for r in results if r is not None])} checks passed")
    
    if all(r is not False for r in results):
        print("✅ System appears ready for building!")
    else:
        print("⚠️  Some issues detected. Review the output above.")


if __name__ == "__main__":
    main()
