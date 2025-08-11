#!/usr/bin/env python3
"""
Advanced prompt engineering for Fantastical AppleScript generation.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class PromptEngine:
    """Advanced prompt engineering for reliable AppleScript generation."""
    
    # Common time expressions and their normalized forms
    TIME_NORMALIZATIONS = {
        'noon': '12 pm',
        'midnight': '12 am',
        'morning': '9 am',
        'afternoon': '2 pm',
        'evening': '6 pm',
        'night': '8 pm',
    }
    
    # Day normalizations
    DAY_NORMALIZATIONS = {
        'today': datetime.now().strftime('%A, %B %d'),
        'tomorrow': (datetime.now() + timedelta(days=1)).strftime('%A, %B %d'),
        'yesterday': (datetime.now() - timedelta(days=1)).strftime('%A, %B %d'),
    }
    
    def __init__(self):
        self.current_date = datetime.now()
        self._update_day_normalizations()
    
    def _update_day_normalizations(self):
        """Update day normalizations with current date context."""
        # Add next week days
        for i in range(1, 8):
            future_date = self.current_date + timedelta(days=i)
            day_name = future_date.strftime('%A').lower()
            
            # Add "next Monday", "next Tuesday", etc.
            if future_date.day > self.current_date.day + 6:
                self.DAY_NORMALIZATIONS[f'next {day_name}'] = future_date.strftime('%A, %B %d')
    
    def create_enhanced_prompt(self, user_input: str) -> str:
        """Create an enhanced prompt with better context and examples."""
        
        # Analyze the input to provide targeted examples
        analysis = self._analyze_input(user_input)
        context = self._build_context()
        examples = self._select_relevant_examples(analysis)
        
        prompt = f"""You are an expert at converting natural language to Fantastical calendar events. Your job is to create a single AppleScript command that Fantastical can reliably parse.

CRITICAL FORMATTING RULES:
1. Use EXACT format: "[Title] on [Day], [Full Date] at [Time] at [Location]"
2. Always use full date format: "Monday, August 12" never just "Monday" or "Aug 12"
3. Use 12-hour time format: "2 pm", "3:30 pm", "12 pm" (not "14:00" or "noon")
4. Location comes LAST after "at" (if provided)
5. End with "with add immediately"

{context}

PERFECT EXAMPLES:
{examples}

COMMON MISTAKES TO AVOID:
- "Meeting tomorrow" → Use "Meeting on Tuesday, August 12"
- "Lunch at noon" → Use "Lunch at 12 pm"  
- "at Factory Girl tomorrow at noon" → Use "on Tuesday, August 12 at 12 pm at Factory Girl"

Request to convert: "{user_input}"

Return ONLY the AppleScript command:"""

        return prompt
    
    def _analyze_input(self, user_input: str) -> Dict[str, Any]:
        """Analyze input to determine what type of event it is."""
        analysis = {
            'has_time': bool(re.search(r'\d{1,2}(?::\d{2})?\s*(?:am|pm|noon|midnight)', user_input.lower())),
            'has_date': bool(re.search(r'today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|next\s+\w+', user_input.lower())),
            'has_location': bool(re.search(r'\bat\s+[A-Z]', user_input)),
            'event_type': self._classify_event_type(user_input),
            'complexity': 'simple'
        }
        
        # Determine complexity
        complexity_score = sum([
            analysis['has_time'],
            analysis['has_date'], 
            analysis['has_location'],
            len(user_input.split()) > 6
        ])
        
        if complexity_score >= 3:
            analysis['complexity'] = 'complex'
        elif complexity_score == 2:
            analysis['complexity'] = 'medium'
            
        return analysis
    
    def _classify_event_type(self, user_input: str) -> str:
        """Classify the type of event based on keywords."""
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ['meeting', 'call', 'standup', 'sync']):
            return 'meeting'
        elif any(word in user_input_lower for word in ['lunch', 'dinner', 'coffee', 'drink']):
            return 'meal'
        elif any(word in user_input_lower for word in ['doctor', 'dentist', 'appointment']):
            return 'appointment'
        elif any(word in user_input_lower for word in ['workout', 'gym', 'exercise', 'run']):
            return 'fitness'
        else:
            return 'general'
    
    def _build_context(self) -> str:
        """Build date/time context for the prompt."""
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        next_week = now + timedelta(days=7)
        
        return f"""CURRENT CONTEXT:
