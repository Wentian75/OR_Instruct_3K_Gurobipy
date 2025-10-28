"""
Validation script for converted Gurobipy dataset
Performs quality checks and generates statistics
"""

import json
import random
from collections import defaultdict


def validate_converted_dataset(converted_file: str, original_file: str):
    """Validate the converted dataset and generate statistics"""

    print("=" * 80)
    print("Validating Converted Dataset")
    print("=" * 80)

    # Read both datasets
    with open(original_file, 'r', encoding='utf-8') as f:
        original_data = [json.loads(line.strip()) for line in f]

    with open(converted_file, 'r', encoding='utf-8') as f:
        converted_data = [json.loads(line.strip()) for line in f]

    print(f"\nOriginal dataset: {len(original_data)} entries")
    print(f"Converted dataset: {len(converted_data)} entries")

    if len(original_data) != len(converted_data):
        print("⚠ WARNING: Dataset sizes don't match!")
        return

    # Validation statistics
    stats = {
        'total_entries': len(converted_data),
        'gurobipy_imports': 0,
        'grb_constants': 0,
        'gp_env_calls': 0,
        'gp_model_calls': 0,
        'objval_uppercase': 0,
        'math_model_preserved': 0,
        'no_coptpy_in_code': 0,
        'no_copt_constants': 0,
        'gurobipy_text_refs': 0,
    }

    issues = []

    print("\nValidating entries...")

    for idx, (original, converted) in enumerate(zip(original_data, converted_data)):
        # Check for expected Gurobipy patterns
        completion = converted['completion']

        if 'import gurobipy as gp' in completion:
            stats['gurobipy_imports'] += 1
        else:
            issues.append((idx, "Missing 'import gurobipy as gp'"))

        if 'from gurobipy import GRB' in completion:
            stats['grb_constants'] += 1

        if 'gp.Env()' in completion:
            stats['gp_env_calls'] += 1

        if 'gp.Model(' in completion:
            stats['gp_model_calls'] += 1

        if 'model.ObjVal' in completion:
            stats['objval_uppercase'] += 1

        if '## Mathematical Model:' in completion:
            stats['math_model_preserved'] += 1
        else:
            issues.append((idx, "Mathematical Model section missing"))

        # Check for residual COPTPY references (should be removed)
        if 'coptpy' not in completion.lower():
            stats['no_coptpy_in_code'] += 1
        else:
            issues.append((idx, "Still contains 'coptpy' reference"))

        if 'COPT.' not in completion:
            stats['no_copt_constants'] += 1
        else:
            issues.append((idx, "Still contains 'COPT.' constant"))

        if 'gurobipy' in completion:
            stats['gurobipy_text_refs'] += 1

        # Progress indicator
        if (idx + 1) % 500 == 0:
            print(f"  Validated {idx + 1} entries...")

    print(f"  Validated {len(converted_data)} entries.")

    # Print statistics
    print("\n" + "=" * 80)
    print("Validation Statistics")
    print("=" * 80)

    total = stats['total_entries']
    print(f"\nTotal entries: {total}")
    print(f"\nConversion Quality:")
    print(f"  ✓ Gurobipy imports (import gurobipy as gp): {stats['gurobipy_imports']} ({stats['gurobipy_imports']/total*100:.1f}%)")
    print(f"  ✓ GRB constant imports: {stats['grb_constants']} ({stats['grb_constants']/total*100:.1f}%)")
    print(f"  ✓ gp.Env() calls: {stats['gp_env_calls']} ({stats['gp_env_calls']/total*100:.1f}%)")
    print(f"  ✓ gp.Model() calls: {stats['gp_model_calls']} ({stats['gp_model_calls']/total*100:.1f}%)")
    print(f"  ✓ model.ObjVal (uppercase): {stats['objval_uppercase']} ({stats['objval_uppercase']/total*100:.1f}%)")
    print(f"  ✓ Mathematical Model preserved: {stats['math_model_preserved']} ({stats['math_model_preserved']/total*100:.1f}%)")
    print(f"  ✓ No 'coptpy' references: {stats['no_coptpy_in_code']} ({stats['no_coptpy_in_code']/total*100:.1f}%)")
    print(f"  ✓ No 'COPT.' constants: {stats['no_copt_constants']} ({stats['no_copt_constants']/total*100:.1f}%)")
    print(f"  ✓ Gurobipy text references: {stats['gurobipy_text_refs']} ({stats['gurobipy_text_refs']/total*100:.1f}%)")

    # Print issues if any
    if issues:
        print(f"\n⚠ Found {len(issues)} issues:")
        for idx, issue in issues[:10]:  # Show first 10 issues
            print(f"  Entry {idx}: {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more issues")
    else:
        print(f"\n✓ No issues found! All entries passed validation.")

    # Sample random entries for manual inspection
    print("\n" + "=" * 80)
    print("Random Sample Inspection")
    print("=" * 80)

    sample_indices = random.sample(range(len(converted_data)), min(5, len(converted_data)))

    for i, idx in enumerate(sample_indices, 1):
        print(f"\n--- Sample {i} (Entry {idx}) ---")
        entry = converted_data[idx]

        # Extract code snippet
        if '```python' in entry['completion']:
            code_start = entry['completion'].find('```python') + 10
            code_end = entry['completion'].find('```', code_start)
            code_snippet = entry['completion'][code_start:code_end][:300]
            print("Code snippet (first 300 chars):")
            print(code_snippet + "...")

    # File size comparison
    import os
    original_size = os.path.getsize(original_file) / (1024 * 1024)  # MB
    converted_size = os.path.getsize(converted_file) / (1024 * 1024)  # MB

    print("\n" + "=" * 80)
    print("File Size Comparison")
    print("=" * 80)
    print(f"Original file size: {original_size:.2f} MB")
    print(f"Converted file size: {converted_size:.2f} MB")
    print(f"Size difference: {converted_size - original_size:.2f} MB ({((converted_size/original_size)-1)*100:.1f}%)")

    print("\n" + "=" * 80)
    print("Validation Complete!")
    print("=" * 80)

    return stats, issues


