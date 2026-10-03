# Universal CSV Input Integration

This document describes the integrated universal CSV input system for the DAAGS project.

## Overview

The DAAGS project now supports two modes:

1. **DAAGS Mode** (Original): Generates e-commerce transaction data with state-based behavior, product catalogs, and optional AI tuning
2. **Universal CSV Mode** (New): Generates synthetic data from ANY CSV file by automatically analyzing patterns

## What Was Integrated

The following components from `simple_approach/` have been integrated into `New-DAAGS-project/`:

### New Module: `daags_engine/universal_csv_input/`

Created four core files:

#### 1. **converters.py**
Implements pattern-detection converters:
- `ConverterEndpoint`: Entry point for raw CSV data
- `MaintainGCD`: Preserves decimal precision and common increments
- `DateAsMilli`: Converts dates to/from milliseconds
- `RemoveStatic`: Removes/restores static prefixes/suffixes
- `Incremental`: Handles monotonically increasing sequences

#### 2. **producers.py**
Implements data generators:
- `Distribution`: Generates values using normal distribution
- `Weighted`: Generates values using weighted sampling

#### 3. **csv_analyzer.py**
`UniversalCSVAnalyzer` class:
- Analyzes CSV file structure
- Applies converters in a pipeline to identify data patterns
- Selects appropriate producers for each column
- Generates synthetic data maintaining patterns

#### 4. **csv_generator.py**
`UniversalCSVGenerator` class:
- High-level interface for CSV generation
- Handles file I/O and error checking
- Provides summary of analysis

## Usage

### Mode 1: Command-Line with CSV File

```bash
# Generate synthetic data from a CSV file
python -m daags_engine.run --universal-csv path/to/your/data.csv

# This will:
# 1. Analyze your CSV structure (prints analysis summary)
# 2. Generate N rows (TOTAL_RECORDS from config)
# 3. Write output to: daags_engine/outputs/synthetic_data.csv
```

### Mode 2: Environment Variables

```bash
export UNIVERSAL_CSV_MODE=true
export UNIVERSAL_CSV_INPUT_PATH=path/to/your/data.csv
export TOTAL_RECORDS=1000  # Optional: override number of rows
python -m daags_engine.run
```

### Mode 3: Traditional DAAGS Mode (Default)

```bash
python -m daags_engine.run                    # Interactive - asks for OpenRouter instruction
python -m daags_engine.run default            # Skip AI tuning
python -m daags_engine.run "your instruction" # Custom instruction
```

## Example: Generating Synthetic E-commerce Data

```bash
# If you have a CSV like: order_id, customer_name, order_date, total_amount, category

# Run:
python -m daags_engine.run --universal-csv data/retail_data.csv

# Output:
# Analyzing CSV: data/retail_data.csv
# (order_id) MaintainGCD -> Distribution
# (customer_name) RemoveStatic -> Weighted
# (order_date) DateAsMilli -> Incremental -> Distribution
# (total_amount) MaintainGCD -> Distribution
# (category) Weighted
# 
# Generating 500 rows...
# Output saved to: daags_engine/outputs/synthetic_data.csv
```

## Configuration

Edit `daags_engine/config.py` to control:

```python
# Number of rows to generate (used in both modes)
TOTAL_RECORDS = 500

# Universal CSV mode output file
UNIVERSAL_CSV_OUTPUT_FILE = "daags_engine/outputs/synthetic_data.csv"
```

## How It Works

### Pattern Detection Pipeline

For each column in the CSV:

1. **Endpoint**: Raw CSV values
2. **Conversion Levels** (attempted in order):
   - Level 1: `MaintainGCD` - Detect decimal patterns
   - Level 2: `DateAsMilli` - Detect date formats
   - Level 3: `RemoveStatic` - Remove common prefixes/suffixes
   - Level 4: `Incremental` - Detect time-series patterns
3. **Production**: Select appropriate producer:
   - `Distribution` - For numeric data with variation
   - `Weighted` - For categorical or repeated patterns

### Example Pipeline

**Input**: `["2024-01-15", "2024-01-20", "2024-02-01"]`
- Endpoint returns raw strings
- DateAsMilli converts to ms: `[1705276800000, 1705622400000, 1706745600000]`
- Incremental detects differences: `[346080000, 1123200000]`
- Distribution generates new differences from normal distribution
- Incremental converts back: new dates
- DateAsMilli converts back to strings

## Key Advantages

1. **Universal**: Works with ANY CSV file
2. **Automatic**: No configuration needed - analyzes structure automatically
3. **Intelligent**: Preserves data patterns (dates, decimals, sequences)
4. **Flexible**: Mixes two generation modes in one project
5. **AI-Ready**: Can add OpenRouter tuning to both modes

## Compatibility

All existing DAAGS functionality remains unchanged:
- Transaction generation (`python -m daags_engine.run default`)
- State-based behavior
- Product catalogs
- Database writers
- OpenRouter integration

## Adding Custom Patterns

To add support for additional data patterns:

1. **Create new Converter** in `converters.py`:
   ```python
   class MyConverter(Converter):
       @staticmethod
       def attempt_creation(obj: Converter) -> Optional["MyConverter"]:
           # Try to detect your pattern
           # Return instance if detected, None otherwise
           
       def convert_from(self, values):
           # Reverse the conversion
   ```

2. **Add to conversion levels** in `csv_analyzer.py`:
   ```python
   MAIN_CONVERSION_LEVELS = [
       [...existing...],
       [MyConverter.attempt_creation],  # Add here
   ]
   ```

## Testing

Test the integration with sample CSVs:

```bash
# Test with retail data
python -m daags_engine.run --universal-csv simple_approach/data/input/retail_sales_dataset.csv

# Test with climate data
python -m daags_engine.run --universal-csv simple_approach/data/input/DailyDelhiClimateTest.csv

# Test with product data
python -m daags_engine.run --universal-csv daags_engine/inputs/amazon_products.csv
```

## Files Modified

- **daags_engine/config.py** - Added universal CSV configuration
- **daags_engine/run.py** - Added CLI support for CSV mode
- **daags_engine/universal_csv_input/** - New package with 4 modules

## Files Created

All new files in `daags_engine/universal_csv_input/`:
- `__init__.py` - Package initialization
- `converters.py` - Pattern detection converters
- `producers.py` - Data generators
- `csv_analyzer.py` - Main analysis engine
- `csv_generator.py` - High-level interface

## Future Enhancements

Possible improvements:
- Multi-modal distributions (mixture of Gaussians)
- Correlation detection and preservation
- Custom converter/producer registration
- Web UI for parameter tuning
- Performance optimization for large files
