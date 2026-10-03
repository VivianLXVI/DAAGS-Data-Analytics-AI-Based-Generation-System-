"""
Universal CSV Analyzer - analyzes any CSV and infers data patterns.

This module combines converter and producer classes to analyze
CSV files and create a blueprint for synthetic data generation.
"""

import csv
from typing import List, Dict, Tuple, Any
from .converters import Converter, ConverterEndpoint
from .converters import MaintainGCD, DateAsMilli, RemoveStatic, Incremental
from .producers import Producer, Distribution, Weighted


class UniversalCSVAnalyzer:
    """Analyzes CSV files and creates producers for each column."""
    
    # Conversion levels define the order in which converters are attempted
    # Simplified set of converters to avoid problematic interactions
    MAIN_CONVERSION_LEVELS = [
        [DateAsMilli.attempt_creation],  # Try dates first - they're distinctive
        [MaintainGCD.attempt_creation],  # Then numeric patterns
        [Incremental.attempt_creation],  # Finally monotonic sequences
    ]
    
    # Producers to attempt in order
    PRODUCERS = [
        Distribution.attempt_creation,
        Weighted.attempt_creation,
    ]
    
    def __init__(self, input_file: str):
        """Initialize analyzer with a CSV file."""
        self.fieldnames: List[str] = []
        self.producers: List[Producer] = []
        self.analyze_file(input_file)
    
    def analyze_file(self, input_file: str) -> None:
        """Analyze CSV file and create producers for each column."""
        fieldnames, col_list = self._csv_to_col_list(input_file)
        self.fieldnames = fieldnames
        
        for i, col in enumerate(col_list):
            field = self.fieldnames[i]
            
            # Start with endpoint converter
            conv: Converter = ConverterEndpoint(col)
            
            # Try conversion levels
            for level in self.MAIN_CONVERSION_LEVELS:
                for func in level:
                    result = func(conv)
                    if result is not None:
                        conv = result
            
            # Try producers
            for func in self.PRODUCERS:
                result = func(conv)
                if result is not None:
                    self.producers.append(result)
                    print(f"({field})", end=" ")
                    result.debug_print()
                    break
        
        print()  # New line after analysis
    
    def generate_n_rows(self, n: int) -> List[Dict[str, Any]]:
        """Generate n rows of synthetic data."""
        result = []
        
        # Generate values for each field
        random_values = []
        for producer in self.producers:
            random_values.append(producer.generate_n_items(n))
        
        # Combine into dictionaries
        for i in range(n):
            row = {}
            for j, field in enumerate(self.fieldnames):
                row[field] = random_values[j][i]
            result.append(row)
        
        return result
    
    def generate_n_rows_to_csv(self, output_file: str, n: int) -> None:
        """Generate n rows and write to CSV file."""
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerows(self.generate_n_rows(n))
        
        print(f"Generated {n} rows to {output_file}")
    
    @staticmethod
    def _csv_to_col_list(filepath: str, max_rows: int = 0) -> Tuple[List[str], List[List[Any]]]:
        """Read CSV and convert to column list format."""
        data = []
        
        with open(filepath, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            
            for row in csv_reader:
                data.append(row)
                if max_rows > 0:
                    max_rows -= 1
                    if max_rows == 0:
                        break
        
        if not data:
            return [], []
        
        # Convert dict list to column list
        fieldnames = list(data[0].keys())
        
        # Create column lists
        col_list: List[List[Any]] = [[] for _ in fieldnames]
        
        for row in data:
            for j, fieldname in enumerate(fieldnames):
                col_list[j].append(row[fieldname])
        
        return fieldnames, col_list
