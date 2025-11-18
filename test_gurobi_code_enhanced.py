"""
Enhanced test script to validate all Gurobi code from OR-Instruct-Data-3K-Gurobipy.jsonl
Tracks: execution success, solution status, unbounded solutions, and objective values.
"""

import json
import re
import subprocess
import tempfile
import os
from typing import Dict, List, Tuple, Optional

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

def create_enhanced_code(original_code: str) -> str:
    """
    Enhance the code to capture solution status and suppress normal output.

    Args:
        original_code: The original Python code

    Returns:
        Enhanced code that captures solution status
    """
    # Add imports if not present
    enhanced = original_code

    # Suppress Gurobi output and capture solution status
    status_capture = """
import sys
import io
import json

# Redirect stdout to suppress Gurobi output
old_stdout = sys.stdout
sys.stdout = io.StringIO()

try:
"""

    # Indent original code
    indented_code = '\n'.join('    ' + line for line in enhanced.split('\n'))

    # Add status capture at the end
    status_output = """
finally:
    # Restore stdout
    sys.stdout = old_stdout

    # Output solution status in JSON format
    try:
        if 'model' in dir():
            status_map = {
                2: 'OPTIMAL',
                3: 'INFEASIBLE',
                4: 'INF_OR_UNBD',
                5: 'UNBOUNDED',
                6: 'CUTOFF',
                7: 'ITERATION_LIMIT',
                8: 'NODE_LIMIT',
                9: 'TIME_LIMIT',
                10: 'SOLUTION_LIMIT',
                11: 'INTERRUPTED',
                12: 'NUMERIC',
                13: 'SUBOPTIMAL',
                14: 'INPROGRESS',
                15: 'USER_OBJ_LIMIT'
            }

            status_code = model.status
            status_name = status_map.get(status_code, f'UNKNOWN_{status_code}')
            is_unbounded = (status_code == 5)  # GRB.UNBOUNDED = 5

            # Try to get objective value
            obj_val = None
            try:
                if status_code == 2:  # OPTIMAL
                    obj_val = model.ObjVal
            except:
                pass

            result = {
                'status_code': status_code,
                'status_name': status_name,
                'is_unbounded': is_unbounded,
                'objective_value': obj_val
            }
            print('###SOLUTION_STATUS###' + json.dumps(result) + '###END###')
        else:
            print('###SOLUTION_STATUS###' + json.dumps({'status_name': 'NO_MODEL', 'is_unbounded': False}) + '###END###')
    except Exception as e:
        print('###SOLUTION_STATUS###' + json.dumps({'status_name': 'ERROR', 'is_unbounded': False, 'error': str(e)}) + '###END###')
"""

    return status_capture + indented_code + status_output