- Today is {now.strftime('%A, %B %d, %Y')} at {now.strftime('%I:%M %p')}
- Tomorrow is {tomorrow.strftime('%A, %B %d')}
- Next week starts {next_week.strftime('%A, %B %d')}"""
    
    def _select_relevant_examples(self, analysis: Dict[str, Any]) -> str:
        """Select relevant examples based on input analysis."""
        
        base_examples = [
            'tell application "Fantastical"\n  parse sentence "Team meeting on Monday, August 12 at 2 pm" with add immediately\nend tell',
            'tell application "Fantastical"\n  parse sentence "Lunch with Anna on Tuesday, August 13 at 12 pm at Factory Girl" with add immediately\nend tell',
        ]
        
        # Add specific examples based on event type
        if analysis['event_type'] == 'meeting':
            base_examples.append(
                'tell application "Fantastical"\n  parse sentence "Project review on Friday, August 16 at 3:30 pm in Conference Room A" with add immediately\nend tell'
            )
        elif analysis['event_type'] == 'meal':
            base_examples.append(
                'tell application "Fantastical"\n  parse sentence "Coffee with Sarah on Wednesday, August 14 at 10 am at Starbucks" with add immediately\nend tell'
            )
        elif analysis['event_type'] == 'appointment':
            base_examples.append(
                'tell application "Fantastical"\n  parse sentence "Doctor appointment on Thursday, August 15 at 9:30 am" with add immediately\nend tell'
            )
        
        # Add complexity-specific examples
        if analysis['complexity'] == 'simple':
            base_examples.append(
                'tell application "Fantastical"\n  parse sentence "Workout on Saturday, August 17 at 7 am" with add immediately\nend tell'
            )
        
        return '\n\n'.join(base_examples)
    
    def validate_applescript_format(self, applescript: str) -> Dict[str, Any]:
        """Validate that the generated AppleScript follows our format requirements."""
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check basic structure
        if not applescript.strip().startswith('tell application "Fantastical"'):
            validation_result['valid'] = False
            validation_result['errors'].append('Must start with tell application "Fantastical"')
        
        if 'parse sentence' not in applescript:
            validation_result['valid'] = False
            validation_result['errors'].append('Must contain parse sentence command')
        
        if not applescript.strip().endswith('end tell'):
            validation_result['valid'] = False
            validation_result['errors'].append('Must end with "end tell"')
        
        if 'with add immediately' not in applescript:
            validation_result['warnings'].append('Should include "with add immediately" for immediate creation')
        
        # Extract the sentence to validate format
        sentence_match = re.search(r'parse sentence "([^"]+)"', applescript)
        if sentence_match:
            sentence = sentence_match.group(1)
            
            # Check for relative dates (should be converted to absolute)
            if re.search(r'\b(today|tomorrow)\b', sentence.lower()):
                validation_result['warnings'].append('Consider using absolute dates instead of relative ones')
            
            # Check time format
            if re.search(r'\d{1,2}:\d{2}(?!\s*(?:am|pm))', sentence):
                validation_result['warnings'].append('Use 12-hour format with am/pm')
        
        return validation_result
    
    def improve_applescript(self, applescript: str, user_input: str) -> str:
        """Attempt to improve AppleScript based on validation results."""
        
        validation = self.validate_applescript_format(applescript)
        
        if not validation['valid']:
            # Try to reconstruct from user input using fallback
            from error_handler import FallbackEventCreator
            fallback = FallbackEventCreator()
            parsed = fallback.parse_basic_event(user_input)
            if parsed:
                return fallback.create_fallback_applescript(parsed)
        
        # Apply improvements for warnings
        improved = applescript
        
        if 'with add immediately' not in improved:
            improved = improved.replace('"', '" with add immediately', 1)
        
        return improved