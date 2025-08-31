#!/usr/bin/env python3
"""Get list of available calendars from Apple Calendar."""

import subprocess
import os
import sys

def get_available_calendars():
    """Get list of calendars from Apple Calendar."""
    script_path = os.path.join(os.path.dirname(__file__), 'get_calendars.applescript')
    
    try:
        result = subprocess.run(
            ['osascript', script_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Parse the output - AppleScript returns as comma-separated list
            output = result.stdout.strip()
            if output:
                # Clean up the AppleScript list format
                calendars = [cal.strip() for cal in output.split(',')]
                return calendars
        return []
    except Exception as e:
        print(f"Error getting calendars: {e}", file=sys.stderr)
        return []

if __name__ == "__main__":
    calendars = get_available_calendars()
    for cal in calendars:
        print(cal)