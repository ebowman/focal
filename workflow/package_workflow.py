#!/usr/bin/env python3
"""
AI-powered packaging script for FOCAL Alfred workflow with dynamic versioning.
"""

import os
import sys
import zipfile
import shutil
import json
from pathlib import Path
from datetime import datetime

def get_version():
    """Get version from info.plist or git tags."""
    workflow_dir = Path(__file__).parent
    info_plist = workflow_dir / 'info.plist'
    
    try:
        # Read version from info.plist
        if info_plist.exists():
            content = info_plist.read_text()
            import re
            # Look for <key>version</key> followed by <string>X.Y.Z</string>
            version_match = re.search(r'<key>version</key>\s*<string>([^<]+)</string>', content)
            if version_match:
                version = version_match.group(1)
                if version != "{{VERSION}}":  # Not a template
                    return version
        
        # Fallback to git tags
        import subprocess
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True, text=True, check=True
        )
        tag = result.stdout.strip()
        version_match = re.search(r'(\d+\.\d+\.\d+)', tag)
        return version_match.group(1) if version_match else "1.0.0"
        
    except Exception as e:
        print(f"Warning: Could not determine version: {e}")
        return "1.0.0"

def process_template_file(src_path, dest_path, version):
    """Process template files by replacing {{VERSION}} placeholder."""
    content = src_path.read_text(encoding='utf-8')
    content = content.replace('{{VERSION}}', version)
    dest_path.write_text(content, encoding='utf-8')

def package_workflow():
    workflow_dir = Path(__file__).parent
    dist_dir = workflow_dir.parent / 'dist'
    build_dir = workflow_dir / 'build'
    
    # Get dynamic version
    version = get_version()
    print(f"📦 Building FOCAL v{version}")
    
    # Clean and create directories
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    dist_dir.mkdir(exist_ok=True)
    
    # Files to include
    files = [
        'info.plist',
        'create_event.py',
        'configure.py',
        '.openai_key',
        '.calendar_app',
        'icon.png',
    ]
    
    # Copy files 
    for filename in files:
        src = workflow_dir / filename
        dest = build_dir / filename
        if src.exists():
            shutil.copy2(src, dest)
            print(f"  ✓ {filename}")
    
    # Copy venv if it exists
    venv_dir = workflow_dir / 'venv'
    if venv_dir.exists():
        print("  📦 Copying Python environment...")
        shutil.copytree(venv_dir, build_dir / 'venv', symlinks=True)
    
    # Create workflow package with version
    package_name = f"FOCAL_v{version}.alfredworkflow"
    package_path = dist_dir / package_name
    
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in build_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(build_dir)
                zipf.write(file_path, arcname)
    
    # Clean up build directory
    shutil.rmtree(build_dir)
    
    print(f"\n✅ Package created: {package_path}")
    print(f"   Size: {package_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    return str(package_path)

if __name__ == "__main__":
    try:
        package_workflow()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)