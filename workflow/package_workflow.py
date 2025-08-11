#!/usr/bin/env python3
"""
Package the Fantastical Calendar Events workflow into an .alfredworkflow file.
"""

import os
import sys
import zipfile
import shutil
import json
from pathlib import Path
from datetime import datetime

class WorkflowPackager:
    """Package Alfred workflow for distribution."""
    
    def __init__(self):
        self.workflow_dir = Path(__file__).parent
        self.build_dir = self.workflow_dir / 'build'
        self.dist_dir = self.workflow_dir.parent / 'dist'
        
    def package_workflow(self) -> str:
        """Package the workflow into an .alfredworkflow file."""
        print("📦 Packaging Fantastical Calendar Events Alfred Workflow...")
        
        # Clean and create build directories
        self._prepare_directories()
        
        # Copy workflow files to build directory
        self._copy_workflow_files()
        
        # Create the .alfredworkflow file
        workflow_file = self._create_workflow_package()
        
        print(f"✅ Workflow packaged successfully: {workflow_file}")
        return workflow_file
    
    def _prepare_directories(self):
        """Prepare build and distribution directories."""
        # Clean build directory
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        self.build_dir.mkdir(parents=True)
        
        # Create dist directory
        self.dist_dir.mkdir(exist_ok=True)
        
        print(f"📁 Build directory: {self.build_dir}")
        print(f"📁 Distribution directory: {self.dist_dir}")
    
    def _copy_workflow_files(self):
        """Copy necessary workflow files to build directory."""
        
        # Essential workflow files
        essential_files = [
            'info.plist',
            'main.py',
            'create_event.py',
            'error_handler.py',
            'prompt_engine.py',
            'setup_config.py',
            'config.py.template',
            'requirements.txt',
        ]
        
        # Optional files (copy if they exist)
        optional_files = [
            'icon.png',
            'README.txt',
        ]
        
        # Copy essential files
        for filename in essential_files:
            src_file = self.workflow_dir / filename
            if src_file.exists():
                shutil.copy2(src_file, self.build_dir / filename)
                print(f"  ✓ Copied {filename}")
            else:
                print(f"  ⚠️ Missing essential file: {filename}")
        
        # Copy optional files
        for filename in optional_files:
            src_file = self.workflow_dir / filename
            if src_file.exists():
                shutil.copy2(src_file, self.build_dir / filename)
                print(f"  ✓ Copied {filename}")
            else:
                print(f"  - Optional file not found: {filename}")
        
        # Create a default icon if none exists
        if not (self.build_dir / 'icon.png').exists():
            self._create_default_icon()
        
        # Create README if it doesn't exist
        if not (self.build_dir / 'README.txt').exists():
            self._create_readme()
    
    def _create_default_icon(self):
        """Create a simple default icon placeholder."""
        # For now, just create a text file indicating an icon is needed
        icon_placeholder = self.build_dir / 'icon_needed.txt'
        with open(icon_placeholder, 'w') as f:
            f.write("A workflow icon (icon.png) should be created for the final release.")
        print("  📝 Created icon placeholder")
    
    def _create_readme(self):
        """Create a README file for the workflow."""
        readme_content = """Fantastical Calendar Events (OpenAI-Powered) - Alfred Workflow

OVERVIEW
This workflow allows you to create calendar events in Fantastical using natural language, powered by OpenAI for reliable parsing.

SETUP
1. Install this workflow by double-clicking the .alfredworkflow file
2. Set up your OpenAI API key:
   - Option A: Set environment variable OPENAI_API_KEY
   - Option B: Run python3 setup_config.py in the workflow directory
   - Option C: Manually create config.py from config.py.template
3. Make sure Fantastical is installed and running

USAGE
- Keyword: cal
- Example: "cal Lunch with Anna tomorrow at noon"
- Example: "cal Team meeting next Tuesday at 2pm in Conference Room A"

The AI will normalize your input into Fantastical's preferred format for reliable event creation.

FEATURES
- OpenAI-powered natural language processing
- Fallback parsing when API is unavailable
- Comprehensive error handling
- Real-time feedback
- Secure API key management

REQUIREMENTS
- macOS with Alfred (Powerpack required)
- Fantastical app
- OpenAI API key
- Python 3.x with openai package

For support or issues, check the workflow logs in ~/Library/Logs/alfred-fantastical.log
"""
        
        readme_file = self.build_dir / 'README.txt'
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        print("  📝 Created README.txt")
    
    def _create_workflow_package(self) -> str:
        """Create the .alfredworkflow zip file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workflow_filename = f"Fantastical_Calendar_Events_OpenAI_{timestamp}.alfredworkflow"
        workflow_path = self.dist_dir / workflow_filename
        
        # Create zip file with all workflow contents
        with zipfile.ZipFile(workflow_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.build_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.build_dir)
                    zipf.write(file_path, arcname)
                    print(f"  📄 Added to package: {arcname}")
        
        # Verify the package
        self._verify_package(workflow_path)
        
        return str(workflow_path)
    
    def _verify_package(self, workflow_path: Path):
        """Verify the created workflow package."""
        print(f"\n🔍 Verifying workflow package...")
        
        with zipfile.ZipFile(workflow_path, 'r') as zipf:
            file_list = zipf.namelist()
            
            # Check for essential files
            essential_files = ['info.plist', 'main.py', 'create_event.py']
            missing_files = []
            
            for essential_file in essential_files:
                if essential_file not in file_list:
                    missing_files.append(essential_file)
            
            if missing_files:
                print(f"  ❌ Missing essential files: {missing_files}")
                return False
            
            print(f"  ✅ Package contains {len(file_list)} files")
            print(f"  ✅ All essential files present")
            print(f"  ✅ Package size: {workflow_path.stat().st_size / 1024:.1f} KB")
            
            return True
    
    def create_installation_guide(self) -> str:
        """Create a detailed installation guide."""
        guide_content = """# Fantastical Calendar Events (OpenAI) - Installation Guide

