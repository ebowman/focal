Alfred–Fantastical Natural Language Calendar Events (OpenAI-Structured)

⸻

Overview

This workflow allows a user to create Fantastical calendar events by entering natural language in Alfred. The input is processed by OpenAI to generate a Fantastical AppleScript command with robust, reliable syntax and ordering, reducing failures caused by Fantastical’s strict natural language parser.

⸻

Architecture

Workflow Steps:
	1.	User triggers Alfred with a keyword (e.g., cal) and enters a natural language event description.
	2.	Python script captures this input and sends it to the OpenAI API with a prompt designed to normalize and order the event details for Fantastical.
	3.	OpenAI returns a structured AppleScript command.
	4.	Python script executes the AppleScript command via osascript, creating the event in Fantastical.

⸻

Problem: Fantastical’s Parser Fragility

Fantastical’s parse sentence API is sensitive to the order and syntax of event descriptions. Small variations in phrasing can cause events to be misinterpreted or rejected. For example:
	•	"Lunch with Anna at Factory Girl tomorrow at noon"
may not always be correctly parsed, depending on the order of time, date, and location.
	•	Nonstandard or ambiguous input may lead to errors or unintended events.

⸻

Solution: OpenAI as a Robust Normalizer

The Python script uses OpenAI to enforce a reliable, unambiguous sentence structure before sending to Fantastical.

Prompt Example:

Convert the following request into a single AppleScript command to create a calendar event in Fantastical. Use the following format: "[Title or Activity] on [Day], [Full Date] at [Time] at [Location]". Be explicit, and avoid ambiguity. Add 'with add immediately' for immediate creation. 
Request: "Lunch with Anna tomorrow at Factory Girl at noon"
Response:


⸻

Example Workflow

User input:
Lunch with Anna tomorrow at Factory Girl at noon

OpenAI-generated AppleScript:

tell application "Fantastical"
  parse sentence "Lunch with Anna on Tuesday, August 12 at 12 pm at Factory Girl" with add immediately
end tell

Why this is robust:
	•	Full date specified (Tuesday, August 12)—removes ambiguity from “tomorrow.”
	•	Time is explicit and follows date.
	•	Location is always at the end.
	•	Event title is at the start.
	•	This format aligns with Fantastical’s parsing expectations, greatly reducing parsing failures.

Naive example (prone to error):

tell application "Fantastical"
  parse sentence "Lunch with Anna at Factory Girl tomorrow at noon"
end tell

This ordering may not be reliably parsed, resulting in either errors or incorrect event details.

⸻

Python Script Example

import sys
import openai
import subprocess

user_input = sys.argv[1]

prompt = f'''
Convert the following request into a single AppleScript command to create a calendar event in Fantastical. Use the following format: "[Title or Activity] on [Day], [Full Date] at [Time] at [Location]". Be explicit, and avoid ambiguity. Add 'with add immediately' for immediate creation.
Request: "{user_input}"
Response:
'''

openai.api_key = "sk-..."  # Use environment variable or keychain

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "system", "content": prompt}]
)
applescript_cmd = response['choices'][0]['message']['content'].strip()

process = subprocess.run(['osascript', '-e', applescript_cmd], capture_output=True, text=True)

if process.returncode == 0:
    print("Event created!")
else:
    print(f"Error: {process.stderr}")


⸻

Alfred Workflow Setup
	•	Keyword: cal
	•	Action: Run Script (/usr/bin/python3)
	•	Argument: {query} (passed to the script)

⸻

Considerations
	•	Do not hardcode OpenAI API keys—use secure storage or environment variables.
	•	Add error handling: output both the AppleScript executed and any returned error for debugging.
	•	Expect ~1–3 seconds latency due to OpenAI API.
	•	You may extend the prompt to support calendar selection, reminders, notes, or recurrence.

⸻

References
	•	Fantastical AppleScript Documentation
	•	OpenAI API Documentation
	•	Community Discussion: Fantastical Script Order Issues

⸻

Rationale

OpenAI enables reliable, error-resistant creation of calendar events by consistently translating user intent into the rigid structure Fantastical’s parser requires. This significantly improves automation success rates and user trust in the workflow.

