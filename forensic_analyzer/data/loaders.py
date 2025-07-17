"""
Data loaders for Cellebrite timeline and location exports.
data/loaders.py
"""

import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import re
from datetime import datetime

from config.settings import CONFIG
from data.parsers import CellebriteTimeParser, AppNameExtractor
from data.validators import DataValidator


class CellebriteTimelineLoader:
    """Loads and processes Cellebrite timeline data."""
    
    def __init__(self):
        self.time_parser = CellebriteTimeParser()
        self.app_extractor = AppNameExtractor()
        self.validator = DataValidator()
    
    def load_timeline(self, filepath: str) -> Optional[pd.DataFrame]:
        """
        Load Cellebrite timeline data from Excel file.
        
        Args:
            filepath: Path to the timeline Excel file
            
        Returns:
            DataFrame with standardized timeline events or None if failed
        """
        try:
            file_path = Path(filepath)
            if not file_path.exists():
                print(f"✗ Timeline file not found: {filepath}")
                return None
                
            if not self.validator.validate_file_size(file_path):
                return None
            
            df = pd.read_excel(filepath, engine='openpyxl', header=1)
            print(f"✓ Loaded timeline: {len(df)} events")
            
            standardized_data = []
            skipped_events = 0
            
            for _, row in df.iterrows():
                event_data = self._process_timeline_row(row)
                if event_data:
                    standardized_data.append(event_data)
                else:
                    skipped_events += 1
            
            if not standardized_data:
                print("✗ No valid timeline events found")
                return None
            
            timeline_df = pd.DataFrame(standardized_data)
            timeline_df = timeline_df.dropna(subset=['timestamp']).sort_values('timestamp')
            
            print(f"✓ Processed {len(timeline_df)} valid timeline events")
            if skipped_events > 0:
                print(f"✓ Skipped {skipped_events} invalid events")
            
            return timeline_df
            
        except Exception as e:
            print(f"✗ Error loading timeline: {e}")
            return None
    
    def _process_timeline_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """Process a single timeline row into standardized format."""
        timestamp_result = self.time_parser.parse_cellebrite_time(row.get('Time', ''))
        if timestamp_result[0] is None:
            return None
        
        timestamp, time_annotation = timestamp_result
        
        # Extract app name from description
        app_name = self.app_extractor.extract_app_name(
            str(row.get('Description', '')), 
            str(row.get('Type', ''))
        )
        
        event_data = {
            'timestamp': pd.to_datetime(timestamp),
            'time_annotation': time_annotation,  # 'start', 'end', or None
            'event_type': str(row.get('Type', '')),
            'direction': str(row.get('Direction', '')),
            'event_description': str(row.get('Type', '')),
            'details': str(row.get('Description', ''))[:500],  # Limit length
            'contact': str(row.get('Party', '')),
            'app_name': app_name,
            'latitude': pd.to_numeric(row.get('Latitude', ''), errors='coerce'),
            'longitude': pd.to_numeric(row.get('Longitude', ''), errors='coerce'),
            'source': 'timeline'
        }
        
        return event_data


class CellebriteLocationLoader:
    """Loads and processes Cellebrite location data."""
    
    def __init__(self):
        self.time_parser = CellebriteTimeParser()
        self.validator = DataValidator()
    
    def load_locations(self, filepath: str) -> Optional[pd.DataFrame]:
        """
        Load Cellebrite location data from Excel file.
        
        Args:
            filepath: Path to the location Excel file
            
        Returns:
            DataFrame with location data or None if failed
        """
        try:
            file_path = Path(filepath)
            if not file_path.exists():
                print(f"✗ Location file not found: {filepath}")
                return None
                
            if not self.validator.validate_file_size(file_path):
                return None
            
            df = pd.read_excel(filepath, engine='openpyxl', header=1)
            print(f"✓ Loaded locations: {len(df)} points")
            
            location_data = []
            skipped_bad_coords = 0
            
            for _, row in df.iterrows():
                location_point = self._process_location_row(row)
                if location_point:
                    location_data.append(location_point)
                else:
                    skipped_bad_coords += 1
            
            if not location_data:
                print("✗ No valid location data found")
                return None
            
            location_df = pd.DataFrame(location_data)
            
            # Remove duplicates and sort
            initial_count = len(location_df)
            location_df = location_df.drop_duplicates(
                subset=['timestamp', 'latitude', 'longitude'], 
                keep='first'
            )
            duplicates_removed = initial_count - len(location_df)
            
            location_df = location_df.sort_values('timestamp')
            
            print(f"✓ Processed {len(location_df)} valid location points")
            if duplicates_removed > 0:
                print(f"✓ Removed {duplicates_removed} duplicate coordinates")
            if skipped_bad_coords > 0:
                print(f"✓ Skipped {skipped_bad_coords} invalid coordinates")
            
            return location_df
            
        except Exception as e:
            print(f"✗ Error loading locations: {e}")
            return None
    
    def _process_location_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """Process a single location row into standardized format."""
        timestamp_result = self.time_parser.parse_cellebrite_time(row.get('Time', ''))
        if timestamp_result[0] is None:
            return None
        
        timestamp = timestamp_result[0]  # Just get timestamp, ignore annotation
        
        lat = pd.to_numeric(row.get('Latitude', ''), errors='coerce')
        lon = pd.to_numeric(row.get('Longitude', ''), errors='coerce')
        
        if pd.isna(lat) or pd.isna(lon):
            return None
        
        # Validate coordinates
        if not self.validator.validate_coordinates(lat, lon):
            return None
        
        accuracy = pd.to_numeric(row.get('Horizontal Accuracy', ''), errors='coerce')
        
        return {
            'timestamp': pd.to_datetime(timestamp),
            'latitude': lat,
            'longitude': lon,
            'accuracy': accuracy,
            'address': row.get('Map Address', ''),
            'source': 'location_tracking'
        }


