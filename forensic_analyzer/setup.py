# setup.py
"""
Setup script for the Forensic Distracted Driving Analyzer package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

setup(
    name="forensic-distracted-driving-analyzer",
    version="2.0.0",
    author="GDSL Forensic Analysis Team",
    author_email="",
    description="A modular tool for forensic analysis of distracted driving incidents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Legal Industry",
        "Intended Audience :: Science/Research", 
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.3.0",
        "simplekml>=1.3.6",
        "openpyxl>=3.0.9",
        "fpdf2>=2.5.0",
        "numpy>=1.21.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "forensic-analyzer=forensic_analyzer.main:main",
        ],
    },
    package_data={
        "forensic_analyzer": [
            "config/*.json",
            "templates/*.html",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)