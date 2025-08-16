FOCAL - Smart Calendar Events with OpenAI

SIMPLE WORKFLOW WITH DUAL CALENDAR SUPPORT

⸻

How to Build and Install:

1. Clone the repo
2. Add your OpenAI key: echo "sk-your-key" > workflow/.openai_key  
3. Choose calendar app: echo "calendar" OR "fantastical" > workflow/.calendar_app
4. Run: ./build.sh
5. Install: Double-click the .alfredworkflow file in dist/
6. Use: focal [your event]

Simple, reliable, configurable.

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
  configure.py         # Interactive configuration script
  info.plist          # Alfred config
  icon.png            # Workflow icon
  .openai_key         # Your API key (gitignored)
  .calendar_app       # Calendar preference: "calendar" or "fantastical"
  package_workflow.py # Enhanced packaging with config files
  
build.sh             # Checks key, creates venv, packages with config

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