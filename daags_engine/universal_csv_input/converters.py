"""
Converters for transforming CSV data into generative formats.

These converters identify patterns in data and transform them into
formats suitable for synthetic data generation.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from functools import reduce
from math import gcd
from typing import List, Optional, Union
import random
import statistics

try:
    from pandas.tseries.api import guess_datetime_format
except ImportError:
    # Fallback if pandas is not available
    guess_datetime_format = None


class Converter(ABC):
    """Base class for all converters."""
    
    from_obj: "Converter"

    @abstractmethod
    def attempt_creation(obj: "Converter") -> Optional["Converter"]:
        """Attempt to create a converter from another converter."""
        pass

    @abstractmethod
    def __iter__(self):
        """Iterate over converted values."""
        pass

    @abstractmethod
    def convert_from(self, values: List[Union[int, float]]) -> List[str]:
        """Convert generated values back to their original format."""
        pass

    def debug_print(self):
        """Debug output showing the converter pipeline."""
        self.from_obj.debug_print()
        print(type(self).__name__, "->", end=" ")


class ConverterEndpoint(Converter):
    """Entry point converter for a list of raw values."""
    
    values: List

    def __init__(self, values: List):
        self.values = values

    @staticmethod
    def attempt_creation(obj: Converter) -> Optional["ConverterEndpoint"]:
        """Endpoint converters are not created from other converters."""
        return None

    def __iter__(self):
        for v in self.values:
            yield v

    def convert_from(self, values: List[Union[int, float]]) -> List[str]:
        """Convert to strings."""
        return [str(v) for v in values]

    def debug_print(self):
        """No further conversion in the pipeline."""
        pass


class MaintainGCD(Converter):
    """Maintains decimal precision and common increments in numeric data."""
    
    common_gcd: float
    numbers: List[Union[float, int]]

    def __init__(self):
        self.numbers = []
        self.common_gcd = 0

    @staticmethod
    def attempt_creation(obj: Converter) -> Optional["MaintainGCD"]:
        """Attempt to identify and maintain GCD patterns."""
        try:
            output = MaintainGCD()
            output.from_obj = obj

            # Convert to floats
            numbers = []
            for num in obj:
                numbers.append(float(num))

            output.numbers = numbers
            output.common_gcd = _gcd_list_fractions(numbers)
            return output
        except (ValueError, TypeError):
            return None

    def __iter__(self):
        for num in self.numbers:
            yield num

    def convert_from(self, values: List[Union[int, float]]) -> List:
        """Apply GCD rounding to generated values."""
        output = []
        for v in values:
            new_value = _round_to_nearest_multiple_exact(v, self.common_gcd)
            if self.common_gcd >= 1:
                new_value = int(new_value)
            output.append(new_value)
        return self.from_obj.convert_from(output)


class RemoveStatic(Converter):
    """Removes static prefix/suffix from string values."""
    
    front_static: str
    back_static: str
    sliced_strings: List[str]

    def __init__(self):
        self.sliced_strings = []
        self.front_static = ""
        self.back_static = ""

    @staticmethod
    def attempt_creation(obj: Converter) -> Optional["RemoveStatic"]:
        """Attempt to identify and remove static string portions."""
        try:
            output = RemoveStatic()
            output.from_obj = obj

            strings = [str(s) for s in obj]

            if not strings or len(strings) < 2:  # Need at least 2 values to find pattern
                return None

            output.front_static = strings[0]
            output.back_static = strings[0]

            for s in strings[1:]:
                output.front_static = _common_front_substring(output.front_static, s)
                output.back_static = _common_back_substring(output.back_static, s)

                if output.front_static == "" and output.back_static == "":
                    return None

            # Only use this converter if we actually found static content
            if output.front_static == "" and output.back_static == "":
                return None

            # Remove static pieces
            skip_front = len(output.front_static)
            skip_back = len(output.back_static)
            for s in strings:
                if skip_back > 0:
                    slice_str = s[skip_front:-skip_back]
                else:
                    slice_str = s[skip_front:]
                
                # Only add non-empty slices
                if slice_str:
                    output.sliced_strings.append(slice_str)

            if not output.sliced_strings:
                return None

            return output
        except Exception:
            return None

    def __iter__(self):
        for slice_str in self.sliced_strings:
            yield slice_str

    def convert_from(self, values: List[Union[int, float]]) -> List[str]:
        """Reapply static portions to generated values."""
        output = []
        for v in values:
            try:
                with_static = self.front_static + str(int(v) if isinstance(v, float) and v == int(v) else v) + self.back_static
                output.append(with_static)
            except Exception:
                # Fallback
                output.append(str(v))
        return self.from_obj.convert_from(output)


class DateAsMilli(Converter):
    """Converts date strings to/from milliseconds since epoch."""
    
    form: str
    datetime_list: List[datetime]
    millisecond_list: List[int]

    def __init__(self):
        self.datetime_list = []
        self.millisecond_list = []
        self.form = ""

    @staticmethod
    def attempt_creation(obj: Converter) -> Optional["DateAsMilli"]:
        """Attempt to identify date format and convert to milliseconds."""
        try:
            output = DateAsMilli()
            output.from_obj = obj

            strings = [str(s) for s in obj]
            if not strings:
                return None

            # Try to detect datetime format
            if guess_datetime_format:
                output.form = guess_datetime_format(strings[0])
            else:
                # Fallback formats to try
                formats = [
                    "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S",
                    "%m/%d/%Y %H:%M:%S", "%Y/%m/%d", "%d-%m-%Y"
                ]
                output.form = None
                for fmt in formats:
                    try:
                        datetime.strptime(strings[0], fmt)
                        output.form = fmt
                        break
                    except ValueError:
                        continue

            if not output.form:
                return None

            for s in strings:
                dt = datetime.strptime(s, output.form)
                output.datetime_list.append(dt)
                output.millisecond_list.append(int(dt.timestamp() * 1000))

            return output
        except Exception:
            return None

    def __iter__(self):
        for milli in self.millisecond_list:
            yield milli

    def convert_from(self, values: List[Union[int, float]]) -> List[str]:
        """Convert milliseconds back to date strings."""
        output = []
        for v in values:
            try:
                # Handle both numeric and string inputs
                if isinstance(v, str):
                    v = float(v)
                v = round(v)
                dt = datetime.fromtimestamp(float(v) / 1000)
                output.append(dt.strftime(self.form))
            except Exception as e:
                # Fallback for problematic values
                output.append(str(v))
        return self.from_obj.convert_from(output)


class Incremental(Converter):
    """Handles monotonically increasing sequences."""
    
    last_value: float
    differences: List[float]

    def __init__(self):
        self.differences = []
        self.last_value = 0

    @staticmethod
    def attempt_creation(obj: Converter) -> Optional["Incremental"]:
        """Attempt to identify incremental pattern."""
        try:
            output = Incremental()
            output.from_obj = obj

            numbers = list(obj)
            if not numbers:
                return None

            output.last_value = float(numbers[0])

            for i in range(1, len(numbers)):
                current = float(numbers[i])
                dif = current - output.last_value

                if dif < 0:
                    return None

                output.last_value = current
                output.differences.append(dif)

            return output
        except (ValueError, TypeError):
            return None

    def __iter__(self):
        for dif in self.differences:
            yield dif

    def convert_from(self, values: List[Union[int, float]]) -> List[str]:
        """Apply incremental conversion."""
        output = []
        current = self.last_value
        for v in values:
            if v < 0:
                v = 0
            new_value = current + v
            current = new_value
            output.append(new_value)
        return self.from_obj.convert_from(output)


def _gcd_list_fractions(numbers: List[Union[int, float]]) -> float:
    """Calculate GCD of a list of floats using fractions."""
    fracs = [Fraction(n).limit_denominator() for n in numbers]

    num_gcd = reduce(gcd, [f.numerator for f in fracs])

    def lcm(a, b):
        return abs(a * b) // gcd(a, b)

    den_lcm = reduce(lcm, [f.denominator for f in fracs])

    return float(Fraction(num_gcd, den_lcm))


def _round_to_nearest_multiple_exact(number_float: float, multiple_float: float) -> float:
    """Round to nearest multiple with high precision using Decimal."""
    try:
        # Handle special float values
        if number_float != number_float:  # NaN check
            return 0.0
        if number_float == float('inf') or number_float == float('-inf'):
            return number_float
        
        # Handle zero multiple
        if multiple_float == 0:
            return number_float
            
        num = Decimal(str(number_float))
        to = Decimal(str(multiple_float))
        rounded_num = round(num / to) * to
        return float(rounded_num)
    except Exception:
        # Fallback for any conversion errors
        return float(number_float)


def _common_front_substring(str1: str, str2: str) -> str:
    """Find common front substring."""
    result = ""
    for char1, char2 in zip(str1, str2):
        if char1 == char2:
            result += char1
        else:
            break
    return result


def _common_back_substring(str1: str, str2: str) -> str:
    """Find common back substring."""
    result = ""
    for i in range(1, min(len(str1), len(str2)) + 1):
        if str1[-i] == str2[-i]:
            result = str1[-i] + result
        else:
            break
    return result

