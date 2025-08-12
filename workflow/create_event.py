#!/usr/bin/env python3
"""
FOCAL - Fantastical OpenAI Calendar Alfred Linker
Simple, straightforward calendar event creation.
"""

import sys
import os
import subprocess
from datetime import datetime, timedelta

def get_api_key():
    """Get OpenAI API key from .openai_key file."""
    key_file = os.path.join(os.path.dirname(__file__), '.openai_key')
    try:
        with open(key_file, 'r') as f:
            return f.read().strip()
    except (FileNotFoundError, IOError):
        return None

def create_prompt(user_input):
    """Create prompt for OpenAI to generate AppleScript."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%A, %B %d")
    
    return f"""Convert this natural language request into an AppleScript command for Fantastical.

RULES:
- For one-time events: "[Title] on [Day], [Full Date] at [Time] at [Location]"
- For recurring events: Keep patterns like "every Monday", "weekly", "monthly"
- Use 12-hour format (2 pm, not 14:00)
- End with "with add immediately"

Today is {today}
Tomorrow is {tomorrow}

Request: "{user_input}"

Return ONLY the AppleScript:
tell application "Fantastical"
  parse sentence "[your formatted event]" with add immediately
end tell"""

def call_openai(prompt, api_key):
    """Call OpenAI API to generate AppleScript."""
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at formatting calendar events for Fantastical."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return None

def execute_applescript(applescript):
    """Execute the AppleScript to create event in Fantastical."""
    try:
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return False

def sanitize_input(text):
    """Basic input sanitization to prevent injection attacks."""
    # Limit length
    if len(text) > 500:
        text = text[:500]
    # Remove potentially dangerous characters
    text = text.replace('\\', '').replace('"', "'")
    return text.strip()

def main():
    if len(sys.argv) < 2:
        print("Error: No event description provided")
        sys.exit(1)
    
    user_input = sanitize_input(sys.argv[1])
    
    if not user_input:
        print("Error: Invalid event description")
        sys.exit(1)
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("Error: OpenAI API key not found in .openai_key file")
        sys.exit(1)
    
    # Generate AppleScript using OpenAI
    prompt = create_prompt(user_input)
    applescript = call_openai(prompt, api_key)
    
    if not applescript:
        print("Error: Failed to generate event with OpenAI")
        sys.exit(1)
    
    # Execute AppleScript
    if execute_applescript(applescript):
        print("Event created successfully!")
    else:
        print("Error: Failed to create event in Fantastical")
        sys.exit(1)

if __name__ == "__main__":
    main()