#!/usr/bin/env python3
"""
Error handling and fallback mechanisms for Fantastical Calendar Events workflow.
"""

import os
import sys
import logging
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class FallbackEventCreator:
    """Fallback event creation when OpenAI API fails."""
    
    @staticmethod
    def parse_basic_event(user_input: str) -> Optional[Dict[str, Any]]:
        """Basic parsing of common event patterns as fallback."""
        patterns = [
            # "Meeting tomorrow at 2pm"
            r'(?P<title>.+?)\s+(?P<date>today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+at\s+(?P<time>\d{1,2}(?::\d{2})?\s*(?:am|pm))',
            
            # "Lunch with Anna at noon tomorrow"
            r'(?P<title>.+?)\s+at\s+(?P<time>noon|\d{1,2}(?::\d{2})?\s*(?:am|pm))\s+(?P<date>today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            
            # "Meeting next Tuesday at 3pm at Conference Room"
            r'(?P<title>.+?)\s+(?P<date>next\s+\w+|\w+day)\s+at\s+(?P<time>\d{1,2}(?::\d{2})?\s*(?:am|pm))\s+at\s+(?P<location>.+)',
            
            # Simple "Title at time"
            r'(?P<title>.+?)\s+at\s+(?P<time>\d{1,2}(?::\d{2})?\s*(?:am|pm|noon))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                return match.groupdict()
        
        # If no pattern matches, at least try to create a basic event
        return {"title": user_input, "time": None, "date": None, "location": None}
    
    @staticmethod
    def create_fallback_applescript(parsed_event: Dict[str, Any]) -> str:
        """Create basic AppleScript from parsed components."""
        title = parsed_event.get('title', 'New Event').strip()
        time_part = parsed_event.get('time', '')
        date_part = parsed_event.get('date', '')
        location_part = parsed_event.get('location', '')
        
        # Build the sentence
        parts = [title]
        
        if date_part:
            parts.append(f"on {date_part}")
        
        if time_part:
            if time_part == 'noon':
                time_part = '12 pm'
            parts.append(f"at {time_part}")
        
        if location_part:
            parts.append(f"at {location_part}")
        
        sentence = " ".join(parts)
        
        return f'''tell application "Fantastical"
  parse sentence "{sentence}" with add immediately
end tell'''

class ErrorHandler:
    """Comprehensive error handling for the workflow."""
    
    ERROR_MESSAGES = {
        'no_api_key': {
            'title': 'OpenAI API Key Missing',
            'message': 'Please set up your OpenAI API key. Run setup_config.py or set OPENAI_API_KEY environment variable.',
            'suggestion': 'Run python3 setup_config.py in the workflow directory'
        },
        'api_limit': {
            'title': 'API Rate Limit Reached',
            'message': 'OpenAI API rate limit exceeded. Please try again in a few minutes.',
            'suggestion': 'Wait a few minutes and try again'
        },
        'api_error': {
            'title': 'OpenAI API Error',
            'message': 'Error communicating with OpenAI API. Using fallback parsing.',
            'suggestion': 'Check your internet connection and API key'
        },
        'fantastical_error': {
            'title': 'Fantastical Error',
            'message': 'Fantastical could not parse the event. Please try rephrasing.',
            'suggestion': 'Try: "Event title on Monday at 2pm" format'
        },
        'no_fantastical': {
            'title': 'Fantastical Not Found',
            'message': 'Fantastical app is not installed or not running.',
            'suggestion': 'Install Fantastical from the App Store'
        },
        'network_error': {
            'title': 'Network Error',
            'message': 'Cannot connect to OpenAI API. Check your internet connection.',
            'suggestion': 'Check internet connection and try again'
        }
    }
    
    @classmethod
    def handle_error(cls, error_type: str, original_error: Exception, user_input: str) -> Dict[str, Any]:
        """Handle specific error types and provide appropriate responses."""
        error_info = cls.ERROR_MESSAGES.get(error_type, {
            'title': 'Unknown Error',
            'message': f'An unexpected error occurred: {str(original_error)}',
            'suggestion': 'Please try again'
        })
        
        logger.error(f"Error type: {error_type}, Original error: {original_error}")
        
        result = {
            'success': False,
            'error_type': error_type,
            'title': error_info['title'],
            'message': error_info['message'],
            'suggestion': error_info['suggestion'],
            'original_error': str(original_error)
        }
        
        # Attempt fallback for certain errors
        if error_type in ['api_error', 'api_limit', 'network_error']:
            fallback_result = cls._attempt_fallback(user_input)
            if fallback_result['success']:
                result['fallback_used'] = True
                result['success'] = True
                result['message'] = 'Created event using fallback parsing (OpenAI API unavailable)'
                result['applescript'] = fallback_result['applescript']
        
        return result
    
    @classmethod
    def _attempt_fallback(cls, user_input: str) -> Dict[str, Any]:
        """Attempt to create event using fallback parsing."""
        try:
            fallback_creator = FallbackEventCreator()
            parsed_event = fallback_creator.parse_basic_event(user_input)
            
            if parsed_event:
                applescript = fallback_creator.create_fallback_applescript(parsed_event)
                
                # Test the AppleScript
                process = subprocess.run(
                    ['osascript', '-e', applescript],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if process.returncode == 0:
                    return {
                        'success': True,
                        'applescript': applescript,
                        'method': 'fallback'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Fallback AppleScript failed: {process.stderr}'
                    }
            
            return {'success': False, 'error': 'Could not parse event'}
            
        except Exception as e:
            logger.error(f"Fallback parsing failed: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def classify_error(error: Exception) -> str:
        """Classify error type based on exception details."""
        error_str = str(error).lower()
        
        if 'api key' in error_str or 'authentication' in error_str:
            return 'no_api_key'
        elif 'rate limit' in error_str or 'quota' in error_str:
            return 'api_limit'
        elif 'network' in error_str or 'connection' in error_str or 'timeout' in error_str:
            return 'network_error'
        elif 'fantastical' in error_str:
            return 'fantastical_error'
        elif 'openai' in error_str:
            return 'api_error'
        else:
            return 'unknown_error'

class SystemChecker:
    """Check system requirements and dependencies."""
    
    @staticmethod
    def check_fantastical() -> Dict[str, Any]:
        """Check if Fantastical is available."""
        try:
            # Check if Fantastical is installed
            process = subprocess.run(
                ['osascript', '-e', 'tell application "System Events" to exists application process "Fantastical"'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            is_running = process.stdout.strip() == 'true'
            
            # Check if app exists
            app_check = subprocess.run(
                ['osascript', '-e', 'tell application "Finder" to exists application file id "com.flexibits.fantastical2.mac"'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            app_exists = app_check.stdout.strip() == 'true'
            
            return {
                'installed': app_exists,
                'running': is_running,
                'available': app_exists  # Can launch even if not running
            }
            
        except Exception as e:
            logger.error(f"Error checking Fantastical: {e}")
            return {'installed': False, 'running': False, 'available': False}
    
    @staticmethod
    def check_dependencies() -> Dict[str, Any]:
        """Check Python dependencies."""
        missing_deps = []
        
        try:
            import openai
        except ImportError:
            missing_deps.append('openai')
        
        return {
            'all_present': len(missing_deps) == 0,
            'missing': missing_deps
        }
    
    @staticmethod
    def diagnose_system() -> Dict[str, Any]:
        """Run full system diagnosis."""
        fantastical_status = SystemChecker.check_fantastical()
        dependency_status = SystemChecker.check_dependencies()
        
        issues = []
        
        if not fantastical_status['installed']:
            issues.append('Fantastical is not installed')
        elif not fantastical_status['available']:
            issues.append('Fantastical is not accessible')
        
        if not dependency_status['all_present']:
            issues.append(f"Missing Python packages: {', '.join(dependency_status['missing'])}")
        
        return {
            'healthy': len(issues) == 0,
            'issues': issues,
            'fantastical': fantastical_status,
            'dependencies': dependency_status
        }