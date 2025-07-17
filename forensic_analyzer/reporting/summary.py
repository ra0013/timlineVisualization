"""
Summary statistics generation for forensic analysis.
reporting/summary.py
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import timedelta

from config.settings import CONFIG, PRIORITY


class ForensicSummaryGenerator:
    """Generates comprehensive summary statistics for forensic analysis."""
    
    def generate_summary(
        self, 
        merged_df: pd.DataFrame, 
        collision_time: Optional[pd.Timestamp] = None,
        app_sessions: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analysis summary.
        
        Args:
            merged_df: DataFrame with analyzed forensic data
            collision_time: Time of collision (optional)
            app_sessions: App usage sessions DataFrame (optional)
            
        Returns:
            Dictionary with comprehensive analysis summary
        """
        summary = {
            'metadata': self._generate_metadata(merged_df, collision_time),
            'key_findings': self._generate_key_findings(merged_df, collision_time),
            'priority_distribution': self._analyze_priority_distribution(merged_df),
            'app_usage': self._analyze_app_usage(merged_df),
            'movement_summary': self._analyze_movement_summary(merged_df),
            'session_summary': self._analyze_session_summary(app_sessions),
            'temporal_analysis': self._analyze_temporal_patterns(merged_df, collision_time),
            'risk_indicators': self._identify_risk_indicators(merged_df, collision_time)
        }
        
        return summary
    
    def _generate_metadata(self, merged_df: pd.DataFrame, collision_time: Optional[pd.Timestamp]) -> Dict[str, Any]:
        """Generate metadata about the analysis."""
        time_range = None
        if not merged_df.empty and 'timestamp' in merged_df.columns:
            timestamps = merged_df['timestamp'].dropna()
            if not timestamps.empty:
                time_range = {
                    'start': timestamps.min().isoformat(),
                    'end': timestamps.max().isoformat(),
                    'duration_hours': (timestamps.max() - timestamps.min()).total_seconds() / 3600
                }
        
        return {
            'total_events': len(merged_df),
            'collision_time': collision_time.isoformat() if collision_time else None,
            'analysis_time_range': time_range,
            'data_sources': merged_df.get('source', pd.Series()).value_counts().to_dict() if 'source' in merged_df.columns else {},
            'location_coverage': self._calculate_location_coverage(merged_df)
        }
    
    def _generate_key_findings(self, merged_df: pd.DataFrame, collision_time: Optional[pd.Timestamp]) -> Dict[str, Any]:
        """Generate key findings for executive summary."""
        findings = {
            'total_events': len(merged_df),
            'high_priority_events': 0,
            'phone_while_driving': 0,
            'critical_events': 0,
            'max_speed': 0,
            'avg_speed': 0,
            'apps_used': 0
        }
        
        if merged_df.empty:
            return findings
        
        # Priority analysis
        if 'forensic_priority' in merged_df.columns:
            high_priority = merged_df[merged_df['forensic_priority'].isin(PRIORITY.HIGH_PRIORITY)]
            findings['high_priority_events'] = len(high_priority)
        
        # Phone while driving
        if 'speed_mph' in merged_df.columns and 'forensic_priority' in merged_df.columns:
            phone_driving = merged_df[
                (merged_df['speed_mph'] > CONFIG.driving_threshold) &
                (merged_df['forensic_priority'].isin(PRIORITY.HIGH_PRIORITY))
            ]
            findings['phone_while_driving'] = len(phone_driving)
        
        # Critical events (if collision time available)
        if collision_time and 'timestamp' in merged_df.columns:
            merged_df_copy = merged_df.copy()
            merged_df_copy['time_to_collision'] = (collision_time - merged_df_copy['timestamp']).dt.total_seconds()
            
            critical_events = merged_df_copy[
                (merged_df_copy['time_to_collision'].between(0, 120)) &
                (merged_df_copy.get('forensic_priority', '').isin(PRIORITY.HIGH_PRIORITY))
            ]
            findings['critical_events'] = len(critical_events)
        
        # Speed analysis
        if 'speed_mph' in merged_df.columns:
            valid_speeds = merged_df['speed_mph'].dropna()
            if not valid_speeds.empty:
                findings['max_speed'] = valid_speeds.max()
                findings['avg_speed'] = valid_speeds.mean()
        
        # App usage
        if 'app_name' in merged_df.columns:
            findings['apps_used'] = merged_df['app_name'].nunique()
        
        return findings
    
    def _analyze_priority_distribution(self, merged_df: pd.DataFrame) -> Dict[str, int]:
        """Analyze distribution of events by forensic priority."""
        if 'forensic_priority' not in merged_df.columns:
            return {'high_priority': 0, 'medium_priority': 0, 'low_priority': 0}
        
        priority_counts = merged_df['forensic_priority'].value_counts()
        
        return {
            'high_priority': sum(priority_counts.get(p, 0) for p in PRIORITY.HIGH_PRIORITY),
            'medium_priority': sum(priority_counts.get(p, 0) for p in PRIORITY.MEDIUM_PRIORITY),
            'low_priority': sum(priority_counts.get(p, 0) for p in PRIORITY.LOW_PRIORITY)
        }
    
    def _analyze_app_usage(self, merged_df: pd.DataFrame) -> Dict[str, int]:
        """Analyze app usage frequency."""
        if 'app_name' not in merged_df.columns:
            return {}
        
        return merged_df['app_name'].value_counts().to_dict()
    
    def _analyze_movement_summary(self, merged_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze movement and speed patterns."""
        if 'speed_mph' not in merged_df.columns:
            return {'error': 'No speed data available'}
        
        # Filter valid speed data
        location_events = merged_df[
            (merged_df['latitude'].notna()) & 
            (merged_df['longitude'].notna()) &
            (merged_df['speed_mph'] > 0)
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
        if 'forensic_priority' in merged_df.columns:
            phone_while_driving = merged_df[
                (merged_df['speed_mph'] > CONFIG.driving_threshold) &
                (merged_df['forensic_priority'].isin(PRIORITY.HIGH_PRIORITY))
            ]
            
            summary['phone_while_driving'] = {
                'count': len(phone_while_driving),
                'events': phone_while_driving[['timestamp', 'app_name', 'event_type', 'speed_mph']].to_dict('records')
            }
        
        return summary
    
    def _analyze_session_summary(self, app_sessions: Optional[pd.DataFrame]) -> Dict[str, Any]:
        """Analyze app usage sessions."""
        if app_sessions is None or app_sessions.empty:
            return {'total_sessions': 0, 'apps_used': 0}
        
        summary = {
            'total_sessions': len(app_sessions),
            'apps_used': app_sessions['app_name'].nunique(),
            'total_duration_seconds': app_sessions['duration_seconds'].sum(),
            'average_session_duration': app_sessions['duration_seconds'].mean(),
            'longest_session': {
                'app': app_sessions.loc[app_sessions['duration_seconds'].idxmax(), 'app_name'],
                'duration_seconds': app_sessions['duration_seconds'].max()
            },
            'sessions_by_app': app_sessions.groupby('app_name').agg({
                'duration_seconds': ['count', 'sum', 'mean']
            }).to_dict()
        }
        
        return summary
    
    def _analyze_temporal_patterns(self, merged_df: pd.DataFrame, collision_time: Optional[pd.Timestamp]) -> Dict[str, Any]:
        """Analyze temporal patterns in phone usage."""
        if merged_df.empty or 'timestamp' not in merged_df.columns:
            return {}
        
        analysis = {
            'events_by_hour': self._analyze_hourly_patterns(merged_df),
            'event_frequency': self._analyze_event_frequency(merged_df)
        }
        
        if collision_time:
            analysis['collision_proximity'] = self._analyze_collision_proximity(merged_df, collision_time)
        
        return analysis
    
    def _analyze_hourly_patterns(self, merged_df: pd.DataFrame) -> Dict[int, int]:
        """Analyze phone usage patterns by hour of day."""
        if 'timestamp' not in merged_df.columns:
            return {}
        
        merged_df_copy = merged_df.copy()
        merged_df_copy['hour'] = merged_df_copy['timestamp'].dt.hour
        
        return merged_df_copy['hour'].value_counts().sort_index().to_dict()
    
    def _analyze_event_frequency(self, merged_df: pd.DataFrame) -> Dict[str, float]:
        """Analyze frequency of events over time."""
        if merged_df.empty or 'timestamp' not in merged_df.columns:
            return {}
        
        timestamps = merged_df['timestamp'].dropna().sort_values()
        if len(timestamps) < 2:
            return {}
        
        total_duration = (timestamps.max() - timestamps.min()).total_seconds()
        
        return {
            'events_per_minute': len(timestamps) / (total_duration / 60) if total_duration > 0 else 0,
            'total_duration_minutes': total_duration / 60
        }
    
    def _analyze_collision_proximity(self, merged_df: pd.DataFrame, collision_time: pd.Timestamp) -> Dict[str, Any]:
        """Analyze events based on proximity to collision time."""
        merged_df_copy = merged_df.copy()
        merged_df_copy['time_to_collision'] = (collision_time - merged_df_copy['timestamp']).dt.total_seconds()
        
        # Events in different time windows
        windows = {
            'last_30_seconds': merged_df_copy[merged_df_copy['time_to_collision'].between(0, 30)],
            'last_2_minutes': merged_df_copy[merged_df_copy['time_to_collision'].between(0, 120)],
            'last_10_minutes': merged_df_copy[merged_df_copy['time_to_collision'].between(0, 600)]
        }
        
        proximity_analysis = {}
        
        for window_name, window_data in windows.items():
            proximity_analysis[window_name] = {
                'total_events': len(window_data),
                'high_priority_events': len(window_data[
                    window_data.get('forensic_priority', '').isin(PRIORITY.HIGH_PRIORITY)
                ]) if 'forensic_priority' in window_data.columns else 0
            }
        
        return proximity_analysis
    
    def _identify_risk_indicators(self, merged_df: pd.DataFrame, collision_time: Optional[pd.Timestamp]) -> List[Dict[str, Any]]:
        """Identify potential risk indicators from the data."""
        risk_indicators = []
        
        if merged_df.empty:
            return risk_indicators
        
        # High frequency phone usage
        if 'forensic_priority' in merged_df.columns:
            high_priority_count = len(merged_df[merged_df['forensic_priority'].isin(PRIORITY.HIGH_PRIORITY)])
            if high_priority_count > 10:  # Threshold for high usage
                risk_indicators.append({
                    'type': 'high_phone_usage',
                    'description': f'High frequency of active phone interactions ({high_priority_count} events)',
                    'severity': 'medium'
                })
        
        # Phone usage while driving
        if 'speed_mph' in merged_df.columns and 'forensic_priority' in merged_df.columns:
            phone_driving = merged_df[
                (merged_df['speed_mph'] > CONFIG.driving_threshold) &
                (merged_df['forensic_priority'].isin(PRIORITY.HIGH_PRIORITY))
            ]
            
            if len(phone_driving) > 0:
                risk_indicators.append({
                    'type': 'phone_while_driving',
                    'description': f'Phone usage while vehicle in motion ({len(phone_driving)} instances)',
                    'severity': 'high'
                })
        
        # Critical timing (if collision time available)
        if collision_time and 'timestamp' in merged_df.columns:
            merged_df_copy = merged_df.copy()
            merged_df_copy['time_to_collision'] = (collision_time - merged_df_copy['timestamp']).dt.total_seconds()
            
            critical_events = merged_df_copy[
                (merged_df_copy['time_to_collision'].between(0, 30)) &
                (merged_df_copy.get('forensic_priority', '').isin(PRIORITY.HIGH_PRIORITY))
            ]
            
            if len(critical_events) > 0:
                risk_indicators.append({
                    'type': 'critical_timing',
                    'description': f'Phone activity in final 30 seconds before collision ({len(critical_events)} events)',
                    'severity': 'critical'
                })
        
        # High speed events
        if 'speed_mph' in merged_df.columns:
            high_speed_events = merged_df[merged_df['speed_mph'] > 70]  # Above 70 mph
            if len(high_speed_events) > 0:
                max_speed = merged_df['speed_mph'].max()
                risk_indicators.append({
                    'type': 'high_speed',
                    'description': f'High speed driving detected (max: {max_speed:.1f} mph)',
                    'severity': 'medium'
                })
        
        return risk_indicators
    
    def _calculate_location_coverage(self, merged_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate location data coverage statistics."""
        if 'location_source' not in merged_df.columns:
            return {'coverage': 'unknown'}
        
        location_sources = merged_df['location_source'].value_counts()
        total_events = len(merged_df)
        
        coverage = {
            'total_events': total_events,
            'events_with_location': len(merged_df[
                (merged_df['latitude'].notna()) & (merged_df['longitude'].notna())
            ]),
            'location_sources': location_sources.to_dict(),
            'coverage_percentage': (len(merged_df[
                (merged_df['latitude'].notna()) & (merged_df['longitude'].notna())
            ]) / total_events * 100) if total_events > 0 else 0
        }
        
        return coverage