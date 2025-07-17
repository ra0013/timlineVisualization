"""
Enhanced PDF report generation for forensic analysis.
reporting/pdf_generator.py
"""

from fpdf import FPDF
from datetime import datetime
import pandas as pd
from typing import Optional, Tuple, Dict, Any, List

from config.settings import CONFIG, PRIORITY
from reporting.summary import ForensicSummaryGenerator


class ForensicReportGenerator:
    """Generates comprehensive PDF reports for forensic analysis."""
    
    def __init__(self):
        self.collision_time: Optional[pd.Timestamp] = None
        self.collision_location: Optional[Tuple[float, float]] = None
        self.app_sessions: pd.DataFrame = pd.DataFrame()
        self.summary_generator = ForensicSummaryGenerator()
    
    def set_collision_details(
        self, 
        collision_time: Optional[pd.Timestamp], 
        collision_location: Optional[Tuple[float, float]]
    ):
        """Set collision details for the report."""
        self.collision_time = collision_time
        self.collision_location = collision_location
    
    def set_app_sessions(self, app_sessions: pd.DataFrame):
        """Set app sessions data for the report."""
        self.app_sessions = app_sessions.copy() if not app_sessions.empty else pd.DataFrame()
    
    def generate_report(self, merged_df: pd.DataFrame, output_pdf: str = "forensic_report.pdf") -> bool:
        """
        Generate comprehensive forensic analysis PDF report.
        
        Args:
            merged_df: DataFrame with analyzed forensic data
            output_pdf: Output PDF filename
            
        Returns:
            True if report generated successfully, False otherwise
        """
        if merged_df is None or merged_df.empty:
            print("✗ No data to generate PDF report")
            return False
        
        print("\n=== GENERATING PDF REPORT ===")
        
        try:
            # Generate analysis summary
            analysis_summary = self.summary_generator.generate_summary(
                merged_df, self.collision_time, self.app_sessions
            )
            
            # Create PDF
            pdf = self._create_pdf_document()
            
            # Add report sections
            self._add_title_page(pdf)
            self._add_executive_summary(pdf, analysis_summary)
            self._add_event_analysis(pdf, merged_df, analysis_summary)
            self._add_movement_analysis(pdf, merged_df, analysis_summary)
            self._add_app_usage_analysis(pdf, analysis_summary)
            self._add_critical_timeline(pdf, merged_df)
            self._add_conclusions(pdf, analysis_summary)
            
            # Save PDF
            pdf.output(output_pdf)
            print(f"✓ PDF report saved: {output_pdf}")
            return True
            
        except Exception as e:
            print(f"✗ Error generating PDF report: {e}")
            return False
    
    def _create_pdf_document(self) -> FPDF:
        """Create and configure PDF document."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(20, 20, 20)
        return pdf
    
    def _add_title_page(self, pdf: FPDF):
        """Add professional title page."""
        pdf.add_page()
        
        # Title
        pdf.set_font("Helvetica", "B", 24)
        pdf.ln(40)
        pdf.cell(0, 15, "FORENSIC ANALYSIS REPORT", ln=True, align="C")
        pdf.ln(10)
        
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, "Distracted Driving Investigation", ln=True, align="C")
        pdf.ln(20)
        
        # Case information
        pdf.set_font("Helvetica", "", 14)
        pdf.cell(0, 10, f"Report Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}", ln=True, align="C")
        
        if self.collision_time:
            pdf.ln(5)
            pdf.cell(0, 10, f"Incident Date: {self.collision_time.strftime('%B %d, %Y at %H:%M:%S')}", ln=True, align="C")
        
        if self.collision_location:
            lat, lon = self.collision_location
            pdf.ln(5)
            pdf.cell(0, 10, f"Incident Location: {lat:.5f}, {lon:.5f}", ln=True, align="C")
            
            # Add Google Maps link
            google_maps_url = f"https://maps.google.com/?q={lat},{lon}"
            pdf.ln(5)
            pdf.set_text_color(0, 0, 255)
            pdf.cell(0, 10, "View Location on Map", ln=True, align="C", link=google_maps_url)
            pdf.set_text_color(0, 0, 0)
        
        # Add disclaimer
        pdf.ln(30)
        pdf.set_font("Helvetica", "I", 10)
        pdf.multi_cell(0, 5, 
            "This report contains analysis of digital evidence for forensic purposes. "
            "All data has been analyzed using validated forensic techniques and tools. "
            "Conclusions are based on available digital evidence and should be considered "
            "within the context of the complete investigation."
        )
    
    def _add_executive_summary(self, pdf: FPDF, analysis_summary: Dict[str, Any]):
        """Add executive summary section."""
        pdf.add_page()
        self._add_section_header(pdf, "EXECUTIVE SUMMARY")
        
        pdf.set_font("Helvetica", "", 11)
        
        # Key findings
        key_findings = analysis_summary.get('key_findings', {})
        
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Key Findings:", ln=True)
        pdf.set_font("Helvetica", "", 11)
        
        findings_text = []
        
        if key_findings.get('total_events', 0) > 0:
            findings_text.append(f"* Total digital events analyzed: {key_findings['total_events']}")
        
        if key_findings.get('high_priority_events', 0) > 0:
            findings_text.append(f"* High-priority phone interactions: {key_findings['high_priority_events']}")
        
        if key_findings.get('phone_while_driving', 0) > 0:
            findings_text.append(f"* Phone usage while driving detected: {key_findings['phone_while_driving']} instances")
        
        if key_findings.get('critical_events', 0) > 0:
            findings_text.append(f"* Critical events in final minutes: {key_findings['critical_events']}")
        
        if key_findings.get('max_speed', 0) > 0:
            findings_text.append(f"* Maximum recorded speed: {key_findings['max_speed']:.1f} mph")
        
        for finding in findings_text:
            pdf.cell(0, 6, finding, ln=True)
        
        pdf.ln(5)
        
        # Analysis methodology
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Analysis Methodology:", ln=True)
        pdf.set_font("Helvetica", "", 11)
        
        methodology_text = [
            "* Digital evidence extracted from mobile device using Cellebrite forensic tools",
            "* Timeline analysis of phone usage events correlated with location data",
            "* Movement pattern analysis using GPS tracking data",
            "* App usage session duration analysis from system logs",
            "* Forensic priority classification based on interaction type and timing"
        ]
        
        for method in methodology_text:
            pdf.cell(0, 6, method, ln=True)
    
    def _add_event_analysis(self, pdf: FPDF, merged_df: pd.DataFrame, analysis_summary: Dict[str, Any]):
        """Add detailed event analysis section."""
        pdf.add_page()
        self._add_section_header(pdf, "EVENT ANALYSIS")
        
        # Priority distribution
        self._add_subsection_header(pdf, "Event Priority Distribution")
        
        priority_stats = analysis_summary.get('priority_distribution', {})
        
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Total Events Analyzed: {len(merged_df)}", ln=True)
        pdf.cell(0, 6, f"High Priority (Active Use): {priority_stats.get('high_priority', 0)}", ln=True)
        pdf.cell(0, 6, f"Medium Priority (Notifications): {priority_stats.get('medium_priority', 0)}", ln=True)
        pdf.cell(0, 6, f"Low Priority (Background): {priority_stats.get('low_priority', 0)}", ln=True)
        
        pdf.ln(8)
        
        # App usage frequency
        self._add_subsection_header(pdf, "Most Frequently Used Apps")
        
        app_usage = analysis_summary.get('app_usage', {})
        top_apps = sorted(app_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        
        pdf.set_font("Helvetica", "", 11)
        for app, count in top_apps:
            pdf.cell(0, 6, f"{app}: {count} events", ln=True)
    
    def _add_movement_analysis(self, pdf: FPDF, merged_df: pd.DataFrame, analysis_summary: Dict[str, Any]):
        """Add movement and speed analysis section."""
        pdf.add_page()
        self._add_section_header(pdf, "MOVEMENT ANALYSIS")
        
        movement_stats = analysis_summary.get('movement_summary', {})
        
        if movement_stats.get('error'):
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 6, "No reliable movement data available for analysis", ln=True)
            return
        
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Total Location Points: {movement_stats.get('total_location_points', 0)}", ln=True)
        pdf.cell(0, 6, f"Average Speed: {movement_stats.get('average_speed_mph', 0):.1f} mph", ln=True)
        pdf.cell(0, 6, f"Maximum Speed: {movement_stats.get('max_speed_mph', 0):.1f} mph", ln=True)
        pdf.cell(0, 6, f"Median Speed: {movement_stats.get('median_speed_mph', 0):.1f} mph", ln=True)
        
        pdf.ln(8)
        
        # Speed distribution
        self._add_subsection_header(pdf, "Speed Distribution")
        
        speed_dist = movement_stats.get('speed_distribution', {})
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Stationary (< {CONFIG.stationary_speed_threshold} mph): {speed_dist.get('stationary', 0)} points", ln=True)
        pdf.cell(0, 6, f"Slow Driving ({CONFIG.stationary_speed_threshold}-{CONFIG.slow_driving_threshold} mph): {speed_dist.get('slow_driving', 0)} points", ln=True)
        pdf.cell(0, 6, f"Fast Driving (> {CONFIG.slow_driving_threshold} mph): {speed_dist.get('fast_driving', 0)} points", ln=True)
        
        # Phone usage while driving
        phone_while_driving = movement_stats.get('phone_while_driving', {})
        if phone_while_driving.get('count', 0) > 0:
            pdf.ln(8)
            self._add_subsection_header(pdf, "Phone Usage While Driving")
            
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 6, f"Instances of phone use while driving: {phone_while_driving['count']}", ln=True)
            
            # Show top instances
            events = phone_while_driving.get('events', [])[:5]  # Top 5
            for event in events:
                timestamp = pd.to_datetime(event['timestamp']).strftime('%H:%M:%S')
                pdf.cell(0, 6, f"  {timestamp} - {event['app_name']} at {event['speed_mph']:.1f} mph", ln=True)
    
    def _add_app_usage_analysis(self, pdf: FPDF, analysis_summary: Dict[str, Any]):
        """Add app usage session analysis."""
        if self.app_sessions.empty:
            return
        
        pdf.add_page()
        self._add_section_header(pdf, "APP USAGE SESSIONS")
        
        session_summary = analysis_summary.get('session_summary', {})
        
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Total App Sessions: {session_summary.get('total_sessions', 0)}", ln=True)
        pdf.cell(0, 6, f"Different Apps Used: {session_summary.get('apps_used', 0)}", ln=True)
        
        total_duration = session_summary.get('total_duration_seconds', 0)
        if total_duration > 0:
            pdf.cell(0, 6, f"Total Usage Time: {total_duration/60:.1f} minutes", ln=True)
            pdf.cell(0, 6, f"Average Session Duration: {session_summary.get('average_session_duration', 0):.1f} seconds", ln=True)
        
        # Longest session
        longest = session_summary.get('longest_session', {})
        if longest:
            pdf.ln(5)
            pdf.cell(0, 6, f"Longest Session: {longest.get('app', 'Unknown')} ({longest.get('duration_seconds', 0):.0f} seconds)", ln=True)
        
        # Critical sessions
        critical = session_summary.get('critical_sessions', {})
        if critical and critical.get('count', 0) > 0:
            pdf.ln(8)
            self._add_subsection_header(pdf, "Critical App Sessions")
            
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 6, f"App sessions in critical window: {critical['count']}", ln=True)
            
            for session in critical.get('sessions', [])[:5]:  # Top 5
                start_time = pd.to_datetime(session['start_time']).strftime('%H:%M:%S')
                duration_min = session['duration_seconds'] / 60
                pdf.cell(0, 6, f"  {start_time} - {session['app_name']}: {duration_min:.1f} minutes", ln=True)
    
    def _add_critical_timeline(self, pdf: FPDF, merged_df: pd.DataFrame):
        """Add critical timeline analysis."""
        if not self.collision_time:
            return
        
        pdf.add_page()
        self._add_section_header(pdf, "CRITICAL TIMELINE ANALYSIS")
        
        # Calculate time to collision for events
        merged_df = merged_df.copy()
        merged_df['time_to_collision'] = (self.collision_time - merged_df['timestamp']).dt.total_seconds()
        
        # Get events in critical windows
        critical_30s = merged_df[merged_df['time_to_collision'].between(0, 30)]
        critical_2min = merged_df[merged_df['time_to_collision'].between(0, 120)]
        
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Events in final 30 seconds: {len(critical_30s)}", ln=True)
        pdf.cell(0, 6, f"Events in final 2 minutes: {len(critical_2min)}", ln=True)
        
        # High priority events in critical window
        high_priority_critical = critical_2min[
            critical_2min['forensic_priority'].isin(PRIORITY.HIGH_PRIORITY)
        ]
        
        if len(high_priority_critical) > 0:
            pdf.ln(8)
            self._add_subsection_header(pdf, " High Priority Events in Final 2 Minutes")
            
            pdf.set_font("Helvetica", "", 10)
            for _, event in high_priority_critical.head(10).iterrows():
                timestamp = event['timestamp'].strftime('%H:%M:%S')
                time_to_collision = event['time_to_collision']
                app_name = event.get('app_name', 'Unknown')
                event_type = event.get('event_type', 'Unknown')
                
                if pdf.get_y() > 250:  # Add new page if needed
                    pdf.add_page()
                
                pdf.multi_cell(0, 5, f"{timestamp} ({time_to_collision:.0f}s before) - {app_name}: {event_type}")
    
    def _add_conclusions(self, pdf: FPDF, analysis_summary: Dict[str, Any]):
        """Add conclusions and recommendations section."""
        pdf.add_page()
        self._add_section_header(pdf, "CONCLUSIONS AND FINDINGS")
        
        pdf.set_font("Helvetica", "", 11)
        
        # Generate conclusions based on analysis
        conclusions = self._generate_conclusions(analysis_summary)
        
        for conclusion in conclusions:
            if pdf.get_y() > 250:  # Add new page if needed
                pdf.add_page()
            pdf.multi_cell(0, 6, f"* {conclusion}")
            pdf.ln(2)
        
        pdf.ln(10)
        
        # Technical notes
        self._add_subsection_header(pdf, "Technical Notes")
        pdf.set_font("Helvetica", "", 10)
        
        technical_notes = [
            "Data was extracted using Cellebrite forensic tools and validated for integrity.",
            "Timeline analysis correlates phone usage events with location and movement data.",
            "Speed calculations use GPS coordinates and may be affected by GPS accuracy.",
            "App usage sessions are identified from system start/end time annotations.",
            "Priority classifications are based on forensic significance and user interaction level."
        ]
        
        for note in technical_notes:
            pdf.multi_cell(0, 5, f"* {note}")
            pdf.ln(1)
    
    def _generate_conclusions(self, analysis_summary: Dict[str, Any]) -> List[str]:
        """Generate conclusions based on analysis results."""
        conclusions = []
        
        key_findings = analysis_summary.get('key_findings', {})
        
        # Phone usage conclusions
        if key_findings.get('high_priority_events', 0) > 0:
            conclusions.append(
                f"Analysis identified {key_findings['high_priority_events']} high-priority phone "
                "interactions indicating active device usage during the analyzed timeframe."
            )
        
        if key_findings.get('phone_while_driving', 0) > 0:
            conclusions.append(
                f"Evidence shows {key_findings['phone_while_driving']} instances of phone usage "
                "while the vehicle was in motion above driving threshold speed."
            )
        
        if key_findings.get('critical_events', 0) > 0:
            conclusions.append(
                f"Critical timeline analysis reveals {key_findings['critical_events']} significant "
                "phone interactions in the final minutes before the incident."
            )
        
        # Movement conclusions
        movement_summary = analysis_summary.get('movement_summary', {})
        if not movement_summary.get('error') and movement_summary.get('max_speed_mph', 0) > 0:
            max_speed = movement_summary['max_speed_mph']
            avg_speed = movement_summary.get('average_speed_mph', 0)
            conclusions.append(
                f"Vehicle movement analysis shows maximum speed of {max_speed:.1f} mph "
                f"with average speed of {avg_speed:.1f} mph during the analyzed period."
            )
        
        # App usage conclusions
        session_summary = analysis_summary.get('session_summary', {})
        if session_summary.get('total_sessions', 0) > 0:
            total_sessions = session_summary['total_sessions']
            total_duration = session_summary.get('total_duration_seconds', 0) / 60
            conclusions.append(
                f"App usage analysis identified {total_sessions} distinct usage sessions "
                f"totaling {total_duration:.1f} minutes of active app engagement."
            )
        
        # General conclusion
        conclusions.append(
            "The digital evidence analysis provides objective data regarding phone usage patterns "
            "and vehicle movement that can be correlated with the incident timeline for "
            "forensic investigation purposes."
        )
        
        return conclusions
    
    def _add_section_header(self, pdf: FPDF, title: str):
        """Add a section header."""
        pdf.set_font("Helvetica", "B", 16)
        pdf.ln(10)
        pdf.cell(0, 12, title, ln=True)
        pdf.ln(5)
    
    def _add_subsection_header(self, pdf: FPDF, title: str):
        """Add a subsection header."""
        pdf.set_font("Helvetica", "B", 12)
        pdf.ln(5)
        pdf.cell(0, 8, title, ln=True)
        pdf.ln(2)