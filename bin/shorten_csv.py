
import csv
import argparse

parser = argparse.ArgumentParser(description="A sample script")
parser.add_argument("count", type=int, help="Number to reduce to")  # Positional
parser.add_argument("input", help="File input")  # Positional
parser.add_argument("output", help="File output")  # Positional
args = parser.parse_args()

# print(f"Hello {args.name}, you are {args.age} years old.")

import csv

n = args.count
with open(args.input, mode='r', newline='', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    header = next(reader)  # Capture the header row
    
    # 1. Collect the first n data rows
    rows = [header]
    for i, row in enumerate(reader):
        if i >= n:
            break
        rows.append(row)

# 2. Write the collected rows to a new file
with open(args.output, mode='w', newline='', encoding='utf-8') as outfile:
    writer = csv.writer(outfile)
    writer.writerows(rows)



