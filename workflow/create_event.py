#!/usr/bin/env python3
"""
FOCAL - Fantastical OpenAI Calendar Alfred Linker
Simple, straightforward calendar event creation.
"""

import sys
import os
import subprocess
import logging
import json
import argparse
from datetime import datetime
from urllib.parse import urlencode, quote
from extraction import create_extraction_prompt, extract_event_data

def setup_logging(debug=False):
    """Setup detailed logging for debugging."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

def get_api_key():
    """Get OpenAI API key from .openai_key file."""
    key_file = os.path.join(os.path.dirname(__file__), '.openai_key')
    try:
        with open(key_file, 'r') as f:
            return f.read().strip()
    except (FileNotFoundError, IOError):
        return None

def get_calendar_app():
    """Get preferred calendar app from config file."""
    config_file = os.path.join(os.path.dirname(__file__), '.calendar_app')
    try:
        with open(config_file, 'r') as f:
            app = f.read().strip().lower()
            return 'fantastical' if app == 'fantastical' else 'calendar'
    except (FileNotFoundError, IOError):
        return 'calendar'  # Default to Apple Calendar

def get_target_calendar():
    """Get target calendar name from config file."""
    config_file = os.path.join(os.path.dirname(__file__), '.target_calendar')
    try:
        with open(config_file, 'r') as f:
            calendar_name = f.read().strip()
            return calendar_name if calendar_name else 'Calendar'
    except (FileNotFoundError, IOError):
        return 'Calendar'  # Default to 'Calendar'

def parse_and_validate_event_data(json_response, logger):
    """Parse and validate the JSON event data from OpenAI."""
    try:
        # Clean up response - remove any markdown code blocks
        if json_response.startswith('```'):
            lines = json_response.split('\n')
            json_response = '\n'.join(lines[1:-1])
        
        event_data = json.loads(json_response)
        logger.info("Successfully parsed JSON response")
        
        # Validate required fields
        required_fields = ['title', 'start_date', 'end_date', 'all_day']
        for field in required_fields:
            if field not in event_data:
                logger.error(f"Missing required field: {field}")
                return None
        
        # Validate all_day field
        if not isinstance(event_data['all_day'], bool):
            logger.error(f"all_day field must be boolean")
            return None
        
        # Validate date formats
        try:
            datetime.strptime(event_data['start_date'], '%Y-%m-%d')
            datetime.strptime(event_data['end_date'], '%Y-%m-%d')
        except ValueError as e:
            logger.error(f"Invalid date format: {str(e)}")
            return None
        
        # Validate time fields based on all_day
        if event_data['all_day']:
            # All-day events should have null times
            if event_data.get('start_time') is not None or event_data.get('end_time') is not None:
                logger.warning("All-day event has time fields, setting to null")
                event_data['start_time'] = None
                event_data['end_time'] = None
        else:
            # Timed events must have valid times
            if not event_data.get('start_time') or not event_data.get('end_time'):
                logger.error("Timed event missing start_time or end_time")
                return None
            try:
                datetime.strptime(event_data['start_time'], '%H:%M')
                datetime.strptime(event_data['end_time'], '%H:%M')
            except ValueError as e:
                logger.error(f"Invalid time format: {str(e)}")
                return None
        
        logger.info("Event data validation successful")
        return event_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {str(e)}")
        logger.debug(f"Raw response: {json_response}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error validating event data: {str(e)}")
        return None

def create_fantastical_url(event_data, user_input, target_calendar, logger):
    """Use Fantastical's explicit fields instead of re-parsing a sentence."""
    try:
        if event_data.get('recurrence'):
            raise ValueError("Recurring events are not supported by Fantastical's structured URL API")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        attribution = f'Created by FOCAL on {timestamp}\nOriginal: "{user_input}"'
        notes = event_data.get('notes')
        params = {
            "title": event_data['title'],
            "start": event_data['start_date'],
            "end": event_data['end_date'],
            "calendarName": target_calendar,
            "notes": f"{notes}\n\n{attribution}" if notes else attribution,
            "add": "1",
        }
        if event_data['all_day']:
            params["allDay"] = "1"
        else:
            params["start"] += f" {event_data['start_time']}"
            params["end"] += f" {event_data['end_time']}"
        if event_data.get('location'):
            params["location"] = event_data['location']
        url = "x-fantastical://parse?" + urlencode(params, quote_via=quote)
        logger.info("Generated structured Fantastical request")
        logger.debug("Fantastical URL: %s", url)
        return url
    except (KeyError, TypeError, ValueError) as error:
        logger.error("Failed to generate Fantastical request: %s", error)
        return None

