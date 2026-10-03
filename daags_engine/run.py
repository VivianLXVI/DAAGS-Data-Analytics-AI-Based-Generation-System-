"""
Entry point for generating DAAGS demo data.

Runs `daags_engine.generator.run_generation()` when executed as a module:
    python -m daags_engine.run [options]

Options:
    --universal-csv <path>  Use universal CSV input mode with the specified CSV file
    <instruction>           OpenRouter instruction (only for DAAGS mode)

Examples:
    python -m daags_engine.run                              # DAAGS mode with AI
    python -m daags_engine.run default                      # DAAGS mode without AI
    python -m daags_engine.run --universal-csv data.csv     # Universal CSV mode
    python -m daags_engine.run "make winter slow down"      # DAAGS with instruction
"""

import sys
import os

from dotenv import load_dotenv
load_dotenv()

from daags_engine.config import UNIVERSAL_CSV_MODE, UNIVERSAL_CSV_INPUT_PATH, TOTAL_RECORDS, UNIVERSAL_CSV_OUTPUT_FILE
from daags_engine.state_config import print_state_behavior, apply_openrouter_tuning
from daags_engine.generator import run_generation


def run_universal_csv_mode(input_csv: str) -> None:
    """Run the universal CSV input generator."""
    from daags_engine.universal_csv_input import UniversalCSVGenerator
    
    if not os.path.exists(input_csv):
        print(f"Error: Input CSV file not found: {input_csv}")
        sys.exit(1)
    
    print(f"\n=== Universal CSV Input Mode ===")
    print(f"Input CSV: {input_csv}")
    print(f"Generating {TOTAL_RECORDS} rows...")
    
    generator = UniversalCSVGenerator(input_csv, verbose=True)
    summary = generator.get_analysis_summary()
    
    print(f"\nAnalysis Summary:")
    print(f"  Columns: {summary['num_columns']}")
    print(f"  Fields: {', '.join(summary['fieldnames'])}")
    
    # Generate and save
    generator.generate(TOTAL_RECORDS, UNIVERSAL_CSV_OUTPUT_FILE)
    print(f"\nOutput saved to: {UNIVERSAL_CSV_OUTPUT_FILE}")


def run_daags_mode(instruction: str = "default") -> None:
    """Run the DAAGS transaction generator."""
    print("\n=== DAAGS Transaction Generator Mode ===")
    
    print_state_behavior("CA")
    apply_openrouter_tuning(instruction)
    print_state_behavior("CA")
    
    run_generation()


def main() -> None:
    """Main entry point."""
    # Check for universal CSV mode flag
    if "--universal-csv" in sys.argv:
        idx = sys.argv.index("--universal-csv")
        if idx + 1 < len(sys.argv):
            input_csv = sys.argv[idx + 1]
            run_universal_csv_mode(input_csv)
        else:
            print("Error: --universal-csv requires a file path")
            sys.exit(1)
    elif UNIVERSAL_CSV_MODE and UNIVERSAL_CSV_INPUT_PATH:
        # Environment variable mode
        run_universal_csv_mode(UNIVERSAL_CSV_INPUT_PATH)
    else:
        # DAAGS mode
        instruction = "default"
        if len(sys.argv) > 1:
            instruction = " ".join(sys.argv[1:]).strip()
        else:
            instruction = input("OpenRouter instruction (type 'default' to skip AI): ").strip()
        
        run_daags_mode(instruction)


if __name__ == "__main__":
    main()