class DataMerger:
    """Merges timeline and location data."""
    
    def merge_timeline_and_locations(
        self, 
        timeline_df: pd.DataFrame, 
        location_df: Optional[pd.DataFrame], 
        tolerance_minutes: int = CONFIG.location_match_tolerance_minutes
    ) -> pd.DataFrame:
        """
        Merge timeline events with location data.
        
        Args:
            timeline_df: Timeline events DataFrame
            location_df: Location data DataFrame (can be None)
            tolerance_minutes: Time tolerance for location matching
            
        Returns:
            Merged DataFrame with location information
        """
        print(f"\n=== MERGING DATA ===")
        print(f"Timeline events: {len(timeline_df)}")
        print(f"Location points: {len(location_df) if location_df is not None else 0}")
        
        if location_df is None or location_df.empty:
            print("⚠️  No location data available - using timeline events only")
            merged_df = timeline_df.copy()
            merged_df['location_source'] = 'timeline_only'
            return merged_df
        
        tolerance = pd.Timedelta(minutes=tolerance_minutes)
        merged_events = []
        matched_count = 0
        
        for _, event in timeline_df.iterrows():
            event_time = event['timestamp']
            
            # If event already has coordinates, keep them
            if not pd.isna(event['latitude']) and not pd.isna(event['longitude']):
                event_dict = event.to_dict()
                event_dict['latitude'] = float(event['latitude'])
                event_dict['longitude'] = float(event['longitude'])
                event_dict['accuracy'] = None
                event_dict['location_source'] = 'timeline_data'
                merged_events.append(event_dict)
                continue
            
            # Find closest location within tolerance
            if not location_df.empty:
                time_diffs = abs(location_df['timestamp'] - event_time)
                closest_idx = time_diffs.idxmin()
                
                if time_diffs[closest_idx] <= tolerance:
                    closest_location = location_df.loc[closest_idx]
                    event_dict = event.to_dict()
                    event_dict['latitude'] = float(closest_location['latitude'])
                    event_dict['longitude'] = float(closest_location['longitude'])
                    event_dict['accuracy'] = closest_location['accuracy']
                    event_dict['location_source'] = 'location_tracking'
                    merged_events.append(event_dict)
                    matched_count += 1
                else:
                    # No location within tolerance
                    event_dict = event.to_dict()
                    event_dict['latitude'] = None
                    event_dict['longitude'] = None
                    event_dict['accuracy'] = None
                    event_dict['location_source'] = 'no_location'
                    merged_events.append(event_dict)
            else:
                # No location data available
                event_dict = event.to_dict()
                event_dict['latitude'] = None
                event_dict['longitude'] = None
                event_dict['accuracy'] = None
                event_dict['location_source'] = 'no_location'
                merged_events.append(event_dict)
        
        merged_df = pd.DataFrame(merged_events)
        
        # Remove duplicates
        print(f"Before deduplication: {len(merged_df)} events")
        merged_df = merged_df.drop_duplicates(
            subset=['timestamp', 'event_type', 'details'], 
            keep='first'
        )
        print(f"After deduplication: {len(merged_df)} events")
        
        # Report merge statistics
        location_sources = merged_df['location_source'].value_counts()
        print(f"✓ Events with timeline coordinates: {location_sources.get('timeline_data', 0)}")
        print(f"✓ Events matched to location tracking: {location_sources.get('location_tracking', 0)}")
        print(f"✓ Events without location: {location_sources.get('no_location', 0)}")
        
        return merged_df