def test_code_execution_enhanced(code: str, index: int, timeout: int = 30) -> Dict:
    """
    Test if the given Python code can run successfully and capture solution status.

    Args:
        code: Python code to test
        index: Index of the code in the dataset
        timeout: Maximum execution time in seconds

    Returns:
        Dict with execution results and solution status
    """
    # Create enhanced code
    enhanced_code = create_enhanced_code(code)

    # Create a temporary file to store the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        temp_file = f.name
        f.write(enhanced_code)

    result = {
        'index': index,
        'success': False,
        'error_detail': '',
        'solution_status': 'NOT_EXECUTED',
        'is_unbounded': False,
        'objective_value': None
    }

    try:
        # Run the code with a timeout
        proc_result = subprocess.run(
            ['python3', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Check if the execution was successful
        if proc_result.returncode == 0:
            result['success'] = True

            # Extract solution status from output
            stdout = proc_result.stdout
            status_match = re.search(r'###SOLUTION_STATUS###(.+?)###END###', stdout)
            if status_match:
                try:
                    status_data = json.loads(status_match.group(1))
                    result['solution_status'] = status_data.get('status_name', 'UNKNOWN')
                    result['is_unbounded'] = status_data.get('is_unbounded', False)
                    result['objective_value'] = status_data.get('objective_value')
                except json.JSONDecodeError:
                    result['solution_status'] = 'PARSE_ERROR'
            else:
                result['solution_status'] = 'NO_STATUS_OUTPUT'
        else:
            # Return the error message
            error_msg = proc_result.stderr.strip()
            if not error_msg and proc_result.stdout:
                error_msg = proc_result.stdout.strip()
            result['error_detail'] = error_msg

    except subprocess.TimeoutExpired:
        result['error_detail'] = f"Execution timeout after {timeout} seconds"
    except Exception as e:
        result['error_detail'] = f"Unexpected error: {str(e)}"
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file)
        except:
            pass

    return result

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
    unbounded_count = 0

    # Track previously failed indices
    previously_failed = [351, 764, 833, 1076, 2025, 2513, 2743, 2910]

    print("=" * 80)
    print("ENHANCED GUROBI CODE TESTING")
    print("=" * 80)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Tracking: Execution success + Solution status + Unbounded detection")
    print(f"Previously failed indices to verify: {previously_failed}")
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
                        'error_detail': 'No Python code found in completion',
                        'solution_status': 'NO_CODE',
                        'is_unbounded': False,
                        'objective_value': None
                    }
                    results.append(result)
                    print(f"[{line_num}/3000] ❌ No code found")
                else:
                    # Test code execution with enhanced tracking
                    result = test_code_execution_enhanced(code, line_num)
                    results.append(result)

                    if result['success']:
                        success_count += 1
                        status_emoji = "⚠️ UNBOUNDED" if result['is_unbounded'] else f"✅ {result['solution_status']}"

                        # Special marking for previously failed indices
                        special_mark = " 🔧 [FIXED]" if line_num in previously_failed else ""

                        print(f"[{line_num}/3000] {status_emoji}{special_mark}")

                        if result['is_unbounded']:
                            unbounded_count += 1
                    else:
                        # Print first 200 chars of error
                        error_preview = result['error_detail'][:200] + '...' if len(result['error_detail']) > 200 else result['error_detail']

                        # Special marking for previously failed indices that still fail
                        special_mark = " ⚠️ [STILL FAILING]" if line_num in previously_failed else ""

                        print(f"[{line_num}/3000] ❌ Failed{special_mark}: {error_preview}")

                total_count += 1

                # Save intermediate results every 100 entries
                if total_count % 100 == 0:
                    save_results(results, output_file)
                    success_rate = (success_count / total_count) * 100
                    unbounded_rate = (unbounded_count / total_count) * 100
                    print(f"\n--- Progress: {total_count}/3000 ---")
                    print(f"    Success: {success_rate:.2f}% | Unbounded: {unbounded_count} ({unbounded_rate:.2f}%)")
                    print()

            except json.JSONDecodeError as e:
                print(f"[{line_num}/3000] ❌ JSON decode error: {str(e)}")
                results.append({
                    'index': line_num,
                    'success': False,
                    'error_detail': f'JSON decode error: {str(e)}',
                    'solution_status': 'JSON_ERROR',
                    'is_unbounded': False,
                    'objective_value': None
                })
                total_count += 1
            except Exception as e:
                print(f"[{line_num}/3000] ❌ Unexpected error: {str(e)}")
                results.append({
                    'index': line_num,
                    'success': False,
                    'error_detail': f'Unexpected error: {str(e)}',
                    'solution_status': 'PROCESSING_ERROR',
                    'is_unbounded': False,
                    'objective_value': None
                })
                total_count += 1

    # Save final results
    save_results(results, output_file)

    # Print summary
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
    print(f"Total entries processed: {total_count}")
    print(f"Successful executions: {success_count} ({success_count / total_count * 100:.2f}%)")
    print(f"Failed executions: {total_count - success_count} ({(total_count - success_count) / total_count * 100:.2f}%)")
    print(f"Unbounded solutions: {unbounded_count} ({unbounded_count / total_count * 100:.2f}%)")
    print()

    # Check previously failed indices
    print("Previously Failed Indices Status:")
    print("-" * 80)
    for idx in previously_failed:
        idx_result = results[idx - 1]  # 0-indexed
        status = "✅ FIXED" if idx_result['success'] else "❌ STILL FAILING"
        print(f"  Index {idx}: {status}")

    print()
    print(f"Results saved to: {output_file}")
    print("=" * 80)

    return results

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
    output_file = 'OR-Instruct-Data-3K-Gurobipy-Test-Results-V2.jsonl'

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        return

    # Process the dataset
    results = process_dataset(input_file, output_file)

    # Generate unbounded solutions report
    generate_unbounded_report(results)

def generate_unbounded_report(results: List[Dict]):
    """Generate detailed report on unbounded solutions."""
    unbounded = [r for r in results if r['is_unbounded']]

    if not unbounded:
        print("\n✅ No unbounded solutions found!")
        return

    print(f"\n⚠️  Found {len(unbounded)} unbounded solutions")
    print("Generating detailed report...")

    report_content = f"""# Unbounded Solutions Report

## Summary

**Total Samples**: 3,000
**Unbounded Solutions**: {len(unbounded)}
**Percentage**: {len(unbounded) / 30:.2f}%

## Unbounded Solution Indices

{', '.join(str(r['index']) for r in unbounded)}

## Detailed Breakdown

"""

    for i, result in enumerate(unbounded, 1):
        report_content += f"""
### Entry #{i}: Index {result['index']}

- **Solution Status**: {result['solution_status']}
- **Objective Value**: {result['objective_value']}

---
"""

    # Save report
    with open('UNBOUNDED_SOLUTIONS_REPORT.md', 'w') as f:
        f.write(report_content)

    print(f"Unbounded solutions report saved to: UNBOUNDED_SOLUTIONS_REPORT.md")

if __name__ == '__main__':
    main()
