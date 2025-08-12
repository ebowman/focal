# FOCAL - Fantastical OpenAI Calendar Alfred Linker

Transform natural language into perfectly formatted Fantastical calendar events using OpenAI.

## What it does

Open Alfred's input window and type `focal` followed by natural language, and it creates the event in Fantastical:

```
focal Lunch with Sarah tomorrow at noon
focal Team standup every Monday at 10am
focal Doctor appointment next Friday at 3:30pm at Medical Center
```

### Build from Source

Since your OpenAI API key is embedded in the release, you need to build this yourself:

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