## Quick Installation

1. **Download** the .alfredworkflow file
2. **Double-click** the file to install in Alfred
3. **Set up your OpenAI API key** (see below)
4. **Test** with keyword `cal` followed by an event description

## OpenAI API Key Setup

You have three options to configure your API key:

### Option 1: Environment Variable (Recommended)
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```
Add this to your `~/.zshrc` or `~/.bash_profile` for persistence.

### Option 2: Interactive Setup
1. Navigate to the workflow directory in Alfred preferences
2. Run: `python3 setup_config.py`
3. Follow the prompts

### Option 3: Manual Configuration
1. Navigate to the workflow directory
2. Copy `config.py.template` to `config.py`
3. Edit `config.py` and add your API key
4. Save the file

## Get Your OpenAI API Key

1. Visit https://platform.openai.com/api-keys
2. Sign in or create an account
3. Create a new API key
4. Copy the key (starts with 'sk-')

## Requirements

- **Alfred Powerpack** (required for workflows)
- **Fantastical** app installed
- **OpenAI API key** with available credits
- **Python 3** with `openai` package

To install the required Python package:
```bash
pip3 install openai
```

## Usage Examples

- `cal Lunch tomorrow at noon`
- `cal Team meeting next Tuesday at 2pm`
- `cal Coffee with Sarah at Starbucks Friday at 10am`
- `cal Doctor appointment next Monday at 9:30am`

## Troubleshooting

### "No API key found"
- Check your API key configuration using one of the three methods above
- Verify the key is valid at https://platform.openai.com/api-keys

### "Fantastical not found"
- Install Fantastical from the App Store
- Make sure Fantastical is running

### "OpenAI library not installed"
```bash
pip3 install openai
```

### General Issues
- Check logs: `~/Library/Logs/alfred-fantastical.log`
- Run workflow tests: `python3 test_workflow.py`
- Verify system: `python3 setup_config.py`

## Support

For issues or questions:
1. Check the log file for error details
2. Run the test suite to diagnose problems
3. Verify all requirements are met
4. Check that your API key has available credits

Enjoy creating calendar events with natural language! 🗓️
"""
        
        guide_file = self.dist_dir / 'INSTALLATION_GUIDE.md'
        with open(guide_file, 'w') as f:
            f.write(guide_content)
        
        print(f"📖 Created installation guide: {guide_file}")
        return str(guide_file)

def main():
    """Package the workflow."""
    packager = WorkflowPackager()
    
    try:
        # Package the workflow
        workflow_file = packager.package_workflow()
        
        # Create installation guide
        guide_file = packager.create_installation_guide()
        
        print(f"\n🎉 Packaging Complete!")
        print(f"📦 Workflow file: {workflow_file}")
        print(f"📖 Installation guide: {guide_file}")
        print(f"\nThe workflow is ready for distribution and installation!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error packaging workflow: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())