#!/usr/bin/env python3
"""
Alfred Script Filter for Fantastical Calendar Events
Provides real-time feedback as user types their event description.
"""

import sys
import json
import os

def create_alfred_items(query):
    """Create Alfred script filter JSON response."""
    items = []
    
    if not query or len(query.strip()) < 3:
        items.append({
            "uid": "help",
            "title": "Enter your event description...",
            "subtitle": "e.g., 'Lunch with Anna tomorrow at noon' or 'Team meeting next Tuesday at 2pm'",
            "arg": "",
            "valid": False,
            "icon": {
                "path": "icon.png"
            }
        })
    else:
        items.append({
            "uid": "create_event",
            "title": f"Create Event: {query}",
            "subtitle": "Press Enter to create calendar event using AI-powered natural language processing",
            "arg": query,  # This passes the actual query text
            "valid": True,
            "icon": {
                "path": "icon.png"
            }
        })
        
        # Show example of what AI might generate
        items.append({
            "uid": "preview",
            "title": "AI will normalize your input for Fantastical",
            "subtitle": "Example: 'Lunch with Anna on Tuesday, August 12 at 12 pm' for reliable parsing",
            "arg": "",
            "valid": False,
            "icon": {
                "path": "icon.png"
            }
        })
    
    return {"items": items}

def main():
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    result = create_alfred_items(query)
    print(json.dumps(result))

if __name__ == "__main__":
    main()