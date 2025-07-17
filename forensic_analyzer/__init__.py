# forensic_analyzer/__init__.py
"""
Forensic Distracted Driving Analyzer - Modular Edition

A comprehensive tool for analyzing phone usage and movement patterns
in forensic investigations of distracted driving incidents.
"""

__version__ = "2.0.0"
__author__ = "Forensic Analysis Team"

from .main import ForensicAnalysisOrchestrator

# Main entry point for the package
def create_analyzer():
    """Create a new forensic analysis orchestrator instance."""
    return ForensicAnalysisOrchestrator()

# Package metadata
__all__ = [
    'ForensicAnalysisOrchestrator',
    'create_analyzer'
]
