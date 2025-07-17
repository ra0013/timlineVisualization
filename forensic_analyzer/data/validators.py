"""
Data validation utilities for forensic analysis.
data/validators.py
"""

import pandas as pd
from pathlib import Path
from typing import Tuple, Optional

from config.settings import CONFIG

class DataValidator:
    """Validates data quality and integrity."""
    
    def validate_file_size(self, file_path: Path) -> bool:
        """
        Validate file size is within reasonable limits.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file size is acceptable, False otherwise
        """
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > CONFIG.max_file_size_mb:
                print(f"  File size ({file_size_mb:.1f} MB) exceeds limit ({CONFIG.max_file_size_mb} MB)")
                return False
            return True
        except Exception as e:
            print(f"✗ Error checking file size: {e}")
            return False
    
    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """
        Validate GPS coordinates are within reasonable bounds.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            True if coordinates are valid, False otherwise
        """
        return (
            CONFIG.min_latitude <= lat <= CONFIG.max_latitude and
            CONFIG.min_longitude <= lon <= CONFIG.max_longitude
        )
    
    def validate_speed(self, speed_mph: float) -> bool:
        """
        Validate speed is within reasonable bounds.
        
        Args:
            speed_mph: Speed in miles per hour
            
        Returns:
            True if speed is reasonable, False otherwise
        """
        return 0 <= speed_mph <= CONFIG.max_reasonable_speed
    
    def validate_timestamp(self, timestamp: pd.Timestamp) -> bool:
        """
        Validate timestamp is reasonable (not too far in past/future).
        
        Args:
            timestamp: Timestamp to validate
            
        Returns:
            True if timestamp is reasonable, False otherwise
        """
        if pd.isna(timestamp):
            return False
        
        # Check if timestamp is within reasonable range (last 10 years)
        now = pd.Timestamp.now()
        ten_years_ago = now - pd.Timedelta(days=3650)
        one_year_future = now + pd.Timedelta(days=365)
        
        return ten_years_ago <= timestamp <= one_year_future
    
    def validate_dataframe_integrity(self, df: pd.DataFrame, required_columns: list) -> Tuple[bool, list]:
        """
        Validate DataFrame has required columns and basic integrity.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            Tuple of (is_valid, missing_columns)
        """
        if df is None or df.empty:
            return False, ["DataFrame is empty"]
        
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            return False, missing_columns
        
        return True, []
    
    def clean_location_data(self, location_df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate location data, removing invalid points.
        
        Args:
            location_df: Raw location DataFrame
            
        Returns:
            Cleaned location DataFrame
        """
        if location_df is None or location_df.empty:
            return location_df
        
        initial_count = len(location_df)
        
        # Remove invalid coordinates
        valid_coords = location_df.apply(
            lambda row: self.validate_coordinates(row['latitude'], row['longitude']), 
            axis=1
        )
        location_df = location_df[valid_coords].copy()
        
        # Remove invalid timestamps
        valid_timestamps = location_df['timestamp'].apply(self.validate_timestamp)
        location_df = location_df[valid_timestamps].copy()
        
        # Remove duplicate coordinates at same time
        location_df = location_df.drop_duplicates(
            subset=['timestamp', 'latitude', 'longitude'], 
            keep='first'
        )
        
        cleaned_count = len(location_df)
        if cleaned_count < initial_count:
            print(f"✓ Cleaned location data: {initial_count} → {cleaned_count} points")
        
        return location_df
    
    def filter_gps_accuracy(self, location_df: pd.DataFrame, max_accuracy: float = None) -> pd.DataFrame:
        """
        Filter location data by GPS accuracy.
        
        Args:
            location_df: Location DataFrame
            max_accuracy: Maximum accuracy in meters (uses config default if None)
            
        Returns:
            Filtered DataFrame with only high-accuracy points
        """
        if location_df is None or location_df.empty:
            return location_df
        
        if max_accuracy is None:
            max_accuracy = CONFIG.max_gps_accuracy
        
        if 'accuracy' not in location_df.columns:
            return location_df
        
        initial_count = len(location_df)
        
        # Keep points with no accuracy data (assume good) or accuracy <= threshold
        good_accuracy = location_df[
            (location_df['accuracy'].isna()) | 
            (location_df['accuracy'] <= max_accuracy)
        ].copy()
        
        filtered_count = len(good_accuracy)
        if filtered_count < initial_count:
            print(f"✓ Filtered by accuracy (≤{max_accuracy}m): {initial_count} → {filtered_count} points")
        
        return good_accuracy