FOCAL - Fantastical OpenAI Calendar Alfred Linker

SIMPLE WORKFLOW - NO COMPLEXITY

⸻

How to Build and Install:

1. Clone the repo
2. Add your OpenAI key: echo "sk-your-key" > workflow/.openai_key  
3. Run: ./build.sh
4. Install: Double-click the .alfredworkflow file in dist/
5. Use: focal [your event]

That's it. No complexity.

⸻

What This Does:

Takes natural language → Sends to OpenAI → Creates AppleScript → Runs in Fantastical

Example: "focal Team meeting every Monday at 2pm"

⸻

File Structure (MINIMAL):

workflow/
  create_event.py    # 100 lines - gets key, calls OpenAI, runs AppleScript
  info.plist         # Alfred config
  icon.png           # Workflow icon
  .openai_key        # Your API key (gitignored)
  package_workflow.py # Packaging script
  
build.sh             # Checks key, creates venv, packages

⸻

The only "complex" part is packaging the venv, which is just:
1. python3 -m venv venv
2. pip install openai
3. Copy everything including venv into a zip file

⸻

Important: Recurring events work! The prompt preserves "every Monday", "weekly", etc.