def execute_fantastical_url(url, logger):
    """Deliver a request; URL dispatch does not acknowledge event persistence."""
    try:
        result = subprocess.run(
            ['/usr/bin/open', '-g', url],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        logger.error("Failed to open Fantastical: %s", error)
        return False
    if result.returncode != 0:
        logger.error("Fantastical URL dispatch failed: %s", result.stderr.strip())
        return False
    return True

def create_calendar_applescript(event_data, user_input, target_calendar, logger):
    """Generate AppleScript for Apple Calendar using structured data."""
    try:
        # Handle null values and add FOCAL attribution
        location = event_data.get('location') or ''
        notes = event_data.get('notes') or ''
        recurrence = event_data.get('recurrence')
        
        # Add FOCAL attribution with timestamp and original instruction
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Escape user input for AppleScript
        escaped_user_input = user_input.replace('"', '\\"').replace('\\', '\\\\')
        focal_attribution = f"Created by FOCAL on {timestamp}\\nOriginal: \"{escaped_user_input}\""
        
        if notes:
            notes = f"{notes}\\n\\n{focal_attribution}"
        else:
            notes = focal_attribution
        
        # Escape quotes in strings for AppleScript
        title = event_data['title'].replace('"', '\\"')
        location = location.replace('"', '\\"')
        notes = notes.replace('"', '\\"')
        calendar_name = target_calendar.replace('"', '\\"')
        
        # Month names for AppleScript (must use constants, not numbers)
        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }
        
        # Parse dates and times for both all-day and timed events
        start_dt = datetime.strptime(event_data['start_date'], "%Y-%m-%d")
        end_dt = datetime.strptime(event_data['end_date'], "%Y-%m-%d")
        
        if event_data['all_day']:
            # All-day events: use dates only
            applescript = f'''tell application "Calendar"
    tell calendar "{calendar_name}"
        set startDate to (current date)
        set year of startDate to {start_dt.year}
        set month of startDate to {month_names[start_dt.month]}
        set day of startDate to {start_dt.day}
        set hours of startDate to 0
        set minutes of startDate to 0
        set seconds of startDate to 0
        
        set endDate to (current date)
        set year of endDate to {end_dt.year}
        set month of endDate to {month_names[end_dt.month]}
        set day of endDate to {end_dt.day}
        set hours of endDate to 0
        set minutes of endDate to 0
        set seconds of endDate to 0
        
        make new event at end with properties {{summary: "{title}", start date: startDate, end date: endDate, allday event: true'''
        else:
            # Timed events: parse dates and times
            start_dt_full = datetime.strptime(f"{event_data['start_date']} {event_data['start_time']}", "%Y-%m-%d %H:%M")
            end_dt_full = datetime.strptime(f"{event_data['end_date']} {event_data['end_time']}", "%Y-%m-%d %H:%M")
            
            applescript = f'''tell application "Calendar"
    tell calendar "{calendar_name}"
        set startDate to (current date)
        set year of startDate to {start_dt_full.year}
        set month of startDate to {month_names[start_dt_full.month]}
        set day of startDate to {start_dt_full.day}
        set hours of startDate to {start_dt_full.hour}
        set minutes of startDate to {start_dt_full.minute}
        set seconds of startDate to 0
        
        set endDate to (current date)
        set year of endDate to {end_dt_full.year}
        set month of endDate to {month_names[end_dt_full.month]}
        set day of endDate to {end_dt_full.day}
        set hours of endDate to {end_dt_full.hour}
        set minutes of endDate to {end_dt_full.minute}
        set seconds of endDate to 0
        
        make new event at end with properties {{summary: "{title}", start date: startDate, end date: endDate'''
        
        if location:
            applescript += f', location: "{location}"'
        
        # Always add notes since we include FOCAL attribution
        applescript += f', description: "{notes}"'
        
        applescript += '}\n    end tell\nend tell'
        
        logger.info("🚀 Generated structured AppleScript for Apple Calendar")
        logger.debug(f"Generated AppleScript: {applescript}")
        
        return applescript
        
    except Exception as e:
        logger.error(f"Failed to generate AppleScript: {str(e)}")
        return None

