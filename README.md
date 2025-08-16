# FOCAL - Smart Calendar Events with OpenAI

**Transform natural language into perfectly formatted calendar events using OpenAI's structured intelligence.**

FOCAL combines the power of OpenAI's language understanding with your preferred calendar app, creating a seamless voice-to-calendar experience through Alfred.

## ✨ What FOCAL Does

Simply type `focal` in Alfred followed by your event description:

```
focal Team meeting tomorrow at 2pm
focal BTGHP Week 5 24-30 August  
focal Lunch with Sarah at Cafe Luna Monday 12:30pm
focal Vacation in Greece Aug 1-7
focal Stand-up meeting every Monday at 9am
```

FOCAL intelligently detects:
- **All-day events**: Date ranges, vacations, conferences
- **Timed events**: Specific times with proper scheduling  
- **Locations**: Restaurants, offices, addresses
- **Recurring events**: Daily, weekly, monthly patterns

## 🏆 Key Features

### **Dual Calendar Support**
Choose your preferred calendar app:
- **Apple Calendar**: Direct structured integration
- **Fantastical**: Reliable natural language generation

### **Smart Event Detection** 
- **All-day events**: "24-30 August", "vacation next week", "conference"
- **Precise timing**: "tomorrow at 2pm", "Monday 9:30am" 
- **Location awareness**: "lunch at Cafe Luna", "meeting at office"
- **Recurring patterns**: "every Monday", "weekly standup"

### **Reliable & Consistent**
- Structured data extraction eliminates parsing errors
- Same intelligent processing regardless of calendar app
- Consistent event formatting and attribution

## 🚀 Installation & Setup

### 1. Build from Source
Since your OpenAI API key is embedded in the workflow, you need to build it yourself:

```bash
git clone https://github.com/ebowman/focal.git
cd focal
echo "sk-your-openai-api-key" > workflow/.openai_key
./build.sh
```

### 2. Install Workflow
Double-click the generated `.alfredworkflow` file from `dist/` to install in Alfred.

### 3. Choose Your Calendar App (Optional)
By default, FOCAL uses Apple Calendar. To switch to Fantastical:

```bash
cd workflow
python3 configure.py
```

Or manually:
```bash
echo "fantastical" > workflow/.calendar_app
./build.sh  # Rebuild to include preference
```

## 📱 Usage Examples

### All-Day Events
```
focal BTGHP Week 5 24-30 August        → Week-long all-day event
focal Vacation in Greece Aug 1-7       → Travel event with location  
focal Conference next week              → Multi-day event
```

### Timed Events  
```
focal Team meeting tomorrow at 2pm     → Standard meeting
focal Lunch Monday 12:30pm at Bistro   → Event with location
focal Doctor appointment Fri 3:30pm    → Specific time and date
```

### Recurring Events
```
focal Stand-up every Monday at 9am     → Weekly recurring
focal Team lunch monthly first Friday  → Monthly pattern
```

## 🔧 How It Works

1. **Natural Language Input** → Alfred captures your description
2. **OpenAI Processing** → Extracts structured event data (title, dates, times, location)
3. **Smart Calendar Integration**:
   - **Apple Calendar**: Direct AppleScript with structured properties
   - **Fantastical**: Generated natural language optimized for Fantastical's parser
4. **Event Creation** → Your event appears with "Created by FOCAL" attribution

## 💡 Why FOCAL?

### **The Problem**
Calendar apps' natural language parsing can be inconsistent:
- "Lunch at Factory Girl tomorrow noon" → Parsing failures
- Date ranges like "24-30 August" → Incorrectly created as timed events
- Complex locations → Missed or malformed

### **FOCAL's Solution**  
- **Structured Intelligence**: OpenAI extracts precise data first, then formats perfectly
- **Calendar Flexibility**: Works with both Apple Calendar and Fantastical
- **Consistent Results**: Same input always produces the same event
- **Smart Defaults**: All-day detection, proper time zones, location handling

## 📋 Requirements

- **Alfred 4+** with Powerpack license
- **macOS 10.15+** 
- **OpenAI API key** ([Get one here](https://platform.openai.com/api-keys))
- **Calendar app**: Apple Calendar (built-in) or Fantastical 3+

## 🛠️ Configuration Options

### Calendar App Selection
```bash
# Use Apple Calendar (default)
echo "calendar" > workflow/.calendar_app

# Use Fantastical  
echo "fantastical" > workflow/.calendar_app
```

### Interactive Configuration
```bash
cd workflow
python3 configure.py
```

## 🐛 Troubleshooting

### Events Not Appearing?
- Check Alfred's debugger for error messages
- Verify your OpenAI API key is valid
- Ensure your chosen calendar app is installed and running

### Wrong Calendar App?
- Run `python3 workflow/configure.py` to change settings
- Or manually edit `.calendar_app` file and rebuild

### API Key Issues?
- Get a new key from [OpenAI Platform](https://platform.openai.com/api-keys)
- Update with: `echo "sk-your-new-key" > workflow/.openai_key`
- Rebuild: `./build.sh`

## 🔐 Security & Privacy

- **API keys stay local**: Your OpenAI key is embedded in the workflow, never shared
- **No external dependencies**: All processing happens on your machine + OpenAI
- **Event attribution**: All events include "Created by FOCAL" for transparency

## 🎯 Examples in Action

| Input | Result |
|-------|---------|
| `focal BTGHP Week 5 24-30 August` | All-day event Aug 24-30 |
| `focal Meeting tomorrow 2pm` | Timed event with 1-hour duration |
| `focal Lunch at Cafe Luna Mon 12:30` | Event with location |
| `focal Vacation in Greece Aug 1-7` | All-day travel event |
| `focal Standup every Monday 9am` | Weekly recurring meeting |

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- **OpenAI GPT-4** for intelligent natural language processing
- **Apple Calendar/Fantastical** for calendar integration  
- **Alfred** for seamless macOS integration