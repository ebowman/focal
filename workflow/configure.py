#!/usr/bin/env python3
"""
FOCAL Configuration Script
Simple setup for API key and calendar app preference.
"""

import os
import sys

def main():
    print("🔧 FOCAL Configuration")
    print("=====================")
    print()
    
    workflow_dir = os.path.dirname(__file__)
    
    # Configure OpenAI API Key
    print("1. OpenAI API Key Setup:")
    api_key_file = os.path.join(workflow_dir, '.openai_key')
    
    if os.path.exists(api_key_file):
        with open(api_key_file, 'r') as f:
            existing_key = f.read().strip()
        if existing_key and not existing_key.startswith('sk-'):
            print("   ⚠️  Invalid API key format found")
        elif existing_key:
            print(f"   ✅ API key configured: {existing_key[:10]}...")
            update_key = input("   Update API key? (y/N): ").lower().strip()
            if update_key != 'y':
                existing_key = None  # Skip key update
        else:
            existing_key = None
    else:
        existing_key = None
    
    if existing_key is None:
        print("   📝 Get your API key from: https://platform.openai.com/api-keys")
        api_key = input("   Enter your OpenAI API key: ").strip()
        
        if not api_key.startswith('sk-'):
            print("   ❌ Invalid API key format (should start with 'sk-')")
            sys.exit(1)
        
        with open(api_key_file, 'w') as f:
            f.write(api_key)
        print("   ✅ API key saved")
    
    print()
    
    # Configure Calendar App
    print("2. Calendar App Preference:")
    calendar_file = os.path.join(workflow_dir, '.calendar_app')
    
    current_app = 'calendar'  # default
    if os.path.exists(calendar_file):
        with open(calendar_file, 'r') as f:
            current_app = f.read().strip().lower()
    
    print(f"   Current: {'Fantastical' if current_app == 'fantastical' else 'Apple Calendar'}")
    print("   Options:")
    print("   1. Apple Calendar (default, structured)")
    print("   2. Fantastical (natural language)")
    
    choice = input("   Choose calendar app (1/2): ").strip()
    
    if choice == '2':
        calendar_app = 'fantastical'
        print("   ✅ Using Fantastical")
    else:
        calendar_app = 'calendar'
        print("   ✅ Using Apple Calendar")
    
    with open(calendar_file, 'w') as f:
        f.write(calendar_app)
    
    print()
    print("🎉 Configuration complete!")
    print("   You can now use FOCAL with Alfred: 'focal [your event]'")

if __name__ == "__main__":
    main()