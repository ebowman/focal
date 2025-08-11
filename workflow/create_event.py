#!/usr/bin/env python3
"""
Fantastical Calendar Event Creator
Uses OpenAI API to normalize natural language input for reliable Fantastical parsing.
"""

import sys
import os
import subprocess
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from error_handler import ErrorHandler, SystemChecker
from prompt_engine import PromptEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/Library/Logs/alfred-fantastical.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FantasticalEventCreator:
    def __init__(self):
        self.api_key = self._get_api_key()
        self.openai_client = None
        self.prompt_engine = PromptEngine()
        
    def _get_api_key(self) -> Optional[str]:
        """Get OpenAI API key from config file."""
        try:
            import config
            return config.get_api_key()
        except Exception as e:
            logger.error(f"Failed to get API key: {e}")
            return None
    
    def _init_openai_client(self):
        """Initialize OpenAI client."""
        if self.openai_client is not None:
            return
            
        try:
            import openai
            if not self.api_key:
                raise ValueError("OpenAI API key not found")
                
            self.openai_client = openai.OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized successfully")
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def _create_prompt(self, user_input: str) -> str:
        """Create optimized prompt for OpenAI."""
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        current_time = datetime.now().strftime("%I:%M %p")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%A, %B %d")
        
        return f"""Convert the following natural language request into a single AppleScript command to create a calendar event in Fantastical.

IMPORTANT FORMATTING RULES:
1. Use this exact format: "[Title/Activity] on [Day], [Full Date] at [Time] at [Location]"
2. Be explicit about dates - convert relative dates (today, tomorrow, next week) to specific dates
3. Use 12-hour time format (12 pm, 3:30 pm, etc.)
4. Always include 'with add immediately' at the end for immediate creation
5. If no location is specified, omit the "at [Location]" part
6. If no specific time is given, suggest a reasonable default or ask for clarification

Context:
- Today is {current_date} at {current_time}
- Tomorrow is {tomorrow}

Request: "{user_input}"

Return ONLY the AppleScript command in this format:
tell application "Fantastical"
  parse sentence "[formatted event]" with add immediately
end tell"""

    def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API to generate AppleScript."""
        try:
            self._init_openai_client()
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at converting natural language to structured calendar events for Fantastical. Always follow the formatting rules exactly."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1  # Low temperature for consistent formatting
            )
            
            applescript_cmd = response.choices[0].message.content.strip()
            logger.info(f"Generated AppleScript: {applescript_cmd}")
            return applescript_cmd
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _execute_applescript(self, applescript_cmd: str) -> Dict[str, Any]:
        """Execute AppleScript command."""
        try:
            # Clean up the AppleScript command
            if not applescript_cmd.startswith('tell application'):
                # If OpenAI returned just the parse sentence, wrap it
                if 'parse sentence' in applescript_cmd:
                    applescript_cmd = f'tell application "Fantastical"\n  {applescript_cmd}\nend tell'
                else:
                    raise ValueError("Invalid AppleScript format received from OpenAI")
            
            # Execute the AppleScript
            process = subprocess.run(
                ['osascript', '-e', applescript_cmd],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            result = {
                'success': process.returncode == 0,
                'stdout': process.stdout.strip(),
                'stderr': process.stderr.strip(),
                'applescript': applescript_cmd
            }
            
            logger.info(f"AppleScript execution result: {result}")
            return result
            
        except subprocess.TimeoutExpired:
            logger.error("AppleScript execution timed out")
            return {
                'success': False,
                'error': 'AppleScript execution timed out',
                'applescript': applescript_cmd
            }
        except Exception as e:
            logger.error(f"AppleScript execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'applescript': applescript_cmd
            }
    
    def create_event(self, user_input: str) -> Dict[str, Any]:
        """Main method to create calendar event."""
        logger.info(f"Creating event for input: {user_input}")
        
        # Check system health first
        system_status = SystemChecker.diagnose_system()
        if not system_status['healthy']:
            logger.warning(f"System issues detected: {system_status['issues']}")
            
            # Handle missing Fantastical
            if not system_status['fantastical']['installed']:
                return ErrorHandler.handle_error('no_fantastical', 
                    Exception("Fantastical not installed"), user_input)
        
        try:
            # Validate input
            if not user_input or len(user_input.strip()) < 3:
                return {
                    'success': False,
                    'error': 'Event description too short',
                    'message': 'Please provide a more detailed event description'
                }
            
            # Generate AppleScript using OpenAI with enhanced prompting
            prompt = self.prompt_engine.create_enhanced_prompt(user_input)
            applescript_cmd = self._call_openai_api(prompt)
            
            # Validate and improve the generated AppleScript
            validation = self.prompt_engine.validate_applescript_format(applescript_cmd)
            if not validation['valid']:
                logger.warning(f"Generated AppleScript validation failed: {validation['errors']}")
                applescript_cmd = self.prompt_engine.improve_applescript(applescript_cmd, user_input)
            elif validation['warnings']:
                logger.info(f"AppleScript warnings: {validation['warnings']}")
                applescript_cmd = self.prompt_engine.improve_applescript(applescript_cmd, user_input)
            
            # Execute AppleScript
            result = self._execute_applescript(applescript_cmd)
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'Calendar event created successfully!',
                    'applescript': result['applescript'],
                    'method': 'openai'
                }
            else:
                # Handle Fantastical parsing errors
                return ErrorHandler.handle_error('fantastical_error',
                    Exception(result.get('stderr', 'Unknown Fantastical error')), 
                    user_input)
                
        except ImportError as e:
            if 'openai' in str(e):
                return ErrorHandler.handle_error('api_error', e, user_input)
            else:
                return ErrorHandler.handle_error('unknown_error', e, user_input)
        except Exception as e:
            # Classify and handle the error appropriately
            error_type = ErrorHandler.classify_error(e)
            return ErrorHandler.handle_error(error_type, e, user_input)

def show_notification(title: str, message: str, sound: bool = True):
    """Show macOS notification."""
    try:
        applescript = f'''
        display notification "{message}" with title "{title}"
        '''
        if sound:
            applescript += ' sound name "Glass"'
        
        subprocess.run(['osascript', '-e', applescript], check=True)
    except Exception as e:
        logger.error(f"Failed to show notification: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 create_event.py 'event description'")
        sys.exit(1)
    
    user_input = sys.argv[1]
    creator = FantasticalEventCreator()
    
    try:
        result = creator.create_event(user_input)
        
        if result['success']:
            success_msg = result['message']
            if result.get('fallback_used'):
                success_msg += " (using fallback parsing)"
            
            print(success_msg)
            show_notification("Calendar Event Created", success_msg)
        else:
            error_msg = result.get('message', 'Unknown error occurred')
            print(f"Error: {error_msg}")
            
            # Show detailed error information
            if 'suggestion' in result:
                print(f"Suggestion: {result['suggestion']}")
            
            if 'original_error' in result:
                print(f"Technical details: {result['original_error']}")
            
            show_notification(result.get('title', 'Calendar Event Failed'), error_msg, sound=False)
            
        # Always show the generated AppleScript for debugging
        if 'applescript' in result:
            method = result.get('method', 'unknown')
            print(f"\nGenerated AppleScript ({method}):\n{result['applescript']}")
        
        # Show system diagnosis if there were issues
        if 'error_type' in result and result['error_type'] in ['no_fantastical', 'api_error']:
            print(f"\nSystem diagnosis: {SystemChecker.diagnose_system()}")
            
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(error_msg)
        logger.error(error_msg)
        show_notification("Calendar Event Failed", "Unexpected error occurred", sound=False)

if __name__ == "__main__":
    main()