FOCAL - Smart Calendar Events with OpenAI

SIMPLE WORKFLOW WITH DUAL CALENDAR SUPPORT

⸻

How to Install:

1. Clone the repo
2. Run: ./install.sh (handles everything: setup, build, install)
3. Use: focal [your event]

Simple, reliable, streamlined.

⸻

What This Does:

Natural Language → OpenAI Structured Extraction → Smart Calendar Integration

Two Modes:
- Apple Calendar: Structured AppleScript with direct properties
- Fantastical: Reliable natural language strings → parse sentence

Example: "focal BTGHP Week 5 24-30 August" → Perfect all-day event

⸻

Architecture (EVOLVED):

workflow/
  create_event.py      # ~450 lines - structured extraction, dual calendar support
  info.plist          # Alfred config
  icon.png            # Workflow icon
  .openai_key         # Your API key (gitignored)
  .calendar_app       # Calendar preference: "calendar" or "fantastical"
  package_workflow.py # Enhanced packaging with config files
  
install.sh           # Interactive setup, creates venv, packages with config

⸻

The Innovation:

Instead of fragile NLP → Now uses structured data extraction:
1. OpenAI extracts JSON: {title, dates, all_day, location, notes}
2. Smart calendar integration:
   - Apple Calendar: Direct AppleScript properties
   - Fantastical: Perfect natural language generation
3. Consistent results regardless of calendar app

⸻

Key Features:
- All-day event detection (date ranges, vacation terms)
- Location awareness
- FOCAL attribution in notes
- Enhanced logging and debugging
- Configuration flexibility
- Reliable multi-day events