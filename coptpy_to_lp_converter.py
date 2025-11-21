#!/usr/bin/env python3
"""
COPTPY/Gurobipy Python Code to LP Format Converter

This tool converts the OR-Instruct dataset from Python code solutions
to standard LP file format solutions. It executes the Python code to
build optimization models, then exports them to LP format.

Author: Claude Code
Date: 2025-11-21
"""

import json
import re
import sys
import os
import tempfile
from typing import Dict, Tuple, Optional
from io import StringIO
import traceback


class LPConverter:
    """Converts COPT/Gurobipy Python code to LP file format"""

    def __init__(self, use_gurobipy: bool = True):
        """
        Initialize converter

        Args:
            use_gurobipy: If True, convert COPT to Gurobi first, then to LP
        """
        self.use_gurobipy = use_gurobipy
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': []
        }

    def extract_code_from_completion(self, completion: str) -> Optional[str]:
        """
        Extract Python code block from completion field

        Args:
            completion: The completion text containing markdown and code

        Returns:
            Python code string or None if not found
        """
        # Pattern to match Python code blocks
        pattern = r'```python\n(.*?)\n```'
        match = re.search(pattern, completion, re.DOTALL)

        if match:
            return match.group(1)
        return None

    def extract_mathematical_model(self, completion: str) -> str:
        """
        Extract the mathematical model section from completion

        Args:
            completion: The completion text

        Returns:
            Mathematical model section text
        """
        # Split at the Python code section
        parts = completion.split('## Python Code Solution')
        if len(parts) > 0:
            return parts[0].strip()
        return ""

    def convert_copt_to_gurobipy(self, code: str) -> str:
        """
        Convert COPTPY code to Gurobipy code

        Args:
            code: COPTPY Python code

        Returns:
            Gurobipy Python code
        """
        # Basic COPT to Gurobi conversions
        conversions = [
            ('import coptpy as cp', 'import gurobipy as gp'),
            ('from coptpy import COPT', 'from gurobipy import GRB'),
            ('cp.Envr()', 'gp.Env(GRB.Env.CloudAccessID, GRB.Env.CloudSecretKey)' if False else 'gp.Env()'),
            ('env.createModel(', 'gp.Model('),
            ('cp.quicksum(', 'gp.quicksum('),
            ('COPT.INTEGER', 'GRB.INTEGER'),
            ('COPT.CONTINUOUS', 'GRB.CONTINUOUS'),
            ('COPT.BINARY', 'GRB.BINARY'),
            ('COPT.MAXIMIZE', 'GRB.MAXIMIZE'),
            ('COPT.MINIMIZE', 'GRB.MINIMIZE'),
            ('COPT.OPTIMAL', 'GRB.OPTIMAL'),
            ('model.solve()', 'model.optimize()'),
            ('model.objval', 'model.ObjVal'),
        ]

        converted = code
        for old, new in conversions:
            converted = converted.replace(old, new)

        return converted

    def execute_code_and_get_model(self, code: str) -> Tuple[Optional[object], Optional[str]]:
        """
        Execute Python code and extract the Gurobi model object

        Args:
            code: Python code that creates a Gurobi model

        Returns:
            Tuple of (Gurobi model object or None, error message or None)
        """
        try:
            # Suppress stdout during execution
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = StringIO()
            sys.stderr = StringIO()

            # Create execution environment
            # Import gurobipy into the execution environment
            import gurobipy as gp
            from gurobipy import GRB

            # Use a single namespace for both globals and locals to avoid scoping issues
            # with list comprehensions and generator expressions
            exec_namespace = {
                'gp': gp,
                'GRB': GRB,
                'gurobipy': gp,
                '__builtins__': __builtins__
            }

            # Execute the code (using same dict for globals and locals)
            exec(code, exec_namespace, exec_namespace)

            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Find the model object in the execution namespace
            model = None
            for var_name, var_value in exec_namespace.items():
                if hasattr(var_value, 'write') and hasattr(var_value, 'optimize'):
                    model = var_value
                    break

            if model is None:
                return None, "Model object not found in execution environment"

            return model, None

        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            error_msg = f"{type(e).__name__}: {str(e)}"
            return None, error_msg

    def model_to_lp_format(self, model: object) -> Optional[str]:
        """
        Convert Gurobi model to LP format string

        Args:
            model: Gurobi model object

        Returns:
            LP format string or None if conversion fails
        """
        try:
            # Create temporary file for LP output
            with tempfile.NamedTemporaryFile(mode='w', suffix='.lp', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            # Write model to LP format
            model.write(tmp_path)

            # Read the LP file
            with open(tmp_path, 'r') as f:
                lp_content = f.read()

            # Clean up temp file
            os.unlink(tmp_path)

            return lp_content

        except Exception as e:
            return None

    def create_lp_completion(self, math_model: str, lp_content: str) -> str:
        """
        Create new completion field with mathematical model and LP format

        Args:
            math_model: Mathematical model section
            lp_content: LP format content

        Returns:
            New completion string
        """
        return f"{math_model}\n\n## LP Format Solution:\n```lp\n{lp_content}\n```"

    def convert_entry(self, entry: Dict) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Convert a single JSONL entry from Python code to LP format

        Args:
            entry: Dictionary with 'prompt' and 'completion' fields

        Returns:
            Tuple of (converted_entry, error_message)
        """
        try:
            prompt = entry.get('prompt', '')
            completion = entry.get('completion', '')

            # Extract Python code
            code = self.extract_code_from_completion(completion)
            if code is None:
                return None, "No Python code block found in completion"

            # Extract mathematical model section
            math_model = self.extract_mathematical_model(completion)

            # Convert COPT to Gurobi if needed
            if 'coptpy' in code.lower() or 'COPT' in code:
                code = self.convert_copt_to_gurobipy(code)

            # Execute code and get model
            model, exec_error = self.execute_code_and_get_model(code)
            if model is None:
                return None, f"Failed to execute code: {exec_error}"

            # Convert model to LP format
            lp_content = self.model_to_lp_format(model)
            if lp_content is None:
                return None, "Failed to convert model to LP format"

            # Create new completion
            new_completion = self.create_lp_completion(math_model, lp_content)

            # Create new entry
            new_entry = {
                'prompt': prompt,
                'completion': new_completion
            }

            return new_entry, None

        except Exception as e:
            return None, f"Unexpected error: {str(e)}\n{traceback.format_exc()}"

    def convert_dataset(self, input_path: str, output_path: str,
                       max_entries: Optional[int] = None,
                       verbose: bool = True) -> Dict:
        """
        Convert entire dataset from Python code to LP format

        Args:
            input_path: Path to input JSONL file
            output_path: Path to output JSONL file
            max_entries: Maximum number of entries to process (None = all)
            verbose: Print progress messages

        Returns:
            Statistics dictionary
        """
        print(f"Starting conversion from {input_path} to {output_path}")
        print(f"Maximum entries to process: {max_entries if max_entries else 'ALL'}")
        print("-" * 80)

        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': []
        }

        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:

            for line_num, line in enumerate(infile, 1):
                # Check if we've reached the limit
                if max_entries and line_num > max_entries:
                    break

                self.stats['total'] += 1

                try:
                    # Parse JSON entry
                    entry = json.loads(line.strip())

                    # Convert entry
                    new_entry, error = self.convert_entry(entry)

                    if new_entry:
                        # Write successful conversion
                        outfile.write(json.dumps(new_entry, ensure_ascii=False) + '\n')
                        self.stats['success'] += 1

                        if verbose and self.stats['success'] % 100 == 0:
                            print(f"Processed {self.stats['success']} entries successfully...")
                    else:
                        # Record failure
                        self.stats['failed'] += 1
                        self.stats['errors'].append({
                            'line': line_num,
                            'error': error
                        })

                        if verbose:
                            print(f"Entry {line_num} FAILED: {error}")

                except json.JSONDecodeError as e:
                    self.stats['failed'] += 1
                    self.stats['errors'].append({
                        'line': line_num,
                        'error': f"JSON decode error: {str(e)}"
                    })
                    if verbose:
                        print(f"Entry {line_num} FAILED: JSON decode error")

        print("-" * 80)
        print(f"Conversion complete!")
        print(f"Total entries: {self.stats['total']}")
        print(f"Successful: {self.stats['success']} ({100*self.stats['success']/self.stats['total']:.2f}%)")
        print(f"Failed: {self.stats['failed']} ({100*self.stats['failed']/self.stats['total']:.2f}%)")

        return self.stats


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert COPT/Gurobipy Python code to LP format'
    )
    parser.add_argument(
        '--input',
        default='OR-Instruct-Data-3K.jsonl',
        help='Input JSONL file (default: OR-Instruct-Data-3K.jsonl)'
    )
    parser.add_argument(
        '--output',
        default='OR-Instruct-Data-3k-LP.jsonl',
        help='Output JSONL file (default: OR-Instruct-Data-3k-LP.jsonl)'
    )
    parser.add_argument(
        '--max-entries',
        type=int,
        default=None,
        help='Maximum number of entries to process (default: all)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: process only first 10 entries'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )

    args = parser.parse_args()

    # Test mode overrides max_entries
    if args.test:
        args.max_entries = 10
        print("TEST MODE: Processing only first 10 entries")

    # Create converter
    converter = LPConverter(use_gurobipy=True)

    # Convert dataset
    stats = converter.convert_dataset(
        input_path=args.input,
        output_path=args.output,
        max_entries=args.max_entries,
        verbose=not args.quiet
    )

    # Print error summary if any
    if stats['failed'] > 0:
        print("\n" + "=" * 80)
        print("ERROR SUMMARY")
        print("=" * 80)
        for i, error_info in enumerate(stats['errors'][:10], 1):  # Show first 10 errors
            print(f"\n{i}. Line {error_info['line']}:")
            print(f"   {error_info['error'][:200]}")  # Truncate long errors

        if len(stats['errors']) > 10:
            print(f"\n... and {len(stats['errors']) - 10} more errors")


if __name__ == '__main__':
    main()
