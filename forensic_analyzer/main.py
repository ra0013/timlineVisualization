#!/usr/bin/env python3
"""
Main entry point for the Forensic Distracted Driving Analyzer.
Orchestrates the modular analysis pipeline.
"""

import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Import modular components
from config.settings import CONFIG
from data.loaders import CellebriteTimelineLoader, CellebriteLocationLoader, DataMerger
from analysis.phone_usage import PhoneUsageAnalyzer
from analysis.movement import MovementAnalyzer
from analysis.app_sessions import AppSessionAnalyzer
from visualization.kml_generator import ForensicKMLGenerator
from reporting.pdf_generator import ForensicReportGenerator


class ForensicAnalysisOrchestrator:
    """
    Main orchestrator for forensic distracted driving analysis.
    Coordinates all analysis modules and generates outputs.
    """
    
    def __init__(self):
        # Initialize analysis components
        self.timeline_loader = CellebriteTimelineLoader()
        self.location_loader = CellebriteLocationLoader()
        self.data_merger = DataMerger()
        self.phone_analyzer = PhoneUsageAnalyzer()
        self.movement_analyzer = MovementAnalyzer()
        self.app_session_analyzer = AppSessionAnalyzer()
        self.kml_generator = ForensicKMLGenerator()
        self.report_generator = ForensicReportGenerator()
        
        # Analysis state
        self.collision_time: Optional[pd.Timestamp] = None
        self.collision_location: Optional[Tuple[float, float]] = None
        self.merged_data: Optional[pd.DataFrame] = None
    
    def set_collision_details(
        self, 
        collision_time: str, 
        collision_lat: Optional[float] = None, 
        collision_lon: Optional[float] = None
    ):
        """
        Set collision time and location for analysis.
        
        Args:
            collision_time: Collision time string (YYYY-MM-DD HH:MM:SS)
            collision_lat: Collision latitude (optional)
            collision_lon: Collision longitude (optional)
        """
        self.collision_time = pd.to_datetime(collision_time)
        
        if collision_lat and collision_lon:
            self.collision_location = (collision_lat, collision_lon)
        
        # Update analyzers with collision info
        self.phone_analyzer.set_collision_time(self.collision_time)
        self.app_session_analyzer.set_collision_time(self.collision_time)
        self.kml_generator.set_collision_details(self.collision_time, collision_lat, collision_lon)
        self.report_generator.set_collision_details(self.collision_time, self.collision_location)
        
        print(f"✓ Collision set for: {self.collision_time}")
    
    def load_data(self, timeline_file: str, location_file: Optional[str] = None) -> bool:
        """
        Load timeline and location data from Cellebrite exports.
        
        Args:
            timeline_file: Path to timeline Excel file
            location_file: Path to location Excel file (optional)
            
        Returns:
            True if data loaded successfully, False otherwise
        """
        print("=== LOADING DATA ===")
        
        # Load timeline data
        timeline_data = self.timeline_loader.load_timeline(timeline_file)
        if timeline_data is None or timeline_data.empty:
            print("✗ Failed to load timeline data")
            return False
        
        # Load location data (optional)
        location_data = None
        if location_file:
            location_data = self.location_loader.load_locations(location_file)
            if location_data is None:
                print("⚠️  Location data failed to load - proceeding with timeline only")
        
        # Merge data
        self.merged_data = self.data_merger.merge_timeline_and_locations(timeline_data, location_data)
        
        if self.merged_data is None or self.merged_data.empty:
            print("✗ Failed to merge data")
            return False
        
        print(f"✓ Data loaded successfully: {len(self.merged_data)} events")
        return True
    
    def run_analysis(self, critical_window_minutes: int = CONFIG.default_critical_window) -> bool:
        """
        Run comprehensive forensic analysis.
        
        Args:
            critical_window_minutes: Minutes before collision to focus analysis
            
        Returns:
            True if analysis completed successfully, False otherwise
        """
        if self.merged_data is None:
            print("✗ No data loaded for analysis")
            return False
        
        print("\n=== RUNNING FORENSIC ANALYSIS ===")
        
        # Filter to critical timeframe if collision time set
        analysis_data = self.merged_data.copy()
        if self.collision_time:
            analysis_data = self.phone_analyzer.filter_critical_timeframe(
                analysis_data, 
                critical_window_minutes
            )
        
        try:
            # 1. Phone usage analysis
            print("\n--- Phone Usage Analysis ---")
            analysis_data = self.phone_analyzer.analyze_phone_usage_patterns(analysis_data)
            
            # 2. App session analysis
            print("\n--- App Session Analysis ---")
            analysis_data = self.app_session_analyzer.analyze_app_usage_duration(analysis_data)
            
            # 3. Movement analysis
            print("\n--- Movement Analysis ---")
            analysis_data = self.movement_analyzer.analyze_movement_patterns(analysis_data)
            
            # 4. Cross-correlation analysis
            print("\n--- Cross-Correlation Analysis ---")
            phone_while_driving = self.phone_analyzer.analyze_phone_use_while_driving(analysis_data)
            app_sessions_while_driving = self.app_session_analyzer.analyze_sessions_while_driving(analysis_data)
            
            # Update merged data with analysis results
            self.merged_data = analysis_data
            
            print("✓ Forensic analysis completed successfully")
            return True
            
        except Exception as e:
            print(f"✗ Error during analysis: {e}")
            return False
    
    def generate_outputs(self, output_kml: str = "forensic_analysis.kml", output_pdf: str = "forensic_report.pdf") -> bool:
        """
        Generate KML visualization and PDF report.
        
        Args:
            output_kml: Output KML filename
            output_pdf: Output PDF filename
            
        Returns:
            True if outputs generated successfully, False otherwise
        """
        if self.merged_data is None:
            print("✗ No analyzed data available for output generation")
            return False
        
        print("\n=== GENERATING OUTPUTS ===")
        
        try:
            # Generate KML visualization
            print("--- Generating KML ---")
            kml_success = self.kml_generator.create_forensic_kml(self.merged_data, output_kml)
            
            # Generate PDF report
            print("--- Generating PDF Report ---")
            pdf_success = self.report_generator.generate_report(self.merged_data, output_pdf)
            
            if kml_success and pdf_success:
                print(f"\n🎉 FORENSIC ANALYSIS COMPLETE! 🎉")
                print(f"📁 KML Visualization: {output_kml}")
                print(f"📄 PDF Report: {output_pdf}")
                print(f"🔍 Review HIGH PRIORITY events for critical evidence")
                print(f"⚖️  Ready for expert testimony and courtroom presentation")
                return True
            else:
                print("⚠️  Some outputs failed to generate")
                return False
                
        except Exception as e:
            print(f"✗ Error generating outputs: {e}")
            return False
    
    def get_analysis_summary(self) -> dict:
        """
        Get comprehensive analysis summary.
        
        Returns:
            Dictionary with analysis results
        """
        if self.merged_data is None:
            return {"error": "No data analyzed"}
        
        summary = {
            "metadata": {
                "total_events": len(self.merged_data),
                "collision_time": self.collision_time.isoformat() if self.collision_time else None,
                "collision_location": self.collision_location,
                "analysis_timestamp": datetime.now().isoformat()
            },
            "phone_usage": self.phone_analyzer.get_usage_summary(self.merged_data),
            "movement": self.movement_analyzer.get_movement_summary(self.merged_data),
            "app_sessions": self.app_session_analyzer.get_session_summary()
        }
        
        return summary


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Forensic Distracted Driving Analysis")
    parser.add_argument("timeline_file", help="Path to Cellebrite timeline Excel export")
    parser.add_argument("-l", "--location", help="Path to Cellebrite location Excel export")
    parser.add_argument("-o", "--output-kml", default="forensic_analysis.kml", help="Output KML file")
    parser.add_argument("-r", "--output-pdf", default="forensic_report.pdf", help="Output PDF report")
    parser.add_argument("-t", "--tolerance", type=int, default=CONFIG.location_match_tolerance_minutes, 
                       help="Time tolerance for location matching (minutes)")
    parser.add_argument("-c", "--collision-time", help="Collision time (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--collision-lat", type=float, help="Collision latitude")
    parser.add_argument("--collision-lon", type=float, help="Collision longitude")
    parser.add_argument("-w", "--window", type=int, default=CONFIG.default_critical_window, 
                       help="Analysis window before collision (minutes)")
    
    args = parser.parse_args()
    
    print("=== FORENSIC DISTRACTED DRIVING ANALYSIS ===")
    print("⚠️  Specialized for fatal collision investigations involving phone usage")
    
    # Initialize orchestrator
    orchestrator = ForensicAnalysisOrchestrator()
    
    # Set collision details if provided
    if args.collision_time:
        orchestrator.set_collision_details(
            args.collision_time, 
            args.collision_lat, 
            args.collision_lon
        )
    
    # Load data
    if not orchestrator.load_data(args.timeline_file, args.location):
        print("✗ Failed to load data")
        return 1
    
    # Run analysis
    if not orchestrator.run_analysis(args.window):
        print("✗ Analysis failed")
        return 1
    
    # Generate outputs
    if not orchestrator.generate_outputs(args.output_kml, args.output_pdf):
        print("✗ Output generation failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())