#!/bin/bash

# FOCAL AI-Powered Release Script
# Analyzes changes, determines version, embeds it, commits, tags, and pushes

set -e

echo "🤖 FOCAL AI Release Assistant"
echo "============================"
echo ""

# Check if we have uncommitted changes - FAIL if any exist
if ! git diff --quiet HEAD || ! git diff --quiet --cached; then
    echo "❌ Error: You have uncommitted changes"
    echo "   Please commit all changes before releasing"
    echo ""
    git status --short
    echo ""
    echo "Release cancelled - clean working directory required"
    exit 1
fi

echo "🔍 Analyzing changes with AI..."
python3 version.py

# Get the AI recommendation
version_output=$(python3 -c "
from version import get_next_version
result = get_next_version()
print(f'{result[\"next_version\"]}|{result[\"bump_type\"]}|{result[\"reasoning\"]}')
")

IFS='|' read -r next_version bump_type reasoning <<< "$version_output"

echo ""
echo "🎯 AI Recommendation:"
echo "   Next version: $next_version ($bump_type bump)"
echo "   Reasoning: $reasoning"
echo ""

read -p "Proceed with v$next_version? (Y/n): " proceed
if [[ "$proceed" =~ ^[Nn] ]]; then
    echo "Release cancelled"
    exit 0
fi

echo ""
echo "📝 Embedding version in workflow files..."
# Update info.plist template with actual version
sed -i '' "s/{{VERSION}}/$next_version/g" workflow/info.plist

echo "💾 Committing version changes..."
git add workflow/info.plist
git commit -m "Release v$next_version

$reasoning

🤖 Version determined by AI analysis"

echo "🏷️  Creating git tag..."
git tag -a "v$next_version" -m "Release v$next_version"

echo "🚀 Pushing to GitHub..."
git push origin main
git push origin "v$next_version"

echo ""
echo "🎉 Release Complete!"
echo "==================="
echo "Version: v$next_version pushed to GitHub"
echo ""
echo "Next steps:"
echo "  1. Create GitHub release from tag v$next_version"
echo "  2. Run './install.sh' to build and package workflow"
echo "  3. Attach the .alfredworkflow file to the GitHub release"
echo ""
echo "🚀 Ready for users!"