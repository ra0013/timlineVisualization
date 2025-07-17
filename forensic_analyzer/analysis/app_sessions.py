"""
App usage session analysis for forensic investigations.
analysis/app_sessions.py
"""

import pandas as pd
from datetime import timedelta
from typing import List, Dict, Any, Optional

from config.settings import CONFIG


class AppSessionAnalyzer:
    """Analyzes app usage sessions and their duration."""
    
    def __init__(self):
        self.app_sessions = pd.DataFrame()
        self.collision_time: Optional[pd.Timestamp] = None
    
    def set_collision_time(self, collision_time: pd.Timestamp):
        """Set collision time for temporal analysis."""
        self.collision_time = collision_time
    
    def analyze_app_usage_duration(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze app usage duration from start/end time pairs.
        
        Args:
            df: DataFrame with timeline events including time annotations
            
        Returns:
            DataFrame with session duration information added
        """
        print(f"\n=== APP USAGE DURATION ANALYSIS ===")
        
        # Find start/end pairs
        start_events = df[df['time_annotation'] == 'start'].copy()
        end_events = df[df['time_annotation'] == 'end'].copy()
        
        print(f"Found {len(start_events)} app start events")
        print(f"Found {len(end_events)} app end events")
        
        app_sessions = []
        
        for _, start_event in start_events.iterrows():
            # Find matching end event
            matching_ends = end_events[
                (end_events['app_name'] == start_event['app_name']) &
                (end_events['timestamp'] > start_event['timestamp']) &
                (end_events['timestamp'] <= start_event['timestamp'] + timedelta(hours=1))  # Within 1 hour
            ]
            
            if not matching_ends.empty:
                end_event = matching_ends.iloc[0]  # Take the first matching end
                
                duration_seconds = (end_event['timestamp'] - start_event['timestamp']).total_seconds()
                
                app_sessions.append({
                    'app_name': start_event['app_name'],
                    'start_time': start_event['timestamp'],
                    'end_time': end_event['timestamp'],
                    'duration_seconds': duration_seconds,
                    'start_lat': start_event['latitude'],
                    'start_lon': start_event['longitude'],
                    'end_lat': end_event['latitude'],
                    'end_lon': end_event['longitude'],
                    'event_type': start_event['event_type'],
                    'details': start_event['details']
                })
        
        self.app_sessions = pd.DataFrame(app_sessions)
        
        if not self.app_sessions.empty:
            print(f"✓ Found {len(self.app_sessions)} app usage sessions")
            
            # Summary by app
            self._print_session_summary()
            
            # Add session info back to main dataframe
            df = self._add_session_info_to_dataframe(df)
        else:
            print("No app usage sessions found")
            self.app_sessions = pd.DataFrame()
        
        return df
    
    def _print_session_summary(self):
        """Print summary of app usage sessions."""
        app_summary = self.app_sessions.groupby('app_name').agg({
            'duration_seconds': ['count', 'sum', 'mean'],
            'start_time': ['min', 'max']
        }).round(2)
        
        print(f"\nApp Usage Summary:")
        for app in app_summary.index:
            count = app_summary.loc[app, ('duration_seconds', 'count')]
            total_time = app_summary.loc[app, ('duration_seconds', 'sum')]
            avg_time = app_summary.loc[app, ('duration_seconds', 'mean')]
            print(f"  {app}: {count} sessions, {total_time:.0f}s total, {avg_time:.0f}s average")
    
    def _add_session_info_to_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add session information back to the main dataframe."""
        df['app_session_duration'] = None
        df['session_id'] = None
        
        for idx, session in self.app_sessions.iterrows():
            # Mark start event
            start_mask = (
                (df['timestamp'] == session['start_time']) & 
                (df['app_name'] == session['app_name'])
            )
            df.loc[start_mask, 'app_session_duration'] = session['duration_seconds']
            df.loc[start_mask, 'session_id'] = idx
            
            # Mark end event
            end_mask = (
                (df['timestamp'] == session['end_time']) & 
                (df['app_name'] == session['app_name'])
            )
            df.loc[end_mask, 'app_session_duration'] = session['duration_seconds']
            df.loc[end_mask, 'session_id'] = idx
        
        return df
    
    def analyze_sessions_while_driving(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analyze app sessions that occurred while driving.
        
        Args:
            df: DataFrame with speed and session data
            
        Returns:
            List of sessions that occurred while driving
        """
        if self.app_sessions.empty or 'speed_mph' not in df.columns:
            return []
        
        sessions_while_driving = []
        
        for _, session in self.app_sessions.iterrows():
            # Check if session occurred while driving
            session_events = df[
                (df['timestamp'] >= session['start_time']) &
                (df['timestamp'] <= session['end_time']) &
                (df['app_name'] == session['app_name'])
            ]
            
            if not session_events.empty and 'speed_mph' in session_events.columns:
                avg_speed = session_events['speed_mph'].mean()
                
                if avg_speed > CONFIG.driving_threshold:
                    session_info = session.to_dict()
                    session_info['avg_speed_during_session'] = avg_speed
                    sessions_while_driving.append(session_info)
        
        if sessions_while_driving:
            print(f"\n⚠️  APP USAGE WHILE DRIVING:")
            for session in sessions_while_driving:
                duration_min = session['duration_seconds'] / 60
                avg_speed = session['avg_speed_during_session']
                start_time = session['start_time'].strftime('%H:%M:%S')
                end_time = session['end_time'].strftime('%H:%M:%S')
                
                print(f"  {session['app_name']}: {duration_min:.1f} minutes at {avg_speed:.1f} mph")
                print(f"    {start_time} - {end_time}")
        
        return sessions_while_driving
    
    def get_critical_sessions(self, minutes_before_collision: int = 10) -> List[Dict[str, Any]]:
        """
        Get app sessions that occurred in critical time window before collision.
        
        Args:
            minutes_before_collision: Minutes before collision to consider critical
            
        Returns:
            List of critical app sessions
        """
        if self.app_sessions.empty or not self.collision_time:
            return []
        
        critical_start_time = self.collision_time - timedelta(minutes=minutes_before_collision)
        
        critical_sessions = self.app_sessions[
            (self.app_sessions['start_time'] >= critical_start_time) &
            (self.app_sessions['start_time'] <= self.collision_time)
        ]
        
        return critical_sessions.to_dict('records')
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive app session summary.
        
        Returns:
            Dictionary with session statistics
        """
        if self.app_sessions.empty:
            return {'total_sessions': 0, 'apps_used': 0}
        
        summary = {
            'total_sessions': len(self.app_sessions),
            'apps_used': self.app_sessions['app_name'].nunique(),
            'total_duration_seconds': self.app_sessions['duration_seconds'].sum(),
            'average_session_duration': self.app_sessions['duration_seconds'].mean(),
            'longest_session': {
                'app': self.app_sessions.loc[self.app_sessions['duration_seconds'].idxmax(), 'app_name'],
                'duration_seconds': self.app_sessions['duration_seconds'].max()
            },
            'sessions_by_app': self.app_sessions.groupby('app_name').agg({
                'duration_seconds': ['count', 'sum', 'mean']
            }).to_dict()
        }
        
        # Add critical sessions if collision time is set
        if self.collision_time:
            critical_sessions = self.get_critical_sessions()
            summary['critical_sessions'] = {
                'count': len(critical_sessions),
                'sessions': critical_sessions
            }
        
        return summary
    
    def get_app_sessions_dataframe(self) -> pd.DataFrame:
        """
        Get the app sessions DataFrame.
        
        Returns:
            DataFrame with app session data
        """
        return self.app_sessions.copy() if not self.app_sessions.empty else pd.DataFrame()
    
    def has_sessions(self) -> bool:
        """
        Check if any app sessions were found.
        
        Returns:
            True if sessions exist, False otherwise
        """
        return not self.app_sessions.empty