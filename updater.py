"""
CAD Translator - Auto-Update Module
====================================
Checks cloud version.json and compares with local version.
Supports GitHub Releases as update source.

Usage:
    from updater import check_for_updates, UpdateInfo
    info = check_for_updates()
    if info.update_available:
        print(f"New version {info.latest_version} available!")
"""
import json
import os
import re
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_PATH = os.path.join(BASE_DIR, "version.json")


def get_local_version() -> dict:
    """Read local version.json."""
    try:
        with open(VERSION_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"version": "0.0.0", "build": 0}


def parse_version(v: str) -> tuple:
    """Parse version string '2.0.0' into tuple (2, 0, 0)."""
    try:
        parts = re.findall(r'\d+', v)
        return tuple(int(p) for p in parts[:3])
    except Exception:
        return (0, 0, 0)


def check_for_updates(timeout: int = 10) -> dict:
    """Check for available updates from cloud.
    
    Returns:
        {
            "update_available": bool,
            "local_version": str,
            "latest_version": str,
            "local_build": int,
            "latest_build": int,
            "release_notes": str,
            "download_url": str,
            "error": str or None,
        }
    """
    local = get_local_version()
    result = {
        "update_available": False,
        "local_version": local.get("version", "0.0.0"),
        "latest_version": local.get("version", "0.0.0"),
        "local_build": local.get("build", 0),
        "latest_build": local.get("build", 0),
        "release_notes": "",
        "download_url": "",
        "error": None,
    }
    
    update_url = local.get("update_url", "")
    if not update_url:
        result["error"] = "No update URL configured"
        return result
    
    try:
        resp = requests.get(update_url, timeout=timeout)
        resp.raise_for_status()
        remote = resp.json()
    except Exception as e:
        result["error"] = f"Failed to fetch update info: {e}"
        return result
    
    remote_ver = remote.get("version", "0.0.0")
    remote_build = remote.get("build", 0)
    local_ver = result["local_version"]
    local_build = result["local_build"]
    
    result["latest_version"] = remote_ver
    result["latest_build"] = remote_build
    result["release_notes"] = remote.get("release_notes", "")
    result["download_url"] = remote.get("download_url", "")
    
    # Compare versions
    if parse_version(remote_ver) > parse_version(local_ver):
        result["update_available"] = True
    elif parse_version(remote_ver) == parse_version(local_ver) and remote_build > local_build:
        result["update_available"] = True
    
    return result


# API endpoint helper
def get_update_api_handler():
    """Return a Flask route handler for update checking."""
    from flask import jsonify
    def handler():
        info = check_for_updates()
        return jsonify(info)
    return handler
