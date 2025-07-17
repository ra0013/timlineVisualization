"""
Phone usage pattern analysis for forensic investigations.
analysis\phone_usage.py
"""

import pandas as pd
from datetime import timedelta
from typing import Optional, Dict, Any, List

from config.settings import CONFIG, PRIORITY
from data.parsers import ForensicEventClassifier


class PhoneUsageAnalyzer:
    """Analyzes phone usage patterns for forensic significance."""
    
    def __init__(self):
        self.classifier = ForensicEventClassifier()
        self.collision_time: Optional[pd.Timestamp] = None
    
    def set_collision_time(self, collision_time: pd.Timestamp):
        """Set collision time for temporal analysis."""
        self.collision_time = collision_time
    
    def analyze_phone_usage_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze phone usage patterns with forensic classification.
        
        Args:
            df: DataFrame with timeline events
            
        Returns:
            DataFrame with forensic analysis added
        """
        if df.empty:
            return df
        
        print(f"\n=== FORENSIC PHONE USAGE ANALYSIS ===")
        
        # Classify events by forensic significance
        df['forensic_priority'] = df.apply(
            lambda row: self.classifier.classify_forensic_event(
                row.get('event_type', ''),
                row.get('details', ''),
                row.get('direction', ''),
                row.get('app_name', '')
            ), axis=1
        )
        
        # Analyze patterns
        self._analyze_priority_distribution(df)
        self._analyze_app_usage_frequency(df)
        self._analyze_critical_timing(df)
        
        return df
    
    def _analyze_priority_distribution(self, df: pd.DataFrame):
        """Analyze distribution of events by forensic priority."""
        priority_counts = df['forensic_priority'].value_counts()
        
        high_priority_count = sum(
            priority_counts.get(priority, 0) 
            for priority in PRIORITY.HIGH_PRIORITY
        )
        medium_priority_count = priority_counts.get('notification_passive', 0)
        low_priority_count = sum(
            priority_counts.get(priority, 0) 
            for priority in PRIORITY.LOW_PRIORITY
        )
        
        print(f"HIGH PRIORITY (Active Use): {high_priority_count}")
        print(f"MEDIUM PRIORITY (Notifications): {medium_priority_count}")
        print(f"LOW PRIORITY (Background): {low_priority_count}")
        
        return {
            'high_priority': high_priority_count,
            'medium_priority': medium_priority_count,
            'low_priority': low_priority_count
        }
    
    def _analyze_app_usage_frequency(self, df: pd.DataFrame):
        """Analyze frequency of app usage."""
        app_usage = df['app_name'].value_counts()
        print(f"\nApp Usage Frequency:")
        for app, count in app_usage.head(10).items():
            print(f"  {app}: {count} events")
        
        return app_usage.to_dict()
    
    def _analyze_critical_timing(self, df: pd.DataFrame):
        """Analyze phone usage in critical time windows."""
        if not self.collision_time:
            return
        
        df['time_to_collision'] = (self.collision_time - df['timestamp']).dt.total_seconds()
        
        # Events in critical windows
        critical_30s = df[df['time_to_collision'].between(0, 30)]
        critical_2min = df[df['time_to_collision'].between(0, 120)]
        
        print(f"\nCRITICAL TIMING:")
        print(f"Phone events in last 30 seconds: {len(critical_30s)}")
        print(f"Phone events in last 2 minutes: {len(critical_2min)}")
        
        # Show critical events
        high_priority_critical = critical_2min[
            critical_2min['forensic_priority'].isin(PRIORITY.HIGH_PRIORITY)
        ]
        
        if len(high_priority_critical) > 0:
            print(f"\n⚠️  HIGH PRIORITY EVENTS IN CRITICAL WINDOW:")
            for _, event in high_priority_critical.iterrows():
                duration_info = ""
                if event.get('app_session_duration'):
                    duration_info = f" ({event['app_session_duration']:.0f}s session)"
                
                details_preview = str(event['details'])[:50]
                print(f"  {event['timestamp'].strftime('%H:%M:%S')} - {event['app_name']}{duration_info}: {details_preview}...")
    
    def analyze_phone_use_while_driving(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analyze phone usage while driving (speed > threshold).
        
        Args:
            df: DataFrame with speed and phone usage data
            
        Returns:
            List of phone usage events while driving
        """
        if 'speed_mph' not in df.columns:
            return []
        
        # Filter for driving events with phone usage
        driving_events = df[
            (df['speed_mph'] > CONFIG.driving_threshold) &
            (df['forensic_priority'].isin(PRIORITY.HIGH_PRIORITY))
        ]
        
        phone_while_driving = []
        
        for _, event in driving_events.iterrows():
            phone_while_driving.append({
                'timestamp': event['timestamp'],
                'app_name': event['app_name'],
                'event_type': event['event_type'],
                'speed_mph': event['speed_mph'],
                'details': event['details'],
                'forensic_priority': event['forensic_priority']
            })
        
        if phone_while_driving:
            print(f"\n⚠️  PHONE USE WHILE DRIVING DETECTED:")
            for event in phone_while_driving[:10]:  # Limit output
                speed = event['speed_mph']
                details = event['details'][:50]
                timestamp = event['timestamp'].strftime('%H:%M:%S')
                print(f"  {timestamp} - {event['event_type']} at {speed:.1f} mph: {details}...")
        
        return phone_while_driving
    
    def filter_critical_timeframe(
        self, 
        df: pd.DataFrame, 
        minutes_before: int = CONFIG.default_analysis_window_before,
        minutes_after: int = CONFIG.default_analysis_window_after
    ) -> pd.DataFrame:
        """
        Filter events to critical timeframe around collision.
        
        Args:
            df: DataFrame with events
            minutes_before: Minutes before collision to include
            minutes_after: Minutes after collision to include
            
        Returns:
            Filtered DataFrame
        """
        if not self.collision_time:
            return df
        
        start_time = self.collision_time - timedelta(minutes=minutes_before)
        end_time = self.collision_time + timedelta(minutes=minutes_after)
        
        critical_events = df[
            (df['timestamp'] >= start_time) & 
            (df['timestamp'] <= end_time)
        ].copy()
        
        print(f"✓ Filtered to critical timeframe: {len(critical_events)} events ({minutes_before}min before to {minutes_after}min after)")
        return critical_events
    
    def get_usage_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get comprehensive phone usage summary.
        
        Args:
            df: DataFrame with analyzed phone usage data
            
        Returns:
            Dictionary with usage statistics
        """
        summary = {
            'total_events': len(df),
            'priority_distribution': self._analyze_priority_distribution(df),
            'app_usage': self._analyze_app_usage_frequency(df),
            'phone_while_driving': [],
            'critical_events': []
        }
        
        # Add driving analysis if speed data available
        if 'speed_mph' in df.columns:
            summary['phone_while_driving'] = self.analyze_phone_use_while_driving(df)
        
        # Add critical timing analysis if collision time set
        if self.collision_time:
            df['time_to_collision'] = (self.collision_time - df['timestamp']).dt.total_seconds()
            
            critical_events = df[
                (df['time_to_collision'].between(0, 120)) &
                (df['forensic_priority'].isin(PRIORITY.HIGH_PRIORITY))
            ]
            
            summary['critical_events'] = critical_events.to_dict('records')
        
        return summary