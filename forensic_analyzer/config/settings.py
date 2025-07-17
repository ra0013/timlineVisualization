"""
Configuration and constants for the forensic analysis system.
config/settings.py
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple


@dataclass
class ForensicConfig:
    """Configuration class for forensic analysis parameters."""
    
    # Time windows (in minutes)
    default_critical_window: int = 10
    default_analysis_window_before: int = 10 
    default_analysis_window_after: int = 2
    
    # Location matching tolerance
    location_match_tolerance_minutes: int = 5
    
    # Speed thresholds (mph)
    stationary_speed_threshold: float = 3.0
    slow_driving_threshold: float = 35.0
    max_reasonable_speed: float = 120.0
    driving_threshold: float = 5.0  # Minimum speed to consider "driving"
    
    # GPS accuracy thresholds (meters)
    max_gps_accuracy: float = 100.0
    high_accuracy_gps: float = 50.0
    
    # Coordinate bounds (US)
    min_latitude: float = 25.0
    max_latitude: float = 49.0
    min_longitude: float = -125.0
    max_longitude: float = -66.0
    
    # Performance limits
    max_location_points_for_path: int = 1000
    min_time_diff_seconds: int = 10
    
    # File size limits (MB)
    max_file_size_mb: int = 100


@dataclass
class KMLStyles:
    """KML style definitions for different event types."""
    
    # Icon URLs
    PHONE_ICON = 'http://maps.google.com/mapfiles/kml/shapes/phone.png'
    MESSAGE_ICON = 'http://maps.google.com/mapfiles/kml/shapes/info-i.png'
    SOCIAL_ICON = 'http://maps.google.com/mapfiles/kml/shapes/camera.png'
    NOTIFICATION_ICON = 'http://maps.google.com/mapfiles/kml/shapes/info.png'
    SYSTEM_ICON = 'http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png'
    COLLISION_ICON = 'http://maps.google.com/mapfiles/kml/shapes/caution.png'
    TARGET_ICON = 'http://maps.google.com/mapfiles/kml/shapes/target.png'
    ARROW_ICON = 'http://maps.google.com/mapfiles/kml/shapes/arrow.png'
    PAUSE_ICON = 'http://maps.google.com/mapfiles/kml/shapes/pause.png'
    CIRCLE_ICON = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
    
    # Colors (AABBGGRR format for KML)
    RED = 'ff0000ff'
    YELLOW = 'ff00ffff'
    GRAY = 'ff888888'
    BLUE = 'ff0000ff'
    GREEN = 'ff00ff00'
    WHITE = 'ffffffff'
    
    # Style definitions
    FORENSIC_STYLES = {
        'call_active': {'icon': PHONE_ICON, 'color': RED, 'scale': 2.0},
        'sms_active': {'icon': MESSAGE_ICON, 'color': RED, 'scale': 2.0},
        'social_media_active': {'icon': SOCIAL_ICON, 'color': RED, 'scale': 2.0},
        'notification_passive': {'icon': NOTIFICATION_ICON, 'color': YELLOW, 'scale': 1.5},
        'system_background': {'icon': SYSTEM_ICON, 'color': GRAY, 'scale': 0.8},
        'collision_site': {'icon': COLLISION_ICON, 'color': RED, 'scale': 3.0},
        'critical_window': {'icon': TARGET_ICON, 'color': RED, 'scale': 1.8},
        'driving_fast': {'icon': ARROW_ICON, 'color': BLUE, 'scale': 1.2},
        'driving_slow': {'icon': ARROW_ICON, 'color': GREEN, 'scale': 0.8},
        'stationary': {'icon': PAUSE_ICON, 'color': YELLOW, 'scale': 0.6},
        'default': {'icon': CIRCLE_ICON, 'color': WHITE, 'scale': 1.0}
    }


class ForensicPriority:
    """Constants for forensic event priority classification."""
    
    HIGH_PRIORITY = ['call_active', 'sms_active', 'social_media_active']
    MEDIUM_PRIORITY = ['notification_passive']
    LOW_PRIORITY = ['system_background', 'default']
    
    # App classifications
    SOCIAL_MEDIA_APPS = ['snapchat', 'instagram', 'facebook', 'twitter', 'tiktok', 'whatsapp', 'telegram']
    MEDIA_APPS = ['youtube', 'spotify']
    BROWSER_APPS = ['browser', 'chrome', 'safari']
    COMMUNICATION_APPS = ['phone', 'messages', 'sms']
    
    # Event type patterns
    CALL_PATTERNS = ['call', 'phone']
    MESSAGE_PATTERNS = ['sms', 'message', 'instant message']
    NOTIFICATION_PATTERNS = ['notification', 'alert', 'device notifications']
    BACKGROUND_PATTERNS = ['log entries', 'network connections', 'system', 'connection']


# Global configuration instance
CONFIG = ForensicConfig()
KML_STYLES = KMLStyles()
PRIORITY = ForensicPriority()