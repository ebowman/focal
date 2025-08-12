#!/bin/bash

# FOCAL Build Script
# Simple build process: check key, create venv, install deps, package

set -e

echo "🔧 Building FOCAL"
echo "================"

cd workflow

# Check for API key
if [ ! -f ".openai_key" ]; then
    echo "❌ ERROR: workflow/.openai_key not found"
    echo ""
    echo "Add your OpenAI API key:"
    echo "  echo 'sk-your-key' > workflow/.openai_key"
    exit 1
fi

if grep -q "REPLACE_WITH_YOUR_OPENAI_API_KEY" .openai_key 2>/dev/null; then
    echo "❌ ERROR: Please add your actual API key to workflow/.openai_key"
    exit 1
fi

echo "✅ API key found"

# Create virtual environment
echo "📦 Setting up Python environment..."
rm -rf venv
python3 -m venv venv
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet openai

# Package the workflow
echo "📦 Creating workflow package..."
cd ..
python3 workflow/package_workflow.py

echo ""
echo "✅ Build complete!"
echo "📦 Install the workflow from: dist/*.alfredworkflow"