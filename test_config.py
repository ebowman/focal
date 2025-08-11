#!/usr/bin/env python3
"""Test the updated configuration system."""

import sys
import os
from pathlib import Path

# Add workflow directory to path
sys.path.insert(0, str(Path(__file__).parent / 'workflow'))

def test_config():
    """Test the configuration system."""
    print("Testing File-Based Configuration System")
    print("=" * 50)
    
    # Test 1: Check if config module can be imported
    try:
        import config
        print("✅ Config module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import config module: {e}")
        return False
    
    # Test 2: Check API key file location
    config_file = Path(__file__).parent / 'workflow' / 'openai_key.txt'
    print(f"\nChecking for API key file at: {config_file}")
    
    if config_file.exists():
        print(f"✅ API key file exists")
        
        # Check file permissions
        import stat
        file_stat = os.stat(config_file)
        file_mode = stat.filemode(file_stat.st_mode)
        print(f"   File permissions: {file_mode}")
        
        # Check if it's readable
        try:
            with open(config_file, 'r') as f:
                content = f.read().strip()
                if content.startswith('sk-'):
                    print(f"✅ API key format looks valid (starts with 'sk-')")
                else:
                    print(f"⚠️  API key doesn't start with 'sk-'")
        except Exception as e:
            print(f"❌ Could not read API key file: {e}")
    else:
        print(f"⚠️  API key file does not exist")
        print(f"   Create it with: echo 'your-api-key' > {config_file}")
    
    # Test 3: Test get_api_key function
    print("\nTesting get_api_key() function...")
    try:
        api_key = config.get_api_key()
        print(f"✅ Successfully retrieved API key")
        print(f"   Key starts with: {api_key[:7]}...")
        print(f"   Key length: {len(api_key)} characters")
    except ValueError as e:
        print(f"⚠️  get_api_key() raised ValueError (expected if no key set):")
        print(f"   {str(e).split('Please')[0].strip()}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test 4: Test save_api_key function
    print("\nTesting save_api_key() function...")
    try:
        test_key = "sk-test-key-for-validation-only"
        saved_path = config.save_api_key(test_key)
        print(f"✅ save_api_key() executed successfully")
        print(f"   Saved to: {saved_path}")
        
        # Verify it was saved correctly
        retrieved_key = config.get_api_key()
        if retrieved_key == test_key:
            print(f"✅ Key was saved and retrieved correctly")
        else:
            print(f"❌ Retrieved key doesn't match saved key")
    except Exception as e:
        print(f"⚠️  Could not test save_api_key: {e}")
    
    print("\n" + "=" * 50)
    print("Configuration test complete!")
    print("\nNext steps:")
    print("1. Set your real API key: python3 workflow/setup_config.py")
    print("2. Package the workflow: python3 package_workflow.py")
    print("3. Install in Alfred and start using!")

if __name__ == "__main__":
    test_config()