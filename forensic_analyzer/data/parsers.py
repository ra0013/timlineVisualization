"""
Parsing utilities for Cellebrite data formats.
"""

import re
from datetime import datetime
from typing import Optional, Tuple


class CellebriteTimeParser:
    """Handles parsing of Cellebrite time formats."""
    
    TIME_FORMATS = [
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
    ]
    
    def parse_cellebrite_time(self, time_str: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse Cellebrite time format with start/end annotations.
        
        Args:
            time_str: Time string from Cellebrite export
            
        Returns:
            Tuple of (ISO timestamp string, annotation) where annotation is 'start', 'end', or None
        """
        try:
            time_str = str(time_str).strip()
            
            # Extract start/end annotation
            annotation = None
            if '[Start time]' in time_str:
                annotation = 'start'
            elif '[End time]' in time_str:
                annotation = 'end'
            
            # Remove timezone part and annotations
            clean_time = re.sub(r'\(UTC[+-]\d+\)', '', time_str).strip()
            clean_time = re.sub(r'\[.*?\]', '', clean_time).strip()
            
            for fmt in self.TIME_FORMATS:
                try:
                    dt = datetime.strptime(clean_time, fmt)
                    return dt.strftime("%Y-%m-%dT%H:%M:%SZ"), annotation
                except ValueError:
                    continue
            
            return None, None
            
        except Exception:
            return None, None


class AppNameExtractor:
    """Extracts specific app names from Cellebrite descriptions and event types."""
    
    # App name mappings
    APP_PATTERNS = {
        # Social media apps
        'snapchat': 'Snapchat',
        'instagram': 'Instagram', 
        'facebook': 'Facebook',
        'tiktok': 'TikTok',
        'twitter': 'Twitter',
        'whatsapp': 'WhatsApp',
        'telegram': 'Telegram',
        
        # Communication apps
        'youtube': 'YouTube',
        'spotify': 'Spotify',
        'maps': 'Maps',
        'navigation': 'Maps',
        'chrome': 'Browser',
        'safari': 'Browser',
        'browser': 'Browser',
        
        # System events
        'notification': 'Notifications',
        'network': 'Network',
        'log': 'System',
    }
    
    def extract_app_name(self, description: str, event_type: str) -> str:
        """
        Extract specific app name from description and event type.
        
        Args:
            description: Event description text
            event_type: Event type text
            
        Returns:
            Standardized app name
        """
        desc_lower = description.lower()
        type_lower = event_type.lower()
        
        # Check both description and event type for app patterns
        combined_text = f"{desc_lower} {type_lower}"
        
        # Direct pattern matching
        for pattern, app_name in self.APP_PATTERNS.items():
            if pattern in combined_text:
                return app_name
        
        # Special handling for communication events
        if any(pattern in type_lower for pattern in ['call', 'phone']):
            return 'Phone'
        elif any(pattern in type_lower for pattern in ['sms', 'message']):
            return 'Messages'
        
        return 'Unknown'


class ForensicEventClassifier:
    """Classifies events by forensic significance."""
    
    def classify_forensic_event(
        self, 
        event_type_str: str, 
        description_str: str, 
        direction_str: str = "", 
        app_name: str = ""
    ) -> str:
        """
        Classify events by forensic significance with app-specific priority.
        
        Args:
            event_type_str: Event type
            description_str: Event description
            direction_str: Event direction (incoming/outgoing)
            app_name: App name
            
        Returns:
            Forensic priority classification
        """
        event_str = str(event_type_str).lower()
        desc_str = str(description_str).lower()
        dir_str = str(direction_str).lower()
        app_str = str(app_name).lower()
        
        # HIGH PRIORITY: Active phone interactions
        if self._is_call_event(event_str, dir_str):
            return 'call_active'
        elif self._is_message_event(event_str):
            return 'sms_active'
        elif self._is_social_media_event(event_str, desc_str, app_str):
            return 'social_media_active'
        elif 'call log' in event_str:  # Call logs indicate phone interaction
            return 'call_active'
        
        # MEDIUM PRIORITY: Notifications that could distract
        elif self._is_notification_event(event_str):
            return 'notification_passive'
        
        # LOW PRIORITY: Background system events
        elif self._is_background_event(event_str):
            return 'system_background'
        
        return 'default'
    
    def _is_call_event(self, event_str: str, dir_str: str) -> bool:
        """Check if event is an active call."""
        return (
            ('call' in event_str or 'phone' in event_str) and 
            ('incoming' in dir_str or 'outgoing' in dir_str)
        )
    
    def _is_message_event(self, event_str: str) -> bool:
        """Check if event is a message/SMS."""
        return any(pattern in event_str for pattern in [
            'sms', 'message', 'instant message'
        ])
    
    def _is_social_media_event(self, event_str: str, desc_str: str, app_str: str) -> bool:
        """Check if event is social media usage."""
        social_apps = ['snapchat', 'instagram', 'facebook', 'twitter', 'tiktok']
        media_apps = ['youtube', 'spotify', 'browser', 'chrome', 'safari']
        
        return (
            'social media' in event_str or
            any(app in app_str for app in social_apps) or
            any(app in desc_str for app in social_apps) or
            any(app in app_str for app in media_apps)
        )
    
    def _is_notification_event(self, event_str: str) -> bool:
        """Check if event is a notification."""
        return any(pattern in event_str for pattern in [
            'notification', 'alert', 'device notifications'
        ])
    
    def _is_background_event(self, event_str: str) -> bool:
        """Check if event is a background system event."""
        return any(pattern in event_str for pattern in [
            'log entries', 'network connections', 'system', 'connection'
        ])