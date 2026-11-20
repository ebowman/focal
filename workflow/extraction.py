"""Extract structured calendar events using OpenAI."""

import logging
from datetime import datetime, timedelta


def create_extraction_prompt(user_input):
    """Create prompt for OpenAI to extract structured event data."""
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after = (now + timedelta(days=2)).strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    current_weekday = now.strftime("%A")

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
- Specific times mentioned → use those times, all_day: false
- An explicit date such as "today" must be honored even if the time has passed.
- Time mentioned without date (e.g., "at 17:00", "catch up at 5pm"):
  * If the specified time is LATER than current time ({current_time}), use TODAY ({today})
  * If the specified time has ALREADY PASSED today, use TOMORROW ({tomorrow})
  * Example: Current time {current_time}, "catch up at 17:00" → use {today} if 17:00 > {current_time}
- No time specified → default to current time ({current_time}) on appropriate date
- If no end time, default to 1 hour after start
- For recurring events, set recurrence field appropriately
- Use null for empty fields, not empty strings

DATE CONTEXT (IMPORTANT - USE THESE EXACT DATES):
- Current time is {current_time} on {current_weekday}, {today}
- Tomorrow is {tomorrow}
- Day after tomorrow is {day_after}
- Next {days_from_now.get('monday', 'N/A')} is Monday
- Next {days_from_now.get('tuesday', 'N/A')} is Tuesday
- Next {days_from_now.get('wednesday', 'N/A')} is Wednesday
- Next {days_from_now.get('thursday', 'N/A')} is Thursday
- Next {days_from_now.get('friday', 'N/A')} is Friday

Request: "{user_input}"

Return ONLY the JSON object:"""


def extract_event_data(prompt, api_key, logger):
    """Call OpenAI API to extract structured event data."""
    try:
        import openai
    except ImportError:
        logger.error("OpenAI SDK is missing. Run ./install.sh to rebuild the workflow.")
        return None

    # SDK debug logs include full requests; keep diagnostics focused on FOCAL.
    for name in ("openai", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)

    try:
        with openai.OpenAI(api_key=api_key, timeout=30, max_retries=1) as client:
            logger.info("Extracting event with OpenAI (gpt-4.1-mini)")
            logger.debug("Full prompt: %s", prompt)
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured calendar event data from natural language. Always return valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=300,
                temperature=0.1,
            )
        content = response.choices[0].message.content
        if not content:
            logger.error("OpenAI returned no event data")
            return None
        logger.debug("OpenAI extracted JSON: %s", content)
        return content.strip()
    except openai.OpenAIError as error:
        logger.error("OpenAI API call failed: %s", error)
        return None
