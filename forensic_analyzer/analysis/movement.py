"""
Movement and speed analysis for forensic investigations.
analysis/movement.py
"""

import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2
from typing import List, Tuple, Optional, Dict, Any

from config.settings import CONFIG
from utils.coordinates import CoordinateUtils


class MovementAnalyzer:
    """Analyzes vehicle movement patterns and correlates with phone usage."""
    
    def __init__(self):
        self.coord_utils = CoordinateUtils()
    
    def analyze_movement_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze movement patterns and correlate with phone usage.
        
        Args:
            df: DataFrame with timeline and location data
            
        Returns:
            DataFrame with movement analysis added
        """
        if df.empty:
            return df
        
        print(f"\n=== MOVEMENT ANALYSIS ===")
        
        # Check if we have location data
        if 'location_source' not in df.columns:
            print("No location source data available for movement analysis")
            df['speed_mph'] = 0
            df['movement_type'] = 'unknown'
            return df
        
        # Get location events for speed calculation
        location_events = self._get_location_events(df)
        
        if location_events.empty:
            print("No valid location data available for movement analysis")
            df['speed_mph'] = 0
            df['movement_type'] = 'stationary'
            return df
        
        # Calculate speeds and movement types
        location_events = self._calculate_speeds_and_movement(location_events)
        
        # Merge speed data back to main dataframe
        df_with_speed = self._merge_speed_data(df, location_events)
        
        # Analyze movement statistics
        self._analyze_movement_statistics(df_with_speed, location_events)
        
        return df_with_speed
    
    def _get_location_events(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and validate location events."""
        location_events = df[
            (df['latitude'].notna()) & 
            (df['longitude'].notna()) &
            (df['location_source'].isin(['location_tracking', 'timeline_data']))
        ].copy()
        
        if location_events.empty:
            return location_events
        
        # Remove duplicate location points
        location_events = location_events.drop_duplicates(
            subset=['timestamp', 'latitude', 'longitude'], 
            keep='first'
        )
        location_events = location_events.sort_values('timestamp')
        
        print(f"Processing {len(location_events)} unique location points for movement analysis")
        
        # Filter by GPS accuracy if available
        if 'accuracy' in location_events.columns:
            good_accuracy = location_events[
                (location_events['accuracy'].isna()) | 
                (location_events['accuracy'] <= CONFIG.max_gps_accuracy)
            ].copy()
            
            if len(good_accuracy) >= 2:
                print(f"Using {len(good_accuracy)} high-accuracy GPS points (≤{CONFIG.max_gps_accuracy}m)")
                location_events = good_accuracy
        
        return location_events
    
    def _calculate_speeds_and_movement(self, location_events: pd.DataFrame) -> pd.DataFrame:
        """Calculate speeds and classify movement types."""
        if len(location_events) < 2:
            location_events['speed_mph'] = 0
            location_events['movement_type'] = 'stationary'
            return location_events
        
        speeds = self._calculate_speeds(location_events)
        location_events['speed_mph'] = speeds
        
        # Classify movement types
        location_events['movement_type'] = location_events['speed_mph'].apply(
            self._classify_movement_type
        )
        
        return location_events
    
    def _calculate_speeds(self, df: pd.DataFrame) -> List[float]:
        """Calculate speed between GPS points with validation and outlier filtering."""
        speeds = []
        
        for i in range(len(df)):
            if i == 0:
                speeds.append(0)
                continue
            
            prev_row = df.iloc[i-1]
            curr_row = df.iloc[i]
            
            # Calculate time difference in seconds
            time_diff = (curr_row['timestamp'] - prev_row['timestamp']).total_seconds()
            
            # Skip if time difference is too small or negative
            if time_diff < CONFIG.min_time_diff_seconds:
                speeds.append(speeds[-1] if speeds else 0)
                continue
            
            # Calculate distance
            distance = self.coord_utils.calculate_distance(
                prev_row['latitude'], prev_row['longitude'],
                curr_row['latitude'], curr_row['longitude']
            )
            
            # Speed in m/s, then convert to mph
            speed_ms = distance / time_diff
            speed_mph = speed_ms * 2.237  # Convert m/s to mph
            
            # Filter out impossible speeds
            if speed_mph > CONFIG.max_reasonable_speed:
                print(f"⚠️  Filtering impossible speed: {speed_mph:.1f} mph at {curr_row['timestamp']}")
                speed_mph = speeds[-1] if speeds else 0
            
            speeds.append(speed_mph)
        
        return speeds
    
    def _classify_movement_type(self, speed_mph: float) -> str:
        """Classify movement type based on speed."""
        if speed_mph < CONFIG.stationary_speed_threshold:
            return 'stationary'
        elif speed_mph < CONFIG.slow_driving_threshold:
            return 'driving_slow'
        else:
            return 'driving_fast'
    
    def _merge_speed_data(self, df: pd.DataFrame, location_events: pd.DataFrame) -> pd.DataFrame:
        """Merge speed data back to main dataframe."""
        df_with_speed = pd.merge_asof(
            df.sort_values('timestamp'), 
            location_events[['timestamp', 'speed_mph', 'movement_type']].sort_values('timestamp'),
            on='timestamp',
            direction='nearest',
            tolerance=pd.Timedelta(minutes=2)
        )
        
        # Fill missing speed data
        df_with_speed['speed_mph'] = df_with_speed['speed_mph'].fillna(0)
        df_with_speed['movement_type'] = df_with_speed['movement_type'].fillna('stationary')
        
        return df_with_speed
    
    def _analyze_movement_statistics(self, df_with_speed: pd.DataFrame, location_events: pd.DataFrame):
        """Analyze and report movement statistics."""
        # Analysis based on timeline events only
        timeline_events = df_with_speed[df_with_speed['source'] == 'timeline']
        
        driving_events = timeline_events[
            (timeline_events['movement_type'].isin(['driving_slow', 'driving_fast'])) &
            (timeline_events['speed_mph'] > CONFIG.driving_threshold)
        ]
        
        phone_while_driving = driving_events[
            driving_events.get('forensic_priority', '').isin(['call_active', 'sms_active', 'social_media_active'])
        ]
        
        # Calculate statistics from location events
        valid_speeds = location_events[location_events['speed_mph'] > 0]['speed_mph']
        avg_speed = valid_speeds.mean() if len(valid_speeds) > 0 else 0
        max_speed = valid_speeds.max() if len(valid_speeds) > 0 else 0
        
        stationary_events = timeline_events[timeline_events['movement_type'] == 'stationary']
        
        print(f"Average speed: {avg_speed:.1f} mph")
        print(f"Maximum speed: {max_speed:.1f} mph")
        print(f"Timeline events while driving: {len(driving_events)}")
        print(f"Timeline events while stationary: {len(stationary_events)}")
        print(f"Phone use while driving (>{CONFIG.driving_threshold} mph): {len(phone_while_driving)}")
        
        if len(phone_while_driving) > 0:
            print(f"\n⚠️  PHONE USE WHILE DRIVING DETECTED:")
            for _, event in phone_while_driving.head(10).iterrows():
                speed = event.get('speed_mph', 0)
                details = str(event.get('details', ''))[:50]
                timestamp = event['timestamp'].strftime('%H:%M:%S')
                event_type = event.get('event_type', 'Unknown')
                print(f"  {timestamp} - {event_type} at {speed:.1f} mph: {details}...")
    
    def get_movement_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get comprehensive movement analysis summary.
        
        Args:
            df: DataFrame with movement analysis
            
        Returns:
            Dictionary with movement statistics
        """
        if 'speed_mph' not in df.columns:
            return {'error': 'No speed data available'}
        
        # Filter valid speed data
        location_events = df[
            (df['latitude'].notna()) & 
            (df['longitude'].notna()) &
            (df['speed_mph'] > 0)
        ]
        
        if location_events.empty:
            return {'error': 'No valid location/speed data'}
        
        speeds = location_events['speed_mph']
        
        summary = {
            'total_location_points': len(location_events),
            'average_speed_mph': speeds.mean(),
            'max_speed_mph': speeds.max(),
            'min_speed_mph': speeds.min(),
            'median_speed_mph': speeds.median(),
            'speed_distribution': {
                'stationary': len(location_events[location_events['speed_mph'] < CONFIG.stationary_speed_threshold]),
                'slow_driving': len(location_events[
                    (location_events['speed_mph'] >= CONFIG.stationary_speed_threshold) &
                    (location_events['speed_mph'] < CONFIG.slow_driving_threshold)
                ]),
                'fast_driving': len(location_events[location_events['speed_mph'] >= CONFIG.slow_driving_threshold])
            }
        }
        
        # Add phone usage while driving if forensic data available
        if 'forensic_priority' in df.columns:
            phone_while_driving = df[
                (df['speed_mph'] > CONFIG.driving_threshold) &
                (df['forensic_priority'].isin(['call_active', 'sms_active', 'social_media_active']))
            ]
            
            summary['phone_while_driving'] = {
                'count': len(phone_while_driving),
                'events': phone_while_driving[['timestamp', 'app_name', 'event_type', 'speed_mph']].to_dict('records')
            }
        
        return summary