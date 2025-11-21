#!/usr/bin/env python3
"""
Test all LP models from OR-Instruct-Data-3k-LP.jsonl dataset.
Extracts LP code from completion field and tests with gurobipy.
Generates a report with run status and optimal status for each entry.
"""

import json
import re
import tempfile
import os
from gurobipy import read, GRB
import sys


def extract_lp_code(completion_text):
    """
    Extract LP model code from the completion field.
    Looks for code blocks containing LP format.
    """
    # Pattern to match ```lp or ```LP code blocks
    pattern = r'```(?:lp|LP)\s*\n(.*?)\n```'
    match = re.search(pattern, completion_text, re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()

    # Fallback: try to find LP format content without code fences
    if '\\' in completion_text and ('Maximize' in completion_text or 'Minimize' in completion_text):
        # Extract from first backslash to 'End'
        start_idx = completion_text.find('\\')
        end_idx = completion_text.find('End', start_idx)
        if start_idx != -1 and end_idx != -1:
            return completion_text[start_idx:end_idx+3].strip()

    return None


def test_lp_model(lp_code, index):
    """
    Test a single LP model with gurobipy.

    Returns:
        tuple: (run_status, optimal_status)
            run_status: 'success' or 'error'
            optimal_status: 'optimal', 'not_optimal', or 'not_applicable'
    """
    run_status = "error"
    optimal_status = "not_applicable"

    if not lp_code:
        return run_status, optimal_status

    # Create a temporary file to store the LP code
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lp', delete=False) as f:
            temp_file = f.name
            f.write(lp_code)

        # Try to read and solve the model
        model = read(temp_file)

        # Set parameters to suppress output
        model.setParam('OutputFlag', 0)
        model.setParam('LogToConsole', 0)

        # Solve the model
        model.optimize()

        # If we got here, the model ran without errors
        run_status = "success"

        # Check optimization status
        if model.status == GRB.OPTIMAL:
            optimal_status = "optimal"
        else:
            optimal_status = "not_optimal"

    except Exception as e:
        run_status = "error"
        optimal_status = "not_applicable"

    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass

    return run_status, optimal_status


def main():
    """
    Main function to process all LP models and generate report.
    """
    input_file = 'OR-Instruct-Data-3k-LP.jsonl'
    output_file = 'LP_TEST_REPORT.txt'

    print(f"Starting LP model testing for {input_file}")
    print(f"Results will be saved to {output_file}")
    print("-" * 60)

    results = []
    total_entries = 0
    success_count = 0
    optimal_count = 0

    # Process each entry
    with open(input_file, 'r', encoding='utf-8') as f:
        for index, line in enumerate(f):
            try:
                # Parse JSON
                entry = json.loads(line)
                completion = entry.get('completion', '')

                # Extract LP code
                lp_code = extract_lp_code(completion)

                # Test the LP model
                run_status, optimal_status = test_lp_model(lp_code, index)

                # Store result
                results.append((index, run_status, optimal_status))

                # Update counters
                total_entries += 1
                if run_status == "success":
                    success_count += 1
                if optimal_status == "optimal":
                    optimal_count += 1

                # Progress update every 100 entries
                if (index + 1) % 100 == 0:
                    print(f"Processed {index + 1} entries... "
                          f"(Success: {success_count}, Optimal: {optimal_count})")

            except Exception as e:
                # If JSON parsing fails, record as error
                results.append((index, "error", "not_applicable"))
                total_entries += 1
                print(f"Error processing entry {index}: {str(e)}")

    # Write results to file
    print("-" * 60)
    print(f"Writing results to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("# LP Model Testing Report\n")
        f.write(f"# Total entries tested: {total_entries}\n")
        f.write(f"# Successfully ran: {success_count}\n")
        f.write(f"# Found optimal solution: {optimal_count}\n")
        f.write("# Format: index | run_status | optimal_status\n")
        f.write("-" * 60 + "\n")

        # Write each result
        for index, run_status, optimal_status in results:
            f.write(f"{index} | {run_status} | {optimal_status}\n")

    # Print summary
    print("-" * 60)
    print("TESTING COMPLETE!")
    print(f"Total entries tested: {total_entries}")
    print(f"Successfully ran: {success_count} ({success_count/total_entries*100:.1f}%)")
    print(f"Found optimal solution: {optimal_count} ({optimal_count/total_entries*100:.1f}%)")
    print(f"Errors: {total_entries - success_count} ({(total_entries-success_count)/total_entries*100:.1f}%)")
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
