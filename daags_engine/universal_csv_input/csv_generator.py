"""
Universal CSV Generator - generates synthetic data from any CSV file.

This integrates with the DAAGS engine to provide flexible CSV-based
synthetic data generation with AI tuning support.
"""

import csv
from typing import Optional, List, Dict, Any
from .csv_analyzer import UniversalCSVAnalyzer


class UniversalCSVGenerator:
    """
    Flexible CSV generator that works with any CSV input file.
    
    Automatically analyzes CSV structure, infers data patterns,
    and generates synthetic data maintaining those patterns.
    """
    
    def __init__(self, input_csv: str, verbose: bool = True):
        """
        Initialize the generator.
        
        Args:
            input_csv: Path to input CSV file
            verbose: Set to True for debug output during analysis
        """
        self.input_csv = input_csv
        self.verbose = verbose
        self.analyzer: Optional[UniversalCSVAnalyzer] = None
        self._load_analyzer()
    
    def _load_analyzer(self) -> None:
        """Load and analyze the CSV file."""
        if self.verbose:
            print(f"Analyzing CSV: {self.input_csv}")
        self.analyzer = UniversalCSVAnalyzer(self.input_csv)
    
    def generate(self, n_rows: int, output_csv: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate synthetic data.
        
        Args:
            n_rows: Number of rows to generate
            output_csv: Optional path to write CSV output
        
        Returns:
            List of generated rows (dictionaries)
        """
        if not self.analyzer:
            raise RuntimeError("Analyzer not initialized")
        
        rows = self.analyzer.generate_n_rows(n_rows)
        
        if output_csv:
            self.analyzer.generate_n_rows_to_csv(output_csv, n_rows)
        
        return rows
    
    def get_fieldnames(self) -> List[str]:
        """Get the field names from analyzed CSV."""
        if not self.analyzer:
            raise RuntimeError("Analyzer not initialized")
        return self.analyzer.fieldnames
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of CSV analysis."""
        if not self.analyzer:
            raise RuntimeError("Analyzer not initialized")
        
        return {
            "input_file": self.input_csv,
            "fieldnames": self.analyzer.fieldnames,
            "num_columns": len(self.analyzer.fieldnames),
            "num_producers": len(self.analyzer.producers),
        }
