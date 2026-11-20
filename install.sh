#!/bin/bash

# FOCAL Install Script
# Complete setup: configure, build, and package

set -e

echo "🔧 Building FOCAL"
echo "================"
echo ""

# Configuration
echo "📋 Configuration Setup"
echo "----------------------"

# 1. OpenAI API Key Setup
api_key_file="workflow/.openai_key"

if [ -f "$api_key_file" ]; then
    existing_key=$(cat "$api_key_file" 2>/dev/null || echo "")
    if [[ "$existing_key" =~ ^sk- ]]; then
        echo "✅ API key found: ${existing_key:0:10}..."
        read -p "Update API key? (y/N): " update_key
        if [[ ! "$update_key" =~ ^[Yy] ]]; then
            echo "   Keeping existing key"
        else
            existing_key=""
        fi
    else
        echo "⚠️  Invalid API key format found"
        existing_key=""
    fi
else
    existing_key=""
fi

if [ -z "$existing_key" ]; then
    echo "📝 Get your API key from: https://platform.openai.com/api-keys"
    read -p "Enter your OpenAI API key: " api_key
    
    if [[ ! "$api_key" =~ ^sk- ]]; then
        echo "❌ Invalid API key format (should start with 'sk-')"
        exit 1
    fi
    
    echo "$api_key" > "$api_key_file"
    echo "✅ API key saved"
fi

# 2. Calendar App Preference
calendar_file="workflow/.calendar_app"
current_app="calendar"

if [ -f "$calendar_file" ]; then
    current_app=$(cat "$calendar_file" 2>/dev/null || echo "calendar")
fi

echo ""
echo "Calendar App Preference:"
if [ "$current_app" = "fantastical" ]; then
    echo "   Current: Fantastical ✓"
    echo "   Options:"
    echo "   1. Apple Calendar (structured)"
    echo "   2. Fantastical (structured URL) [CURRENT]"
    echo "   [Enter] Keep current (Fantastical)"
    echo ""
    read -p "Choose calendar app (1/2/Enter): " choice
    
    if [ "$choice" = "1" ]; then
        echo "calendar" > "$calendar_file"
        echo "✅ Switched to Apple Calendar"
    elif [ "$choice" = "2" ] || [ -z "$choice" ]; then
        echo "fantastical" > "$calendar_file"
        echo "✅ Keeping Fantastical"
    else
        echo "fantastical" > "$calendar_file"
        echo "✅ Keeping Fantastical (default)"
    fi
else
    echo "   Current: Apple Calendar ✓"
    echo "   Options:"
    echo "   1. Apple Calendar (structured) [CURRENT]"
    echo "   2. Fantastical (structured URL)"
    echo "   [Enter] Keep current (Apple Calendar)"
    echo ""
    read -p "Choose calendar app (1/2/Enter): " choice
    
    if [ "$choice" = "2" ]; then
        echo "fantastical" > "$calendar_file"
        echo "✅ Switched to Fantastical"
    elif [ "$choice" = "1" ] || [ -z "$choice" ]; then
        echo "calendar" > "$calendar_file"
        echo "✅ Keeping Apple Calendar"
    else
        echo "calendar" > "$calendar_file"
        echo "✅ Keeping Apple Calendar (default)"
    fi
fi

# 3. Target Calendar Selection (for both Apple Calendar and Fantastical)
target_calendar_file="workflow/.target_calendar"
current_calendar=""

if [ -f "$target_calendar_file" ]; then
    current_calendar=$(cat "$target_calendar_file" 2>/dev/null || echo "")
fi

# Configure target calendar for both apps
echo ""
echo "Target Calendar Selection:"
echo "--------------------------"

# Ensure Calendar app is running and accessible before fetching calendars
echo "Ensuring Calendar app is running..."

# Check if Calendar is accessible via AppleScript
calendar_accessible() {
    osascript -e 'tell application "Calendar" to return (count of calendars)' >/dev/null 2>&1
}

if ! calendar_accessible; then
    echo "Starting Calendar app..."
    open -a "Calendar"
    
    # Wait for Calendar to be fully accessible (up to 10 seconds)
    for i in {1..10}; do
        sleep 1
        if calendar_accessible; then
            echo "Calendar app is now accessible"
            break
        fi
        if [ $i -eq 10 ]; then
            echo "⚠️  Calendar app may not be fully accessible"
        fi
    done
fi

# Get available calendars
echo "Fetching available calendars..."
calendars=$(python3 workflow/get_calendars.py 2>/dev/null)

if [ -z "$calendars" ]; then
    echo "⚠️  Could not fetch calendars. Using default 'Calendar'"
    echo "Calendar" > "$target_calendar_file"
else
    echo "Available calendars:"
    i=1
    while IFS= read -r cal; do
        if [ "$cal" = "$current_calendar" ]; then
            echo "   $i. $cal [CURRENT]"
        else
            echo "   $i. $cal"
        fi
        ((i++))
    done <<< "$calendars"
    
    if [ -n "$current_calendar" ]; then
        echo "   [Enter] Keep current ($current_calendar)"
    fi
    
    echo ""
    read -p "Choose calendar number (or Enter to keep current): " cal_choice
    
    if [ -z "$cal_choice" ] && [ -n "$current_calendar" ]; then
        echo "✅ Keeping calendar: $current_calendar"
    elif [ -n "$cal_choice" ]; then
        selected_cal=$(echo "$calendars" | sed -n "${cal_choice}p")
        if [ -n "$selected_cal" ]; then
            echo "$selected_cal" > "$target_calendar_file"
            echo "✅ Selected calendar: $selected_cal"
        else
            echo "⚠️  Invalid selection. Using first calendar"
            first_cal=$(echo "$calendars" | head -1)
            echo "$first_cal" > "$target_calendar_file"
            echo "✅ Using calendar: $first_cal"
        fi
    else
        # No current calendar and no choice made - use first
        first_cal=$(echo "$calendars" | head -1)
        echo "$first_cal" > "$target_calendar_file"
        echo "✅ Using calendar: $first_cal"
    fi
fi

echo ""

# Build Process
echo "📦 Building Workflow"
echo "-------------------"

cd workflow

echo "Setting up Python environment..."
rm -rf venv
python3 -m venv venv
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet openai

echo "Creating workflow package..."
cd ..
python3 workflow/package_workflow.py

echo "Installing workflow into Alfred..."
# Find the newest .alfredworkflow file and install it
workflow_file=$(find dist/ -name "*.alfredworkflow" -exec ls -t {} + | head -1)
if [ -n "$workflow_file" ]; then
    open "$workflow_file"
    echo "✅ Workflow installed in Alfred"
else
    echo "❌ Could not find workflow file to install"
    exit 1
fi

echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo "🚀 Usage: focal [your event]"
echo ""
echo "FOCAL is now installed and ready to use in Alfred!"