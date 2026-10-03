# Quick Start: Universal CSV Input

Get started generating synthetic data from any CSV in 2 minutes.

## Setup (One-time)

1. Make sure you're in the `New-DAAGS-project/` directory
2. The universal CSV input module is already integrated

## Quick Examples

### Example 1: Retail Sales Data

```bash
# Generate 1000 rows from retail dataset
python -m daags_engine.run --universal-csv simple_approach/data/input/retail_sales_dataset.csv
```

### Example 2: Climate Data

```bash
# Generate 500 rows of climate data (default TOTAL_RECORDS)
python -m daags_engine.run --universal-csv simple_approach/data/input/DailyDelhiClimateTest.csv
```

### Example 3: Your Own CSV

```bash
# Use any CSV file you have
python -m daags_engine.run --universal-csv path/to/your/file.csv
```

## Output

Generated synthetic data is saved to:
```
daags_engine/outputs/synthetic_data.csv
```

## How to Change Output Rows

Edit `daags_engine/config.py`:
```python
TOTAL_RECORDS = 5000  # Change this number
```

## Understanding the Output

When you run the command, you'll see analysis output like:

```
Analyzing CSV: simple_approach/data/input/retail_sales_dataset.csv
(order_id) MaintainGCD -> Distribution
(customer_id) MaintainGCD -> Distribution
(purchase_date) DateAsMilli -> Incremental -> Distribution
(amount) MaintainGCD -> Distribution
(category) Weighted

Generating 500 rows...
Output saved to: daags_engine/outputs/synthetic_data.csv
```

This shows what pattern each column is using:
- **MaintainGCD**: Preserves decimal/integer precision
- **DateAsMilli**: Recognizes dates
- **Incremental**: Detects time sequences
- **Distribution**: Uses normal distribution (for numeric data with variation)
- **Weighted**: Uses weighted sampling (for categorical/repeated data)

## Next Steps

1. **Customize output rows**: Edit `TOTAL_RECORDS` in config.py
2. **Use multiple CSVs**: Run the command with different input files
3. **Add validation**: Compare input and output distributions
4. **Scale up**: Test with larger CSVs to find performance limits
5. **Combine modes**: Use DAAGS mode for transactions, CSV mode for reference data

## Integration with DAAGS (Advanced)

You can use both modes together:

```bash
# Generate transaction data (DAAGS mode)
python -m daags_engine.run default

# Generate synthetic reference data (CSV mode)
python -m daags_engine.run --universal-csv daags_engine/inputs/amazon_products.csv

# Mix both outputs in your pipeline
```

## Troubleshooting

**Error: Input CSV file not found**
- Check the file path is correct
- Use absolute path if in a different directory

**Output CSV is empty**
- Check input CSV has headers (first row)
- Check input CSV has at least 2 rows of data

**Columns showing only Weighted**
- This means columns are mostly categorical/non-numeric
- That's OK! It will still generate valid synthetic data

## Tips

- Test with small CSVs (< 1000 rows) first
- The analyzer prints the detected pattern for each column
- Output maintains the same column structure as input
- Generated data preserves statistical properties of input

For full documentation, see: [UNIVERSAL_CSV_INPUT.md](UNIVERSAL_CSV_INPUT.md)
