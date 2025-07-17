"""
Geographic coordinate utilities for forensic analysis.
"""

from math import radians, sin, cos, sqrt, atan2
from typing import Tuple, List, Optional


class CoordinateUtils:
    """Utilities for geographic coordinate calculations."""
    
    EARTH_RADIUS_METERS = 6371000  # Earth's radius in meters
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.
        
        Args:
            lat1: First point latitude
            lon1: First point longitude  
            lat2: Second point latitude
            lon2: Second point longitude
            
        Returns:
            Distance in meters
        """
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return self.EARTH_RADIUS_METERS * c
    
    def calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate bearing between two coordinates.
        
        Args:
            lat1: Start point latitude
            lon1: Start point longitude
            lat2: End point latitude  
            lon2: End point longitude
            
        Returns:
            Bearing in degrees (0-360)
        """
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        dlon_rad = radians(lon2 - lon1)
        
        y = sin(dlon_rad) * cos(lat2_rad)
        x = cos(lat1_rad) * sin(lat2_rad) - sin(lat1_rad) * cos(lat2_rad) * cos(dlon_rad)
        
        bearing_rad = atan2(y, x)
        bearing_deg = (bearing_rad * 180 / 3.14159 + 360) % 360
        
        return bearing_deg
    
    def calculate_center_point(self, coordinates: List[Tuple[float, float]]) -> Tuple[float, float]:
        """
        Calculate the center point of a list of coordinates.
        
        Args:
            coordinates: List of (latitude, longitude) tuples
            
        Returns:
            Tuple of (center_latitude, center_longitude)
        """
        if not coordinates:
            return (0.0, 0.0)
        
        if len(coordinates) == 1:
            return coordinates[0]
        
        total_lat = sum(coord[0] for coord in coordinates)
        total_lon = sum(coord[1] for coord in coordinates)
        
        center_lat = total_lat / len(coordinates)
        center_lon = total_lon / len(coordinates)
        
        return (center_lat, center_lon)
    
    def get_bounding_box(self, coordinates: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
        """
        Get bounding box for a list of coordinates.
        
        Args:
            coordinates: List of (latitude, longitude) tuples
            
        Returns:
            Tuple of (min_lat, min_lon, max_lat, max_lon)
        """
        if not coordinates:
            return (0.0, 0.0, 0.0, 0.0)
        
        lats = [coord[0] for coord in coordinates]
        lons = [coord[1] for coord in coordinates]
        
        return (min(lats), min(lons), max(lats), max(lons))
    
    def is_within_radius(
        self, 
        center_lat: float, 
        center_lon: float, 
        test_lat: float, 
        test_lon: float, 
        radius_meters: float
    ) -> bool:
        """
        Check if a point is within a given radius of a center point.
        
        Args:
            center_lat: Center point latitude
            center_lon: Center point longitude
            test_lat: Test point latitude
            test_lon: Test point longitude
            radius_meters: Radius in meters
            
        Returns:
            True if point is within radius, False otherwise
        """
        distance = self.calculate_distance(center_lat, center_lon, test_lat, test_lon)
        return distance <= radius_meters
    
    def format_coordinates(self, lat: float, lon: float, precision: int = 5) -> str:
        """
        Format coordinates for display.
        
        Args:
            lat: Latitude
            lon: Longitude
            precision: Decimal places
            
        Returns:
            Formatted coordinate string
        """
        lat_dir = "N" if lat >= 0 else "S"
        lon_dir = "E" if lon >= 0 else "W"
        
        return f"{abs(lat):.{precision}f}°{lat_dir}, {abs(lon):.{precision}f}°{lon_dir}"
    
    def validate_coordinate_bounds(
        self, 
        lat: float, 
        lon: float, 
        min_lat: float = -90, 
        max_lat: float = 90,
        min_lon: float = -180, 
        max_lon: float = 180
    ) -> bool:
        """
        Validate coordinates are within specified bounds.
        
        Args:
            lat: Latitude to validate
            lon: Longitude to validate
            min_lat: Minimum latitude bound
            max_lat: Maximum latitude bound
            min_lon: Minimum longitude bound
            max_lon: Maximum longitude bound
            
        Returns:
            True if coordinates are valid, False otherwise
        """
        return (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)