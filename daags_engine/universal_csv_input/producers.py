"""
Producers for generating synthetic data based on patterns.

These producers take trained patterns from converters and
generate new synthetic values that maintain the patterns.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Union
import random
import statistics

from .converters import Converter


class Producer(ABC):
    """Base class for all producers."""
    
    from_obj: Converter

    @staticmethod
    @abstractmethod
    def attempt_creation(obj: Converter) -> Optional["Producer"]:
        """Attempt to create a producer from a converter."""
        pass

    @abstractmethod
    def generate_n_items(self, n: int) -> List[str]:
        """Generate n synthetic items."""
        pass

    def debug_print(self):
        """Debug output showing producer type."""
        self.from_obj.debug_print()
        print(type(self).__name__)


class Distribution(Producer):
    """Generates values using normal distribution based on training data."""
    
    mean: float
    stdev: float

    @staticmethod
    def attempt_creation(obj: Converter) -> Optional["Distribution"]:
        """Attempt to fit normal distribution to numeric data."""
        try:
            output = Distribution()
            output.from_obj = obj

            numbers = []
            for item in obj:
                numbers.append(float(item))

            output.mean = statistics.mean(numbers)
            output.stdev = statistics.stdev(numbers) if len(numbers) > 1 else 0.0
            
            # Only create if stdev is reasonable (not zero or extremely small)
            if output.stdev < 1e-10:
                return None
                
            return output
        except (ValueError, TypeError, statistics.StatisticsError):
            return None

    def generate_n_items(self, n: int) -> List[str]:
        """Generate n values from normal distribution."""
        values = []
        for _ in range(n):
            while True:  # Keep trying until we get a valid value
                # Box-Muller transform for normal distribution
                try:
                    u1 = random.random()
                    u2 = random.random()
                    # Avoid log(0)
                    while u1 == 0:
                        u1 = random.random()
                    
                    import math
                    z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
                    value = self.mean + self.stdev * z0
                    
                    # Make sure value is valid
                    if isinstance(value, float) and value == value:  # NaN check
                        values.append(value)
                        break
                except Exception:
                    # Fallback: just use the mean
                    values.append(self.mean)
                    break
        
        return self.from_obj.convert_from(values)


class Weighted(Producer):
    """Generates values using weighted sampling from observed values."""
    
    unique_values: List[float]
    weights: List[float]

    @staticmethod
    def attempt_creation(obj: Converter) -> Optional["Weighted"]:
        """Create weighted producer from unique values in data."""
        try:
            output = Weighted()
            output.from_obj = obj

            values = list(obj)
            
            try:
                # Try to convert to numeric for better handling
                numeric_values = [float(v) for v in values]
            except (ValueError, TypeError):
                # Fall back to string values if numeric conversion fails
                numeric_values = values

            if not numeric_values:
                return None

            # Get unique values and their frequencies
            unique_vals = []
            seen = {}
            for v in numeric_values:
                if v not in seen:
                    seen[v] = 0
                    unique_vals.append(v)
                seen[v] += 1
            
            counts = [seen[v] for v in unique_vals]
            total = sum(counts)
            
            output.unique_values = unique_vals
            output.weights = [c / total for c in counts]

            return output
        except Exception:
            return None

    def generate_n_items(self, n: int) -> List[str]:
        """Generate n values using weighted sampling."""
        sampled = []
        for _ in range(n):
            # Weighted random choice
            r = random.random()
            cumsum = 0
            for i, weight in enumerate(self.weights):
                cumsum += weight
                if r <= cumsum:
                    sampled.append(self.unique_values[i])
                    break
            else:
                # Fallback in case of floating point issues
                sampled.append(self.unique_values[-1])
        
        return self.from_obj.convert_from(sampled)

