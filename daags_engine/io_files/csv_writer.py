"""CSV streaming writer used by `daags_engine.generator`.

The generator writes large datasets in batches, appending to the same file
instead of holding everything in memory.
"""

# daags_engine/outputs/csv_writer.py

import os
import csv


def ensure_output_folder(path: str):
    os.makedirs(path, exist_ok=True)


def write_batch(file_path: str, rows: list, header: list = None, write_header=False):
    """
    Appends a batch of rows to CSV.
    Uses streaming so memory stays low.
    """
    mode = "w" if write_header else "a"

    with open(file_path, mode, newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if write_header and header:
            writer.writerow(header)

        writer.writerows(rows)
