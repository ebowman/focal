#!/usr/bin/env python3
"""
Simple packaging script for FOCAL Alfred workflow.
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
from datetime import datetime

def package_workflow():
    workflow_dir = Path(__file__).parent
    dist_dir = workflow_dir.parent / 'dist'
    build_dir = workflow_dir / 'build'
    
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
        if src.exists():
            shutil.copy2(src, build_dir / filename)
            print(f"  ✓ {filename}")
    
    # Copy venv if it exists
    venv_dir = workflow_dir / 'venv'
    if venv_dir.exists():
        print("  📦 Copying Python environment...")
        shutil.copytree(venv_dir, build_dir / 'venv', symlinks=True)
    
    # Create workflow package
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"FOCAL_{timestamp}.alfredworkflow"
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