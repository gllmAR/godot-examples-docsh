#!/usr/bin/env python3
"""
Godot Version Configuration
==========================

Configuration for different Godot versions and their compatibility.
"""

SUPPORTED_VERSIONS = {
    "4.5-beta1": {
        "stable": "4.5-beta1",
        "template": "4.5.beta1",
        "download_urls": {
            "linux": "https://github.com/godotengine/godot-builds/releases/download/4.5-beta1/Godot_v4.5-beta1_linux.x86_64.zip",
            "macos": "https://github.com/godotengine/godot-builds/releases/download/4.5-beta1/Godot_v4.5-beta1_macos.universal.zip",
            "windows": "https://github.com/godotengine/godot-builds/releases/download/4.5-beta1/Godot_v4.5-beta1_win64.exe.zip",
            "templates": "https://github.com/godotengine/godot-builds/releases/download/4.5-beta1/Godot_v4.5-beta1_export_templates.tpz"
        },
        "features": ["web_export", "headless", "c_sharp"],
        "recommended": False
    },
    "4.4.1": {
        "stable": "4.4.1-stable",
        "template": "4.4.1.stable",
        "download_urls": {
            "linux": "https://github.com/godotengine/godot-builds/releases/download/4.4.1-stable/Godot_v4.4.1-stable_linux.x86_64.zip",
            "macos": "https://github.com/godotengine/godot-builds/releases/download/4.4.1-stable/Godot_v4.4.1-stable_macos.universal.zip",
            "windows": "https://github.com/godotengine/godot-builds/releases/download/4.4.1-stable/Godot_v4.4.1-stable_win64.exe.zip",
            "templates": "https://github.com/godotengine/godot-builds/releases/download/4.4.1-stable/Godot_v4.4.1-stable_export_templates.tpz"
        },
        "features": ["web_export", "headless", "c_sharp"],
        "recommended": True
    },
    "4.3": {
        "stable": "4.3-stable",
        "template": "4.3.stable",
        "download_urls": {
            "linux": "https://github.com/godotengine/godot-builds/releases/download/4.3-stable/Godot_v4.3-stable_linux.x86_64.zip",
            "macos": "https://github.com/godotengine/godot-builds/releases/download/4.3-stable/Godot_v4.3-stable_macos.universal.zip",
            "windows": "https://github.com/godotengine/godot-builds/releases/download/4.3-stable/Godot_v4.3-stable_win64.exe.zip",
            "templates": "https://github.com/godotengine/godot-builds/releases/download/4.3-stable/Godot_v4.3-stable_export_templates.tpz"
        },
        "features": ["web_export", "headless"],
        "recommended": False
    },
    "4.2": {
        "stable": "4.2-stable",
        "template": "4.2.stable",
        "download_urls": {
            "linux": "https://github.com/godotengine/godot-builds/releases/download/4.2-stable/Godot_v4.2-stable_linux.x86_64.zip",
            "macos": "https://github.com/godotengine/godot-builds/releases/download/4.2-stable/Godot_v4.2-stable_macos.universal.zip",
            "windows": "https://github.com/godotengine/godot-builds/releases/download/4.2-stable/Godot_v4.2-stable_win64.exe.zip",
            "templates": "https://github.com/godotengine/godot-builds/releases/download/4.2-stable/Godot_v4.2-stable_export_templates.tpz"
        },
        "features": ["web_export", "headless"],
        "recommended": False
    }
}

# Default version for new projects
DEFAULT_VERSION = "4.4.1"

# Minimum supported version
MIN_VERSION = "4.2"

def get_version_info(version: str) -> dict:
    """Get version information for a specific Godot version"""
    return SUPPORTED_VERSIONS.get(version, {})

def get_recommended_version() -> str:
    """Get the recommended Godot version"""
    for version, info in SUPPORTED_VERSIONS.items():
        if info.get("recommended", False):
            return version
    return DEFAULT_VERSION

def is_version_supported(version: str) -> bool:
    """Check if a Godot version is supported"""
    return version in SUPPORTED_VERSIONS

def get_download_url(version: str, platform: str) -> str:
    """Get download URL for a specific version and platform"""
    version_info = get_version_info(version)
    return version_info.get("download_urls", {}).get(platform, "")

def validate_version_string(version_str: str) -> tuple:
    """Validate and parse a version string"""
    import re
    
    # Extract version number (e.g., "4.4.1.stable.official" -> "4.4.1")
    version_match = re.match(r'(\d+)\.(\d+)\.(\d+)', version_str)
    if not version_match:
        return None, None, None
    
    return tuple(map(int, version_match.groups()))

def compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings. Returns -1, 0, or 1"""
    v1_parts = validate_version_string(version1)
    v2_parts = validate_version_string(version2)
    
    if v1_parts[0] is None or v2_parts[0] is None:
        return 0
    
    if v1_parts < v2_parts:
        return -1
    elif v1_parts > v2_parts:
        return 1
    else:
        return 0
