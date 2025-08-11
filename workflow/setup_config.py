#!/usr/bin/env python3
"""Interactive setup script for OpenAI API key configuration.

This script provides a simple way to configure your OpenAI API key
for the Fantastical Alfred workflow.
"""

import os
import sys
from pathlib import Path
from getpass import getpass

def validate_api_key(api_key):
    """Validate the format of an OpenAI API key.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not api_key:
        return False
    
    # OpenAI keys typically start with 'sk-'
    if not api_key.startswith('sk-'):
        return False
    
    # Basic length check
    if len(api_key) < 20:
        return False
    
    return True

def main():
    """Main setup function."""
    print("=" * 60)
    print("Fantastical Alfred Workflow - OpenAI API Key Setup")
    print("=" * 60)
    print()
    
    # Determine config file path
    config_file = Path(__file__).parent / 'openai_key.txt'
    
    # Check if key already exists
    if config_file.exists():
        print(f"⚠️  API key file already exists at:")
        print(f"   {config_file}")
        print()
        response = input("Do you want to replace it? (y/n): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            return
        print()
    
    # Get API key from user
    print("Please enter your OpenAI API key.")
    print("(Get one from: https://platform.openai.com/api-keys)")
    print()
    print("Note: The key will be hidden as you type for security.")
    print()
    
    while True:
        api_key = getpass("OpenAI API Key: ").strip()
        
        if not api_key:
            print("❌ No key entered. Please try again.")
            continue
        
        if not validate_api_key(api_key):
            print("❌ Invalid API key format.")
            print("   OpenAI keys should start with 'sk-' and be at least 20 characters.")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                print("Setup cancelled.")
                return
            continue
        
        break
    
    # Save the API key
    try:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(api_key)
        
        # Set restrictive permissions (owner read/write only)
        os.chmod(config_file, 0o600)
        
        print()
        print("✅ API key saved successfully!")
        print(f"   Location: {config_file}")
        print()
        print("The workflow is now ready to use!")
        print("Try it in Alfred with: cal [your event description]")
        print()
        
        # Test the configuration
        print("Testing configuration...")
        try:
            # Import after saving to test
            import config
            test_key = config.get_api_key()
            if test_key == api_key:
                print("✅ Configuration test passed!")
            else:
                print("⚠️  Configuration test returned different key.")
        except Exception as e:
            print(f"⚠️  Configuration test failed: {e}")
            print("   Please check the setup manually.")
    
    except Exception as e:
        print(f"❌ Failed to save API key: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()