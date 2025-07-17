#!/usr/bin/env python3
"""
Basic functionality test for the modular forensic analyzer.
FIXED FOR RUNNING FROM INSIDE forensic_analyzer DIRECTORY
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_imports():
    """Test that all modules can be imported."""
    try:
        # Import directly since we're already in the forensic_analyzer directory
        from main import ForensicAnalysisOrchestrator
        from config.settings import CONFIG
        from data.loaders import CellebriteTimelineLoader
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print(f"Current directory: {current_dir}")
        print(f"Contents: {list(current_dir.iterdir())}")
        return False

def test_configuration():
    """Test configuration loading."""
    try:
        from config.settings import CONFIG, KML_STYLES, PRIORITY
        print(f"✅ Config loaded - driving threshold: {CONFIG.driving_threshold} mph")
        print(f"✅ Styles loaded - {len(KML_STYLES.FORENSIC_STYLES)} style definitions")
        print(f"✅ Priorities loaded - High priority events: {PRIORITY.HIGH_PRIORITY}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_orchestrator():
    """Test basic orchestrator functionality."""
    try:
        from main import ForensicAnalysisOrchestrator
        
        orchestrator = ForensicAnalysisOrchestrator()
        print("✅ Orchestrator created successfully")
        
        # Test collision setting
        orchestrator.set_collision_details("2024-01-15 14:30:45", 40.7128, -74.0060)
        print("✅ Collision details set successfully")
        
        return True
    except Exception as e:
        print(f"❌ Orchestrator error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_file_structure():
    """Check if all required files exist in current directory."""
    print(f"📁 Checking file structure in: {current_dir}")
    
    required_files = [
        "__init__.py",
        "main.py", 
        "config/__init__.py",
        "config/settings.py",
        "data/__init__.py",
        "data/loaders.py",
        "data/parsers.py",
        "data/validators.py",
        "analysis/__init__.py",
        "analysis/phone_usage.py",
        "analysis/movement.py",
        "analysis/app_sessions.py",
        "visualization/__init__.py",
        "visualization/kml_generator.py",
        "visualization/styles.py",
        "reporting/__init__.py",
        "reporting/pdf_generator.py",
        "reporting/summary.py",
        "utils/__init__.py",
        "utils/coordinates.py"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        full_path = current_dir / file_path
        if full_path.exists():
            existing_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")
    
    print(f"\n✅ Found {len(existing_files)} files")
    print(f"❌ Missing {len(missing_files)} files")
    
    return len(missing_files) == 0

if __name__ == "__main__":
    print("=== BASIC FUNCTIONALITY TEST ===")
    print(f"Working directory: {os.getcwd()}")
    print(f"Script directory: {current_dir}")
    
    # First check file structure
    print("\n--- File Structure Check ---")
    structure_ok = check_file_structure()
    
    if not structure_ok:
        print("\n❌ File structure is incomplete. Please check missing files.")
        print("\nDid you create all the module files with the code I provided?")
        sys.exit(1)
    
    # Run functionality tests
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration), 
        ("Orchestrator Test", test_orchestrator)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
    
    print(f"\n=== RESULTS: {passed}/{len(tests)} tests passed ===")
    
    if passed == len(tests):
        print("🎉 All basic tests passed! Ready for data testing.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")