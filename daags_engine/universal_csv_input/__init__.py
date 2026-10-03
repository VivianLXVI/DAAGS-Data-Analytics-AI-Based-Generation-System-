"""
Universal CSV Input System for DAAGS

This module integrates the simple_approach's data analysis capabilities
with DAAGS engine to enable synthetic data generation from any CSV file.

Key components:
- csv_analyzer: Analyzes CSV structure and infers data types
- converters: Transform data into generative formats
- producers: Generate synthetic values based on patterns
- csv_generator: Flexible data generator for any CSV structure
"""

from .csv_analyzer import UniversalCSVAnalyzer
from .csv_generator import UniversalCSVGenerator

__all__ = ["UniversalCSVAnalyzer", "UniversalCSVGenerator"]
