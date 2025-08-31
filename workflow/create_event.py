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
from datetime import datetime, timedelta

def setup_logging():
    """Setup detailed logging for debugging."""
    logging.basicConfig(
        level=logging.DEBUG,
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

def create_extraction_prompt(user_input):
    """Create prompt for OpenAI to extract structured event data."""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (now + timedelta(days=2)).strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    current_weekday = now.strftime("%A")
    
    # Calculate next week days for reference
    days_from_now = {}
    for i in range(1, 8):
        future_date = now + timedelta(days=i)
        days_from_now[future_date.strftime("%A").lower()] = future_date.strftime("%Y-%m-%d")
    
    return f"""Extract event information from this natural language request and return JSON with these exact fields:

{{
    "title": "event title",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD", 
    "all_day": true/false,
    "start_time": "HH:MM" (24-hour format, null if all_day),
    "end_time": "HH:MM" (24-hour format, null if all_day),
    "location": "location or null",
    "notes": "additional notes or null",
    "recurrence": "daily|weekly|monthly|yearly|null"
}}

RULES FOR ALL-DAY EVENTS:
- Date range patterns like "24-30 August", "Aug 20-25", "June 1-7" → all_day: true
- Multi-day events without specific times → all_day: true
- Week/vacation terminology ("Week 5", "vacation", "conference", "retreat") → all_day: true
- Travel events ("trip to", "holiday in") → all_day: true
- If all_day: true, set start_time and end_time to null

RULES FOR TIMED EVENTS:
- Single day with no time → use current time: {current_time}, all_day: false
- Specific times mentioned → use those times, all_day: false
- If no end time, default to 1 hour after start
- For recurring events, set recurrence field appropriately
- Use null for empty fields, not empty strings

DATE CONTEXT (IMPORTANT - USE THESE EXACT DATES):
- Today is {current_weekday}, {today}
- Tomorrow is {tomorrow}
- Day after tomorrow is {day_after}
- Next {days_from_now.get('monday', 'N/A')} is Monday
- Next {days_from_now.get('tuesday', 'N/A')} is Tuesday
- Next {days_from_now.get('wednesday', 'N/A')} is Wednesday
- Next {days_from_now.get('thursday', 'N/A')} is Thursday
- Next {days_from_now.get('friday', 'N/A')} is Friday
- Current time is {current_time}

Request: "{user_input}"

Return ONLY the JSON object:"""

def extract_event_data(prompt, api_key, logger):
    """Call OpenAI API to extract structured event data."""
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        logger.info("Sending extraction prompt to OpenAI")
        logger.debug(f"Full prompt: {prompt}")
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured calendar event data from natural language. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.1
        )
        
        json_response = response.choices[0].message.content.strip()
        logger.info("Received JSON response from OpenAI")
        logger.info(f"🔍 OPENAI EXTRACTED JSON: {json_response}")
        
        return json_response
    except Exception as e:
        logger.error(f"OpenAI API call failed: {str(e)}")
        return None

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

def create_fantastical_string(event_data, logger):
    """Generate reliable Fantastical natural language string from structured data."""
    try:
        from datetime import datetime
        
        title = event_data['title']
        
        if event_data['all_day']:
            # All-day events: "BTGHP Week 5 from August 24 to August 30"
            start_dt = datetime.strptime(event_data['start_date'], '%Y-%m-%d')
            end_dt = datetime.strptime(event_data['end_date'], '%Y-%m-%d')
            
            if event_data['start_date'] == event_data['end_date']:
                # Single day all-day: "BTGHP Week 5 on August 24, 2025"
                event_string = f"{title} on {start_dt.strftime('%B %d, %Y')}"
            else:
                # Multi-day all-day: "BTGHP Week 5 from August 24 to August 30, 2025"
                if start_dt.year == end_dt.year and start_dt.month == end_dt.month:
                    event_string = f"{title} from {start_dt.strftime('%B %d')} to {end_dt.strftime('%d, %Y')}"
                else:
                    event_string = f"{title} from {start_dt.strftime('%B %d')} to {end_dt.strftime('%B %d, %Y')}"
        else:
            # Timed events: "Meeting on August 17, 2025 at 2:00 PM to 3:00 PM"
            start_dt = datetime.strptime(f"{event_data['start_date']} {event_data['start_time']}", '%Y-%m-%d %H:%M')
            end_dt = datetime.strptime(f"{event_data['end_date']} {event_data['end_time']}", '%Y-%m-%d %H:%M')
            
            event_string = f"{title} on {start_dt.strftime('%B %d, %Y')} at {start_dt.strftime('%I:%M %p')}"
            
            # Add end time if different day or not exactly 1 hour
            if event_data['start_date'] != event_data['end_date'] or (end_dt - start_dt).seconds != 3600:
                if event_data['start_date'] == event_data['end_date']:
                    event_string += f" to {end_dt.strftime('%I:%M %p')}"
                else:
                    event_string += f" to {end_dt.strftime('%B %d, %Y at %I:%M %p')}"
        
        # Add location if specified
        if event_data.get('location'):
            event_string += f" at {event_data['location']}"
        
        # Add calendar specification for Fantastical
        if target_calendar:
            event_string += f" /{target_calendar}"
        
        logger.info("✨ Generated Fantastical natural language string")
        logger.info(f"🎯 FANTASTICAL SENTENCE: '{event_string}'")
        
        return event_string
        
    except Exception as e:
        logger.error(f"Failed to generate Fantastical string: {str(e)}")
        return None

