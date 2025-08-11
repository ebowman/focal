# Debugging Alfred Workflow Issues

## 1. Enable Alfred Debug Mode

1. Open Alfred Preferences → Workflows
2. Find "Fantastical Calendar Events (OpenAI)" workflow
3. Click the bug icon (🐛) in the top-right corner of the workflow window
4. This opens the Debug Console

## 2. Test the Workflow

With the debug console open:
1. Trigger Alfred (⌘ + Space or your hotkey)
2. Type: `fc test event tomorrow at 3pm`
3. Press Enter
4. Watch the debug output for errors

## 3. Common Issues to Look For

### Path Issues
The debug console will show if scripts can't be found:
- `./run.sh: No such file or directory`
- `python3: command not found`

### Permission Issues
- `Permission denied: ./run.sh`
- Scripts need execute permissions

### Python/Module Issues
- `ModuleNotFoundError: No module named 'openai'`
- Venv not being used correctly

### API Key Issues
- `OpenAI API key not found`
- Invalid API key format

## 4. Manual Testing

To test outside Alfred, find the workflow directory:

```bash
# Find your workflow directory (it has a unique ID)
cd ~/Library/Application\ Support/Alfred/Alfred.alfredpreferences/workflows/
ls -la
# Look for the one with our files

# Once in the workflow directory, test directly:
cd [your-workflow-id]/
./run.sh create_event.py "test event"
```

## 5. Quick Fixes

### Fix Permissions
```bash
chmod +x run.sh
chmod +x *.py
```

### Test Python Path
```bash
./venv/bin/python3 --version
./venv/bin/python3 -c "import openai; print('OpenAI imported successfully')"
```

### Check API Key
```bash
cat openai_key.txt
```

### Test Without Wrapper
```bash
./venv/bin/python3 create_event.py "test event"
```

## 6. Alfred-Specific Environment

Alfred runs with a minimal environment. Common issues:
- Different PATH than terminal
- No shell configuration loaded
- Working directory might be different

## 7. Emergency Fallback

If the venv approach isn't working, create a simpler wrapper:

```bash
#!/bin/bash
/usr/bin/python3 -m pip install --user openai
/usr/bin/python3 "$@"
```

## 8. View Full Error Output

In the debug console, look for:
- `[ERROR]` messages
- Python tracebacks
- Shell error codes
- Missing file errors

Copy the entire debug output to diagnose the issue.