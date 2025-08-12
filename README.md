# FOCAL - Fantastical OpenAI Calendar Alfred Linker

Transform natural language into perfectly formatted Fantastical calendar events using OpenAI.

## What it does

Type `focal` followed by natural language, and it creates the event in Fantastical:

```
focal Lunch with Sarah tomorrow at noon
focal Team standup every Monday at 10am
focal Doctor appointment next Friday at 3:30pm at Medical Center
```

## Installation

### Quick Install (Pre-built)
1. Download the latest `.alfredworkflow` from [Releases](https://github.com/ebowman/focal/releases)
2. Double-click to install
3. Start using with `focal`

### Build from Source
```bash
git clone https://github.com/ebowman/focal.git
cd focal
echo "sk-your-openai-key" > workflow/.openai_key
./build.sh
# Install the .alfredworkflow from dist/
```

## Why FOCAL?

Fantastical's parser can be finicky. FOCAL uses OpenAI to ensure your events are formatted perfectly every time.

**Before:** "Lunch at Factory Girl tomorrow noon" → Might fail  
**After:** "Lunch on Tuesday, December 12 at 12:00 PM at Factory Girl" → Always works

## Requirements

- Alfred 4+ with Powerpack
- Fantastical 3+
- OpenAI API key
- macOS 10.15+

## License

MIT