def create_fantastical_applescript(fantastical_string, event_data, user_input, target_calendar, logger):
    """Generate AppleScript for Fantastical using natural language string."""
    try:
        # Add FOCAL attribution with timestamp and original instruction
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Escape user input for AppleScript
        escaped_user_input = user_input.replace('"', '\\"').replace('\\', '\\\\')
        focal_attribution = f"Created by FOCAL on {timestamp}\\nOriginal: \"{escaped_user_input}\""
        
        if event_data.get('notes'):
            notes = f"{event_data['notes']}\\n\\n{focal_attribution}"
        else:
            notes = focal_attribution
        
        # Escape quotes in the fantastical string and notes for AppleScript
        escaped_fantastical_string = fantastical_string.replace('"', '\\"')
        escaped_notes = notes.replace('"', '\\"')
        
        # Build AppleScript for Fantastical with notes (calendar is now in the sentence)
        applescript = f'''tell application "Fantastical"
    parse sentence "{escaped_fantastical_string}" notes "{escaped_notes}" with add immediately
end tell'''
        
        logger.info("🚀 Generated AppleScript for Fantastical")
        logger.debug(f"Generated AppleScript: {applescript}")
        
        return applescript
        
    except Exception as e:
        logger.error(f"Failed to generate Fantastical AppleScript: {str(e)}")
        return None

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
    logger = setup_logging()
    logger.info("FOCAL starting up")
    
    if len(sys.argv) < 2:
        logger.error("No event description provided")
        print("Error: No event description provided")
        sys.exit(1)
    
    user_input = sanitize_input(sys.argv[1])
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
    
    # Generate AppleScript based on calendar app choice
    logger.info(f"🔄 Generating AppleScript for {app_name}...")
    if calendar_app == "fantastical":
        # Generate natural language string for Fantastical
        logger.info("📝 Creating natural language string for Fantastical NLP...")
        fantastical_string = create_fantastical_string(event_data, logger)
        if not fantastical_string:
            logger.error("Failed to generate Fantastical string")
            print("Error: Failed to generate event string")
            sys.exit(1)
        
        logger.info("📋 Converting to Fantastical AppleScript...")
        applescript = create_fantastical_applescript(fantastical_string, event_data, user_input, target_calendar, logger)
    else:
        # Generate structured AppleScript for Apple Calendar
        logger.info("🔧 Creating structured AppleScript for Apple Calendar...")
        applescript = create_calendar_applescript(event_data, user_input, target_calendar, logger)
    
    if not applescript:
        logger.error("Failed to generate AppleScript")
        print("Error: Failed to generate event script")
        sys.exit(1)
    
    # Execute AppleScript
    logger.info("Attempting to execute AppleScript")
    app_name = "Fantastical" if calendar_app == "fantastical" else "Apple Calendar"
    if execute_applescript(applescript, calendar_app, logger):
        logger.info("Event created successfully!")
        print("Event created successfully!")
    else:
        logger.error(f"Failed to create event in {app_name}")
        print(f"Error: Failed to create event in {app_name}")
        sys.exit(1)

if __name__ == "__main__":
    main()