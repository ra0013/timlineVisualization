"""
KML generation for forensic analysis visualization.
visualization/kml_generator.py
"""

import pandas as pd
import simplekml
from typing import Optional, Tuple, List, Dict, Any

from config.settings import CONFIG, KML_STYLES, PRIORITY
from visualization.styles import KMLStyleManager


class ForensicKMLGenerator:
    """Generates forensic KML files for Google Earth visualization."""
    
    def __init__(self):
        self.kml = simplekml.Kml()
        self.kml.name = "Distracted Driving Forensic Analysis"
        self.style_manager = KMLStyleManager()
        self.collision_time: Optional[pd.Timestamp] = None
        self.collision_location: Optional[Tuple[float, float]] = None
        self.app_sessions: pd.DataFrame = pd.DataFrame()
    
    def set_collision_details(
        self, 
        collision_time: pd.Timestamp, 
        collision_lat: Optional[float] = None, 
        collision_lon: Optional[float] = None
    ):
        """Set collision time and location for visualization."""
        self.collision_time = collision_time
        if collision_lat and collision_lon:
            self.collision_location = (collision_lat, collision_lon)
    
    def set_app_sessions(self, app_sessions: pd.DataFrame):
        """Set app sessions data for visualization."""
        self.app_sessions = app_sessions.copy() if not app_sessions.empty else pd.DataFrame()
    
    def create_forensic_kml(
        self, 
        merged_df: pd.DataFrame, 
        output_path: str = "forensic_analysis.kml"
    ) -> bool:
        """
        Create comprehensive forensic KML with all analysis components.
        
        Args:
            merged_df: DataFrame with analyzed forensic data
            output_path: Output KML file path
            
        Returns:
            True if KML created successfully, False otherwise
        """
        if merged_df is None or merged_df.empty:
            print("✗ No data to create KML")
            return False
        
        print(f"\n=== CREATING FORENSIC KML ===")
        
        try:
            # Initialize fresh KML
            self.kml = simplekml.Kml()
            self.kml.name = "Distracted Driving Forensic Analysis"
            
            # Apply styles
            self.style_manager.apply_styles_to_kml(self.kml)
            
            # Create folder structure
            folders = self._create_folder_structure()
            
            # Add collision marker if available
            if self.collision_location:
                self._add_collision_marker(folders['collision'])
            
            # Add event markers
            events_added = self._add_event_markers(merged_df, folders)
            
            # Add app session visualizations
            if not self.app_sessions.empty:
                self._add_app_session_visualizations(folders['app_sessions'], merged_df)
            
            # Add movement path
            self._add_movement_path(merged_df, folders['movement'])
            
            # Save KML
            self.kml.save(output_path)
            
            print(f"✓ Forensic KML saved: {output_path}")
            print(f"✓ Events with location: {events_added}")
            print(f"✓ Total analyzed events: {len(merged_df)}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error creating KML: {e}")
            return False
    
    def _create_folder_structure(self) -> Dict[str, Any]:
        """Create organized folder structure for KML."""
        folders = {
            'high_priority': self.kml.newfolder(name="🔴 HIGH PRIORITY - Active Phone Use"),
            'app_sessions': self.kml.newfolder(name="📱 APP USAGE SESSIONS"),
            'medium_priority': self.kml.newfolder(name="🟡 MEDIUM PRIORITY - Notifications"),
            'low_priority': self.kml.newfolder(name="🔵 LOW PRIORITY - Background Events"),
            'movement': self.kml.newfolder(name="🚗 MOVEMENT ANALYSIS"),
            'collision': self.kml.newfolder(name="💥 COLLISION SITE") if self.collision_location else None
        }
        
        return {k: v for k, v in folders.items() if v is not None}
    
    def _add_collision_marker(self, collision_folder):
        """Add collision site marker."""
        if not self.collision_location:
            return
        
        collision_marker = collision_folder.newpoint()
        collision_marker.name = "COLLISION LOCATION"
        collision_marker.coords = [self.collision_location]
        collision_marker.style = self.style_manager.get_style('collision_site')
        
        description = f"<b>Collision Time:</b> {self.collision_time.strftime('%Y-%m-%d %H:%M:%S')}<br/>"
        description += f"<b>CRITICAL EVIDENCE LOCATION</b>"
        collision_marker.description = description
    
    def _add_event_markers(self, merged_df: pd.DataFrame, folders: Dict[str, Any]) -> int:
        """Add individual event markers to appropriate folders."""
        events_added = 0
        
        for _, event in merged_df.iterrows():
            if pd.isna(event['latitude']) or pd.isna(event['longitude']):
                continue
            
            # Determine folder based on forensic priority
            forensic_priority = event.get('forensic_priority', 'default')
            folder = self._get_event_folder(forensic_priority, folders)
            
            if folder is None:
                continue
            
            # Create placemark
            placemark = self._create_event_placemark(event, folder)
            if placemark:
                events_added += 1
        
        return events_added
    
    def _get_event_folder(self, forensic_priority: str, folders: Dict[str, Any]):
        """Get appropriate folder for event based on priority."""
        if forensic_priority in PRIORITY.HIGH_PRIORITY:
            return folders.get('high_priority')
        elif forensic_priority in PRIORITY.MEDIUM_PRIORITY:
            return folders.get('medium_priority')
        else:
            return folders.get('low_priority')
    
    def _create_event_placemark(self, event: pd.Series, folder) -> Optional[Any]:
        """Create individual event placemark."""
        try:
            placemark = folder.newpoint()
            
            # Enhanced name with app info
            app_info = f" ({event['app_name']})" if event.get('app_name') and event['app_name'] != 'Unknown' else ""
            time_info = f" [{event.get('time_annotation', '').upper()}]" if event.get('time_annotation') else ""
            placemark.name = f"{event['event_type']}{app_info}{time_info} - {event['timestamp'].strftime('%H:%M:%S')}"
            
            placemark.coords = [(event['longitude'], event['latitude'])]
            placemark.timestamp.when = event['timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Enhanced description
            placemark.description = self._create_event_description(event)
            
            # Apply style
            forensic_priority = event.get('forensic_priority', 'default')
            placemark.style = self.style_manager.get_style(forensic_priority)
            
            return placemark
            
        except Exception as e:
            print(f"  Error creating placemark for event: {e}")
            return None
    
    def _create_event_description(self, event: pd.Series) -> str:
        """Create detailed description for event placemark."""
        forensic_priority = event.get('forensic_priority', 'default')
        description_parts = [
            f"<b> FORENSIC PRIORITY:</b> {forensic_priority.upper()}",
            f"<b>App:</b> {event.get('app_name', 'Unknown')}",
            f"<b>Time:</b> {event['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
            f"<b>Event Type:</b> {event['event_type']}",
            f"<b>Direction:</b> {event.get('direction', 'N/A')}",
        ]
        
        # Add session information
        if event.get('time_annotation'):
            description_parts.append(f"<b>Session Point:</b> {event['time_annotation'].upper()}")
        
        if event.get('app_session_duration'):
            duration_min = event['app_session_duration'] / 60
            description_parts.append(f"<b>Session Duration:</b> {duration_min:.1f} minutes")
        
        # Add timing relative to collision
        if self.collision_time:
            time_diff = (self.collision_time - event['timestamp']).total_seconds()
            if time_diff > 0:
                description_parts.append(f"<b>Time to Collision:</b> {time_diff:.0f} seconds")
        
        # Add speed information
        if event.get('speed_mph'):
            description_parts.append(f"<b>Vehicle Speed:</b> {event['speed_mph']:.1f} mph")
            description_parts.append(f"<b>Movement:</b> {event.get('movement_type', 'unknown')}")
        
        # Add contact information
        if event.get('contact') and str(event['contact']) != 'nan':
            description_parts.append(f"<b>Contact:</b> {event['contact']}")
        
        # Add event details
        if event.get('details') and str(event['details']) != 'nan':
            details = str(event['details'])[:200]  # Limit length
            description_parts.append(f"<b>Details:</b> {details}")
        
        description_parts.append(f"<b>Location Source:</b> {event.get('location_source', 'unknown')}")
        
        return "<br/>".join(description_parts)
    
    def _add_app_session_visualizations(self, app_sessions_folder, merged_df: pd.DataFrame):
        """Create visual representations of app usage sessions."""
        if self.app_sessions.empty:
            print("No app sessions to visualize")
            return
        
        print(f"Creating app usage session visualizations for {len(self.app_sessions)} sessions")
        sessions_visualized = 0
        
        for _, session in self.app_sessions.iterrows():
            session_marker = self._create_session_marker(session, merged_df, app_sessions_folder)
            if session_marker:
                sessions_visualized += 1
        
        print(f"✓ Visualized {sessions_visualized} app sessions with location data")
    
    def _create_session_marker(self, session: pd.Series, merged_df: pd.DataFrame, folder) -> Optional[Any]:
        """Create marker for individual app session."""
        # Get session location
        start_lat, start_lon = session.get('start_lat'), session.get('start_lon')
        
        # If session doesn't have coordinates, try to find them from merged_df
        if pd.isna(start_lat) or pd.isna(start_lon):
            session_events = merged_df[
                (merged_df['timestamp'] >= session['start_time'] - pd.Timedelta(minutes=1)) &
                (merged_df['timestamp'] <= session['start_time'] + pd.Timedelta(minutes=1)) &
                (merged_df['latitude'].notna()) &
                (merged_df['longitude'].notna())
            ]
            
            if not session_events.empty:
                first_event = session_events.iloc[0]
                start_lat, start_lon = first_event['latitude'], first_event['longitude']
        
        # Skip sessions without location data
        if pd.isna(start_lat) or pd.isna(start_lon):
            return None
        
        try:
            duration_min = session['duration_seconds'] / 60
            
            # Create session marker
            session_marker = folder.newpoint()
            session_marker.name = f"{session['app_name']} - {duration_min:.1f} min session"
            session_marker.coords = [(start_lon, start_lat)]
            session_marker.timestamp.when = session['start_time'].strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Calculate average speed during session
            avg_speed = self._calculate_session_speed(session, merged_df)
            
            # Create description
            session_marker.description = self._create_session_description(session, avg_speed)
            
            # Apply style based on whether used while driving
            style_name = 'critical_window' if avg_speed > CONFIG.driving_threshold else 'notification_passive'
            session_marker.style = self.style_manager.get_style(style_name)
            
            return session_marker
            
        except Exception as e:
            print(f"  Error creating session marker: {e}")
            return None
    
    def _calculate_session_speed(self, session: pd.Series, merged_df: pd.DataFrame) -> float:
        """Calculate average speed during an app session."""
        session_events = merged_df[
            (merged_df['timestamp'] >= session['start_time']) &
            (merged_df['timestamp'] <= session['end_time'])
        ]
        
        if not session_events.empty and 'speed_mph' in session_events.columns:
            valid_speeds = session_events['speed_mph'].dropna()
            if not valid_speeds.empty:
                return valid_speeds.mean()
        
        return 0.0
    
    def _create_session_description(self, session: pd.Series, avg_speed: float) -> str:
        """Create description for app session marker."""
        duration_min = session['duration_seconds'] / 60
        
        description_parts = [
            f"<b>📱 APP USAGE SESSION</b>",
            f"<b>App:</b> {session['app_name']}",
            f"<b>Duration:</b> {duration_min:.1f} minutes ({session['duration_seconds']:.0f} seconds)",
            f"<b>Start:</b> {session['start_time'].strftime('%Y-%m-%d %H:%M:%S')}",
            f"<b>End:</b> {session['end_time'].strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        
        if avg_speed > 0:
            description_parts.append(f"<b>Average Speed During Session:</b> {avg_speed:.1f} mph")
        
        if self.collision_time:
            time_to_collision = (self.collision_time - session['start_time']).total_seconds()
            if time_to_collision > 0:
                description_parts.append(f"<b>Time to Collision:</b> {time_to_collision:.0f} seconds")
        
        if avg_speed > CONFIG.driving_threshold:
            description_parts.append(f"<b> WARNING: App used while driving!</b>")
        
        # Add session details
        if session.get('details') and str(session['details']) != 'nan':
            details = str(session['details'])[:100]
            description_parts.append(f"<b>Content:</b> {details}...")
        
        return "<br/>".join(description_parts)
    
    def _add_movement_path(self, merged_df: pd.DataFrame, movement_folder):
        """Create movement path visualization."""
        if 'location_source' not in merged_df.columns:
            print("No location source data available for movement path")
            return
        
        # Get high-quality location points
        location_events = merged_df[
            (merged_df['location_source'] == 'location_tracking') &
            (merged_df['latitude'].notna()) & 
            (merged_df['longitude'].notna())
        ].copy()
        
        if location_events.empty:
            print("No location tracking data available for movement path")
            return
        
        # Filter for GPS accuracy
        if 'accuracy' in location_events.columns:
            good_gps = location_events[
                (location_events['accuracy'].isna()) | 
                (location_events['accuracy'] <= CONFIG.high_accuracy_gps)
            ].copy()
            
            if len(good_gps) >= 2:
                location_events = good_gps
                print(f"Using {len(location_events)} high-accuracy GPS points for movement path")
        
        # Remove duplicates and sort
        location_events = location_events.drop_duplicates(subset=['timestamp', 'latitude', 'longitude'])
        location_events = location_events.sort_values('timestamp')
        
        # Subsample for performance
        if len(location_events) > CONFIG.max_location_points_for_path:
            step = len(location_events) // CONFIG.max_location_points_for_path
            location_events = location_events.iloc[::step]
            print(f"Subsampled to {len(location_events)} points for performance")
        
        if len(location_events) < 2:
            print("Insufficient GPS data for movement path")
            return
        
        # Create path line
        self._create_path_line(location_events, movement_folder)
        
        # Add speed markers
        if 'speed_mph' in location_events.columns:
            self._add_speed_markers(location_events, movement_folder)
    
    def _create_path_line(self, location_events: pd.DataFrame, movement_folder):
        """Create the main movement path line."""
        linestring = movement_folder.newlinestring(name="Vehicle Movement Path")
        coords = [(row['longitude'], row['latitude']) for _, row in location_events.iterrows()]
        linestring.coords = coords
        linestring.style.linestyle.color = simplekml.Color.blue
        linestring.style.linestyle.width = 3
    
    def _add_speed_markers(self, location_events: pd.DataFrame, movement_folder):
        """Add speed markers along the movement path."""
        # Sample speed markers (don't add for every point)
        speed_markers = location_events[
            (location_events['speed_mph'] > 10) &  # Only when moving
            (location_events.index % 10 == 0)  # Every 10th point
        ]
        
        for _, point in speed_markers.iterrows():
            speed_marker = movement_folder.newpoint()
            speed_marker.name = f"Speed: {point['speed_mph']:.1f} mph"
            speed_marker.coords = [(point['longitude'], point['latitude'])]
            speed_marker.timestamp.when = point['timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ')
            
            movement_type = point.get('movement_type', 'driving_slow')
            speed_marker.style = self.style_manager.get_style(movement_type)
            
            speed_marker.description = (
                f"<b>Speed:</b> {point['speed_mph']:.1f} mph<br/>"
                f"<b>Time:</b> {point['timestamp'].strftime('%H:%M:%S')}"
            )