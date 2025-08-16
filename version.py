#!/usr/bin/env python3
"""
AI-Powered Semantic Versioning for FOCAL
Analyzes git changes and uses OpenAI to determine the next version.
"""

import subprocess
import re
import json
from pathlib import Path
from openai import OpenAI

def get_openai_key():
    """Get OpenAI API key from workflow/.openai_key file."""
    key_file = Path(__file__).parent / 'workflow' / '.openai_key'
    if not key_file.exists():
        raise FileNotFoundError("OpenAI API key not found. Run install.sh first.")
    return key_file.read_text().strip()

def get_current_version():
    """Get current version from git tags or default to 1.0.0."""
    try:
        # Get latest tag
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True, text=True, check=True
        )
        tag = result.stdout.strip()
        # Extract version from tag (handles v1.0.0 or 1.0.0)
        match = re.search(r'(\d+\.\d+\.\d+)', tag)
        return match.group(1) if match else "1.0.0"
    except subprocess.CalledProcessError:
        return "1.0.0"

def get_changes_since_last_tag():
    """Get all commits since the last tag."""
    try:
        # Try to get commits since last tag
        result = subprocess.run(
            ['git', 'log', '--oneline', '--no-merges', '--since="1 week ago"'],
            capture_output=True, text=True, check=True
        )
        if not result.stdout.strip():
            # If no recent commits, get last few commits
            result = subprocess.run(
                ['git', 'log', '--oneline', '--no-merges', '-10'],
                capture_output=True, text=True, check=True
            )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "No git history available"

def get_file_changes():
    """Get summary of changed files."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-status', 'HEAD~5..HEAD'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "No file changes detected"

def ask_openai_for_version(current_version, changes, file_changes):
    """Use OpenAI to analyze changes and suggest next version."""
    client = OpenAI(api_key=get_openai_key())
    
    prompt = f"""
You are a semantic versioning expert. Analyze these git changes and determine the next version number.

Current version: {current_version}

Recent commits:
{changes}

File changes:
{file_changes}

Semantic Versioning Rules:
- MAJOR (X.y.z): Breaking changes, incompatible API changes
- MINOR (x.Y.z): New features, backwards compatible
- PATCH (x.y.Z): Bug fixes, backwards compatible

Respond with ONLY a JSON object:
{{
    "next_version": "X.Y.Z",
    "bump_type": "major|minor|patch",
    "reasoning": "Brief explanation of why this version bump"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content.strip()
        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            raise ValueError("No valid JSON found in OpenAI response")
            
    except Exception as e:
        print(f"OpenAI API error: {e}")
        # Fallback to simple patch increment
        parts = current_version.split('.')
        parts[2] = str(int(parts[2]) + 1)
        return {
            "next_version": '.'.join(parts),
            "bump_type": "patch",
            "reasoning": f"Fallback patch increment due to API error: {e}"
        }

def increment_version(current_version, bump_type):
    """Manually increment version based on bump type."""
    major, minor, patch = map(int, current_version.split('.'))
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"

def get_next_version():
    """Main function to get the next version using AI analysis."""
    current_version = get_current_version()
    changes = get_changes_since_last_tag()
    file_changes = get_file_changes()
    
    print(f"Current version: {current_version}")
    print(f"Analyzing {len(changes.splitlines())} recent commits...")
    
    # Get AI recommendation
    ai_result = ask_openai_for_version(current_version, changes, file_changes)
    
    print(f"AI Analysis:")
    print(f"  Recommended: {ai_result['next_version']} ({ai_result['bump_type']} bump)")
    print(f"  Reasoning: {ai_result['reasoning']}")
    
    return ai_result

if __name__ == "__main__":
    try:
        result = get_next_version()
        print(f"\nNext version: {result['next_version']}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)