def execute_applescript(applescript, calendar_app, logger):
    """Execute the AppleScript to create event in the specified calendar app."""
    try:
        app_name = "Fantastical" if calendar_app == "fantastical" else "Apple Calendar"
        logger.info(f"Executing AppleScript in {app_name}")
        logger.debug(f"AppleScript to execute: {applescript}")
        
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        logger.info(f"AppleScript execution completed with return code: {result.returncode}")
        
        if result.stdout:
            logger.debug(f"AppleScript stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"AppleScript stderr: {result.stderr}")
        
        if result.returncode != 0:
            logger.error(f"AppleScript failed with code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.error("AppleScript execution timed out")
        return False
    except subprocess.SubprocessError as e:
        logger.error(f"Subprocess error executing AppleScript: {str(e)}")
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
    parser = argparse.ArgumentParser(description="Create a calendar event from natural language.")
    parser.add_argument("--dry-run", action="store_true", help="Extract and show the event without creating it")
    parser.add_argument("--debug", action="store_true", help="Include detailed extraction and calendar request logs")
    parser.add_argument("description", nargs="+", help="Event description")
    args = parser.parse_args()
    logger = setup_logging(args.debug)
    logger.info("FOCAL starting up")
    
    user_input = sanitize_input(" ".join(args.description))
    logger.info(f"Processing user input: '{user_input}'")
    
    if not user_input:
        logger.error("Invalid event description after sanitization")
        print("Error: Invalid event description")
        sys.exit(1)
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        logger.error("OpenAI API key not found")
        print("Error: OpenAI API key not found in .openai_key file")
        sys.exit(1)
    
    # Get calendar app preference
    calendar_app = get_calendar_app()
    app_name = "Fantastical" if calendar_app == "fantastical" else "Apple Calendar"
    logger.info(f"📅 CALENDAR APP: {app_name} ({calendar_app})")
    
    logger.info("API key found, proceeding with event generation")
    
    # Extract structured event data using OpenAI
    prompt = create_extraction_prompt(user_input)
    logger.debug(f"Created extraction prompt for OpenAI")
    
    json_response = extract_event_data(prompt, api_key, logger)
    
    if not json_response:
        logger.error("Failed to get response from OpenAI")
        print("Error: Failed to process event with OpenAI")
        sys.exit(1)
    
    # Parse and validate the extracted data
    event_data = parse_and_validate_event_data(json_response, logger)
    
    if not event_data:
        logger.error("Failed to parse or validate event data")
        print("Error: Failed to extract valid event data")
        sys.exit(1)
    
    # Get target calendar for both apps
    target_calendar = get_target_calendar()
    logger.info(f"📅 Target calendar: {target_calendar}")
    
    if calendar_app == "fantastical":
        request = create_fantastical_url(event_data, user_input, target_calendar, logger)
    else:
        request = create_calendar_applescript(event_data, user_input, target_calendar, logger)

    if not request:
        print("Error: Failed to generate calendar request; see the log for details")
        sys.exit(1)

    if args.dry_run:
        print(json.dumps(event_data, indent=2))
        print(f"Dry run: no event created. Target: {app_name} / {target_calendar}")
        logger.debug("Calendar request: %s", request)
        return

    if calendar_app == "fantastical":
        success = execute_fantastical_url(request, logger)
        status = "Request sent to Fantastical (check the app to confirm)"
    else:
        success = execute_applescript(request, calendar_app, logger)
        status = "Event created"
    if not success:
        logger.error(f"Failed to create event in {app_name}")
        print(f"Error: Failed to create event in {app_name}")
        sys.exit(1)
    print(f"{status}: {event_data['title']} on {event_data['start_date']} "
          f"at {event_data.get('start_time') or 'all day'} in {target_calendar}")

if __name__ == "__main__":
    main()