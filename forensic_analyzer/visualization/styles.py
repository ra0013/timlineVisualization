"""
KML styling management for forensic analysis visualization.
visualizations/styles.py
"""

import simplekml
from typing import Dict, Any

from config.settings import KML_STYLES


class KMLStyleManager:
    """Manages KML styles for different event types and priorities."""
    
    def __init__(self):
        self.styles: Dict[str, simplekml.Style] = {}
        self._create_styles()
    
    def _create_styles(self):
        """Create all forensic-specific KML styles."""
        for event_type, style_info in KML_STYLES.FORENSIC_STYLES.items():
            style = simplekml.Style()
            style.iconstyle.icon.href = style_info['icon']
            style.iconstyle.color = style_info['color']
            style.iconstyle.scale = style_info['scale']
            
            # Add label style for better visibility
            style.labelstyle.color = style_info['color']
            style.labelstyle.scale = 0.8
            
            self.styles[event_type] = style
    
    def get_style(self, event_type: str) -> simplekml.Style:
        """
        Get KML style for a specific event type.
        
        Args:
            event_type: Type of event/priority level
            
        Returns:
            KML Style object
        """
        return self.styles.get(event_type, self.styles['default'])
    
    def apply_styles_to_kml(self, kml: simplekml.Kml):
        """
        Apply all styles to a KML object.
        
        Args:
            kml: KML object to apply styles to
        """
        for style_name, style in self.styles.items():
            # Add style to KML document
            #kml_style = kml.newstyle()
            #kml_style.iconstyle.icon.href = style.iconstyle.icon.href
            #kml_style.iconstyle.color = style.iconstyle.color
            #kml_style.iconstyle.scale = style.iconstyle.scale
            #kml_style.labelstyle.color = style.labelstyle.color
            #kml_style.labelstyle.scale = style.labelstyle.scale
            return
   
 
    def create_priority_legend(self, kml: simplekml.Kml):
        """
        Create a legend explaining the priority color coding.
        
        Args:
            kml: KML object to add legend to
        """
        legend_folder = kml.newfolder(name="📋 LEGEND - Event Priority Guide")
        
        legend_info = [
            (" HIGH PRIORITY", "Active phone interactions (calls, texts, social media)", "call_active"),
            (" MEDIUM PRIORITY", "Passive notifications and alerts", "notification_passive"),
            (" LOW PRIORITY", "Background system events", "system_background"),
            (" COLLISION SITE", "Location and time of collision", "collision_site"),
            (" CRITICAL WINDOW", "Events in critical timeframe", "critical_window"),
            (" MOVEMENT", "Vehicle speed and movement indicators", "driving_fast")
        ]
        
        for name, description, style_type in legend_info:
            legend_item = legend_folder.newpoint()
            legend_item.name = name
            legend_item.description = f"<b>{description}</b>"
            # Place legend items off-map (coordinates don't matter for legend)
            legend_item.coords = [(0, 0)]
            legend_item.style = self.get_style(style_type)
            legend_item.visibility = 0  # Hide by default
    
    def get_line_style(self, color: str = "blue", width: int = 3) -> Dict[str, Any]:
        """
        Get line style configuration for paths.
        
        Args:
            color: Line color
            width: Line width
            
        Returns:
            Line style configuration
        """
        color_map = {
            "blue": simplekml.Color.blue,
            "red": simplekml.Color.red,
            "green": simplekml.Color.green,
            "yellow": simplekml.Color.yellow,
            "white": simplekml.Color.white
        }
        
        return {
            "color": color_map.get(color, simplekml.Color.blue),
            "width": width
        }
    
    def customize_style(
        self, 
        event_type: str, 
        icon_url: str, 
        color: str, 
        scale: float = 1.0
    ) -> simplekml.Style:
        """
        Create or customize a style for specific needs.
        
        Args:
            event_type: Name for the style
            icon_url: URL to icon image
            color: Color in KML format (AABBGGRR)
            scale: Icon scale factor
            
        Returns:
            Custom KML Style object
        """
        style = simplekml.Style()
        style.iconstyle.icon.href = icon_url
        style.iconstyle.color = color
        style.iconstyle.scale = scale
        style.labelstyle.color = color
        style.labelstyle.scale = 0.8
        
        # Store for future use
        self.styles[event_type] = style
        
        return style
    
    def get_collision_highlight_style(self) -> simplekml.Style:
        """
        Get special style for collision-related highlights.
        
        Returns:
            High-visibility style for collision markers
        """
        style = simplekml.Style()
        style.iconstyle.icon.href = KML_STYLES.COLLISION_ICON
        style.iconstyle.color = KML_STYLES.RED
        style.iconstyle.scale = 3.5  # Extra large for visibility
        style.labelstyle.color = KML_STYLES.RED
        style.labelstyle.scale = 1.2
        
        # Add balloon style for better popup appearance
        style.balloonstyle.bgcolor = simplekml.Color.white
        style.balloonstyle.textcolor = simplekml.Color.black
        
        return style
    
    def get_time_based_style(self, seconds_to_collision: float) -> str:
        """
        Get style based on time proximity to collision.
        
        Args:
            seconds_to_collision: Seconds before collision
            
        Returns:
            Style name based on temporal proximity
        """
        if seconds_to_collision <= 30:  # Last 30 seconds
            return 'critical_window'
        elif seconds_to_collision <= 120:  # Last 2 minutes
            return 'call_active'  # High priority
        elif seconds_to_collision <= 600:  # Last 10 minutes
            return 'notification_passive'  # Medium priority
        else:
            return 'system_background'  # Low priority
    
    def get_speed_based_style(self, speed_mph: float) -> str:
        """
        Get style based on vehicle speed.
        
        Args:
            speed_mph: Speed in miles per hour
            
        Returns:
            Style name based on speed
        """
        if speed_mph < 3:
            return 'stationary'
        elif speed_mph < 35:
            return 'driving_slow'
        else:
            return 'driving_fast'