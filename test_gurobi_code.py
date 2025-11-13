"""
Test script to validate all Gurobi code from OR-Instruct-Data-3K-Gurobipy.jsonl
Creates a test results dataset with index, success status, and error details.
"""

import json
import re
import subprocess
import tempfile
import os
from typing import Dict, List, Tuple

def extract_python_code(completion: str) -> str:
    """
    Extract Python code from the completion text.

    Args:
        completion: The completion text containing the Python code

    Returns:
        The extracted Python code as a string
    """
    # Look for code blocks marked with ```python
    code_match = re.search(r'```python\n(.*?)\n```', completion, re.DOTALL)
    if code_match:
        return code_match.group(1)

    # If no python code block found, look for any code block
    code_match = re.search(r'```\n(.*?)\n```', completion, re.DOTALL)
    if code_match:
        return code_match.group(1)

    return ""

def test_code_execution(code: str, index: int, timeout: int = 30) -> Tuple[bool, str]:
    """
    Test if the given Python code can run successfully.

    Args:
        code: Python code to test
        index: Index of the code in the dataset
        timeout: Maximum execution time in seconds

    Returns:
        Tuple of (success: bool, error_message: str)
    """
    # Create a temporary file to store the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        temp_file = f.name
        f.write(code)

    try:
        # Run the code with a timeout
        result = subprocess.run(
            ['python3', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Check if the execution was successful
        if result.returncode == 0:
            return True, ""
        else:
            # Return the error message
            error_msg = result.stderr.strip()
            if not error_msg and result.stdout:
                error_msg = result.stdout.strip()
            return False, error_msg

    except subprocess.TimeoutExpired:
        return False, f"Execution timeout after {timeout} seconds"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file)
        except:
            pass

def process_dataset(input_file: str, output_file: str):
    """
    Process the entire dataset and create test results.

    Args:
        input_file: Path to the input JSONL file
        output_file: Path to the output JSONL file for test results
    """
    results = []
    total_count = 0
    success_count = 0

    print("Starting to process dataset...")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print("-" * 80)

    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            try:
                # Parse JSON line
                entry = json.loads(line)
                completion = entry.get('completion', '')

                # Extract Python code
                code = extract_python_code(completion)

                if not code:
                    result = {
                        'index': line_num,
                        'success': False,
                        'error_detail': 'No Python code found in completion'
                    }
                    results.append(result)
                    print(f"[{line_num}/3000] ❌ No code found")
                else:
                    # Test code execution
                    success, error_msg = test_code_execution(code, line_num)

                    result = {
                        'index': line_num,
                        'success': success,
                        'error_detail': error_msg if not success else ''
                    }
                    results.append(result)

                    if success:
                        success_count += 1
                        print(f"[{line_num}/3000] ✅ Success")
                    else:
                        # Print first 200 chars of error
                        error_preview = error_msg[:200] + '...' if len(error_msg) > 200 else error_msg
                        print(f"[{line_num}/3000] ❌ Failed: {error_preview}")

                total_count += 1

                # Save intermediate results every 100 entries
                if total_count % 100 == 0:
                    save_results(results, output_file)
                    success_rate = (success_count / total_count) * 100
                    print(f"\n--- Progress: {total_count}/3000 ({success_rate:.2f}% success) ---\n")

            except json.JSONDecodeError as e:
                print(f"[{line_num}/3000] ❌ JSON decode error: {str(e)}")
                results.append({
                    'index': line_num,
                    'success': False,
                    'error_detail': f'JSON decode error: {str(e)}'
                })
                total_count += 1
            except Exception as e:
                print(f"[{line_num}/3000] ❌ Unexpected error: {str(e)}")
                results.append({
                    'index': line_num,
                    'success': False,
                    'error_detail': f'Unexpected error: {str(e)}'
                })
                total_count += 1

    # Save final results
    save_results(results, output_file)

    # Print summary
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
    print(f"Total entries processed: {total_count}")
    print(f"Successful executions: {success_count}")
    print(f"Failed executions: {total_count - success_count}")
    print(f"Success rate: {(success_count / total_count * 100):.2f}%")
    print(f"Results saved to: {output_file}")
    print("=" * 80)

def save_results(results: List[Dict], output_file: str):
    """
    Save results to JSONL file.

    Args:
        results: List of result dictionaries
        output_file: Path to output file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

def main():
    """Main function to run the testing pipeline."""
    input_file = 'OR-Instruct-Data-3K-Gurobipy.jsonl'
    output_file = 'OR-Instruct-Data-3K-Gurobipy-Test-Results.jsonl'

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        return

    # Process the dataset
    process_dataset(input_file, output_file)

if __name__ == '__main__':
    main()
