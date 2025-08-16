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
    echo "   2. Fantastical (natural language) [CURRENT]"
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
    echo "   2. Fantastical (natural language)"
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
# Find the generated .alfredworkflow file and install it
workflow_file=$(find dist/ -name "*.alfredworkflow" | head -1)
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