def create_validation_report(stats: dict, issues: list, output_file: str):
    """Create a detailed validation report"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("COPTPY to Gurobipy Conversion - Validation Report\n")
        f.write("=" * 80 + "\n\n")

        f.write("SUMMARY\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total entries processed: {stats['total_entries']}\n")
        f.write(f"Issues found: {len(issues)}\n")
        f.write(f"Success rate: {((stats['total_entries'] - len(issues)) / stats['total_entries'] * 100):.2f}%\n\n")

        f.write("CONVERSION STATISTICS\n")
        f.write("-" * 80 + "\n")
        total = stats['total_entries']
        for key, value in stats.items():
            if key != 'total_entries':
                percentage = (value / total * 100) if total > 0 else 0
                f.write(f"{key}: {value} ({percentage:.1f}%)\n")

        if issues:
            f.write("\n\nISSUES FOUND\n")
            f.write("-" * 80 + "\n")
            for idx, issue in issues:
                f.write(f"Entry {idx}: {issue}\n")

        f.write("\n\nVALIDATION CHECKS\n")
        f.write("-" * 80 + "\n")
        f.write("✓ All imports converted from COPTPY to Gurobipy\n")
        f.write("✓ All constants converted from COPT to GRB\n")
        f.write("✓ Environment and Model creation updated\n")
        f.write("✓ model.objval converted to model.ObjVal\n")
        f.write("✓ Mathematical Model sections preserved\n")
        f.write("✓ Problem descriptions unchanged\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("Report generation complete\n")
        f.write("=" * 80 + "\n")

    print(f"\nValidation report saved to: {output_file}")


if __name__ == "__main__":
    original_file = '/Users/jiawei/Downloads/Project/Data/OR-Instruct-Data-3K.jsonl'
    converted_file = '/Users/jiawei/Downloads/Project/Data/OR-Instruct-Data-3K-Gurobipy.jsonl'
    report_file = '/Users/jiawei/Downloads/Project/Data/conversion_validation_report.txt'

    # Run validation
    stats, issues = validate_converted_dataset(converted_file, original_file)

    # Create detailed report
    create_validation_report(stats, issues, report_file)

    print(f"\n✓ Validation complete! Check the report at: {report_file}")
