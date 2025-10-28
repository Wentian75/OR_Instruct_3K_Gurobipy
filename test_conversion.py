"""
Test script for COPTPY to Gurobipy conversion
Tests conversion on a few sample entries
"""

import json
from coptpy_to_gurobipy_converter import CoptpyToGurobiConverter


def test_conversion_samples(input_file: str, num_samples: int = 3):
    """Test conversion on sample entries and display results"""

    print("=" * 80)
    print("Testing COPTPY to Gurobipy Conversion on Sample Entries")
    print("=" * 80)

    converter = CoptpyToGurobiConverter()

    with open(input_file, 'r', encoding='utf-8') as f:
        # Read first few entries
        entries = []
        for i, line in enumerate(f):
            if i >= num_samples:
                break
            entries.append(json.loads(line.strip()))

    for idx, entry in enumerate(entries, 1):
        print(f"\n{'='*80}")
        print(f"SAMPLE {idx}")
        print(f"{'='*80}")

        # Convert entry
        converted = converter.convert_entry(entry)

        # Display prompt changes
        print("\n--- PROMPT CONVERSION ---")
        print("\nORIGINAL PROMPT (first 200 chars):")
        print(entry['prompt'][:200] + "...")

        print("\nCONVERTED PROMPT (first 200 chars):")
        print(converted['prompt'][:200] + "...")

        # Display completion changes - focus on code section
        print("\n--- COMPLETION CONVERSION ---")

        # Extract code blocks from original
        original_code_match = entry['completion'].split('```python')
        if len(original_code_match) > 1:
            original_code = original_code_match[1].split('```')[0][:500]
            print("\nORIGINAL CODE (first 500 chars):")
            print(original_code + "...")

        # Extract code blocks from converted
        converted_code_match = converted['completion'].split('```python')
        if len(converted_code_match) > 1:
            converted_code = converted_code_match[1].split('```')[0][:500]
            print("\nCONVERTED CODE (first 500 chars):")
            print(converted_code + "...")

        # Check for key conversions
        print("\n--- VERIFICATION CHECKS ---")
        checks = [
            ('import gurobipy as gp', 'Import statement conversion'),
            ('from gurobipy import GRB', 'GRB constant import'),
            ('gp.Env()', 'Environment creation'),
            ('gp.Model(', 'Model creation'),
            ('GRB.INTEGER', 'Variable type constant'),
            ('GRB.MAXIMIZE', 'Objective sense constant'),
            ('GRB.OPTIMAL', 'Status constant'),
            ('model.ObjVal', 'Objective value attribute'),
            ('gurobipy', 'Text reference to gurobipy'),
        ]

        for pattern, description in checks:
            if pattern in converted['completion']:
                print(f"✓ {description}: FOUND")
            else:
                # Some patterns might not appear in every sample
                if pattern in ['GRB.MAXIMIZE', 'GRB.INTEGER']:
                    print(f"- {description}: Not in this sample (OK)")
                else:
                    print(f"✗ {description}: MISSING")

        # Check that mathematical model is preserved
        if '## Mathematical Model:' in converted['completion']:
            print("✓ Mathematical Model section: PRESERVED")
        else:
            print("✗ Mathematical Model section: ISSUE")

        # Check that coptpy references are removed
        if 'coptpy' in converted['completion']:
            print("⚠ Warning: 'coptpy' still found in completion")
        else:
            print("✓ All coptpy references: REMOVED")

        if 'COPT.' in converted['completion']:
            print("⚠ Warning: 'COPT.' still found in completion")
        else:
            print("✓ All COPT. references: REMOVED")

    print("\n" + "=" * 80)
    print("Testing Complete!")
    print("=" * 80)


def save_sample_comparison(input_file: str, output_file: str, sample_idx: int = 0):
    """Save a detailed before/after comparison of one sample"""

    converter = CoptpyToGurobiConverter()

    with open(input_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == sample_idx:
                entry = json.loads(line.strip())
                break

    converted = converter.convert_entry(entry)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("BEFORE CONVERSION (COPTPY)\n")
        f.write("=" * 80 + "\n\n")
        f.write("PROMPT:\n")
        f.write(entry['prompt'])
        f.write("\n\nCOMPLETION:\n")
        f.write(entry['completion'])

        f.write("\n\n" + "=" * 80 + "\n")
        f.write("AFTER CONVERSION (GUROBIPY)\n")
        f.write("=" * 80 + "\n\n")
        f.write("PROMPT:\n")
        f.write(converted['prompt'])
        f.write("\n\nCOMPLETION:\n")
        f.write(converted['completion'])

    print(f"Detailed comparison saved to: {output_file}")


if __name__ == "__main__":
    input_file = '/Users/jiawei/Downloads/Project/Data/OR-Instruct-Data-3K.jsonl'

    # Test on first 3 samples
    test_conversion_samples(input_file, num_samples=3)

    # Save detailed comparison of first sample
    print("\nSaving detailed comparison of first sample...")
    save_sample_comparison(
        input_file,
        '/Users/jiawei/Downloads/Project/Data/sample_comparison.txt',
        sample_idx=0
    )
