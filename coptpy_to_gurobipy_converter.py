"""
COPTPY to Gurobipy Dataset Converter
Converts OR-Instruct dataset from COPTPY API to Gurobipy API
Preserves mathematical models and problem descriptions
"""

import json
import re
from typing import Dict, Tuple


class CoptpyToGurobiConverter:
    """Converts COPTPY code and references to Gurobipy"""

    def __init__(self):
        # Define all conversion mappings
        self.code_replacements = [
            # Import statements
            (r'import coptpy as cp', 'import gurobipy as gp'),
            (r'from coptpy import COPT', 'from gurobipy import GRB'),

            # Environment and Model creation
            (r'cp\.Envr\(\)', 'gp.Env()'),
            (r'env\.createModel\(', 'gp.Model('),

            # Constants - Variable types
            (r'COPT\.INTEGER', 'GRB.INTEGER'),
            (r'COPT\.CONTINUOUS', 'GRB.CONTINUOUS'),
            (r'COPT\.BINARY', 'GRB.BINARY'),

            # Constants - Optimization sense
            (r'COPT\.MAXIMIZE', 'GRB.MAXIMIZE'),
            (r'COPT\.MINIMIZE', 'GRB.MINIMIZE'),

            # Constants - Status
            (r'COPT\.OPTIMAL', 'GRB.OPTIMAL'),

            # Methods and attributes
            (r'model\.objval', 'model.ObjVal'),
            (r'cp\.quicksum\(', 'gp.quicksum('),
        ]

        self.text_replacements = [
            # Text references in markdown and comments
            (r'using `coptpy`', 'using `gurobipy`'),
            (r'`coptpy` library', '`gurobipy` library'),
            (r'the `coptpy`', 'the `gurobipy`'),
            (r'## Python Code Solution Using `coptpy`:', '## Python Code Solution Using `gurobipy`:'),
            (r'COPT environment', 'Gurobi environment'),
            (r'COPT model', 'Gurobi model'),
            (r'Create a COPT', 'Create a Gurobi'),
            (r'create a COPT', 'create a Gurobi'),
            (r'Create COPT', 'Create Gurobi'),
            (r'Creates a COPT', 'Creates a Gurobi'),
            # Installation instructions
            (r'pip install coptpy', 'pip install gurobipy'),
            (r'install coptpy', 'install gurobipy'),
            (r'installed coptpy', 'installed gurobipy'),
            # Additional text references
            (r'CPLEX or Gurobi', 'optimization solvers'),
            (r'such as CPLEX or Gurobi', 'such as Gurobi'),
            (r'importing the `coptpy`', 'importing the `gurobipy`'),
            (r'Imports the `coptpy`', 'Imports the `gurobipy`'),
            (r'COPTPY libraries', 'Gurobipy libraries'),
            (r'necessary COPTPY', 'necessary Gurobipy'),
            (r'the COPTPY', 'the Gurobipy'),
            (r'import COPTPY', 'import Gurobipy'),
        ]

    def convert_prompt(self, prompt: str) -> str:
        """Convert prompt section - only changes coptpy references to gurobipy"""
        # Only replace the initial instruction mentioning coptpy
        converted = prompt.replace(
            'Build a mathematical model and corresponding python code using `coptpy`',
            'Build a mathematical model and corresponding python code using `gurobipy`'
        )
        return converted

    def convert_completion(self, completion: str) -> str:
        """Convert completion section - preserves math model, converts code and text"""
        # Split into Mathematical Model and Python Code sections
        parts = completion.split('## Python Code Solution Using `coptpy`:')

        if len(parts) != 2:
            # Handle edge cases where the split pattern might be slightly different
            # Try alternative patterns
            alt_patterns = [
                '## Python Code Solution Using `coptpy`',
                'Python Code Solution Using `coptpy`:',
                'Python Code Solution Using `coptpy`'
            ]

            for pattern in alt_patterns:
                if pattern in completion:
                    parts = completion.split(pattern)
                    break

        if len(parts) == 2:
            math_model_section = parts[0]
            code_section = parts[1]

            # Convert the code section
            converted_code = self._convert_code_section(code_section)

            # Reassemble with updated header
            converted_completion = math_model_section + '## Python Code Solution Using `gurobipy`:' + converted_code
        else:
            # Fallback: if we can't split properly, just apply text replacements
            # but this shouldn't happen with well-formed data
            converted_completion = self._apply_text_replacements(completion)

        return converted_completion

    def _convert_code_section(self, code_section: str) -> str:
        """Convert the Python code section with all API replacements"""
        converted = code_section

        # Apply code replacements (for code blocks)
        for pattern, replacement in self.code_replacements:
            converted = re.sub(pattern, replacement, converted)

        # Apply text replacements (for descriptions and comments)
        for pattern, replacement in self.text_replacements:
            converted = re.sub(pattern, replacement, converted)

        return converted

    def _apply_text_replacements(self, text: str) -> str:
        """Apply only text replacements (not code-specific)"""
        converted = text
        for pattern, replacement in self.text_replacements:
            converted = re.sub(pattern, replacement, converted)
        return converted

    def convert_entry(self, entry: Dict) -> Dict:
        """Convert a single JSONL entry"""
        converted_entry = {
            'prompt': self.convert_prompt(entry['prompt']),
            'completion': self.convert_completion(entry['completion'])
        }
        return converted_entry

    def convert_dataset(self, input_file: str, output_file: str) -> Tuple[int, int]:
        """
        Convert entire dataset from COPTPY to Gurobipy

        Args:
            input_file: Path to input JSONL file (COPTPY)
            output_file: Path to output JSONL file (Gurobipy)

        Returns:
            Tuple of (total_entries, successfully_converted)
        """
        total_entries = 0
        successful_conversions = 0

        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:

            for line_num, line in enumerate(infile, 1):
                total_entries += 1

                try:
                    # Parse JSON entry
                    entry = json.loads(line.strip())

                    # Convert entry
                    converted_entry = self.convert_entry(entry)

                    # Write to output file
                    outfile.write(json.dumps(converted_entry, ensure_ascii=False) + '\n')

                    successful_conversions += 1

                    # Progress indicator every 100 entries
                    if line_num % 100 == 0:
                        print(f"Processed {line_num} entries...")

                except Exception as e:
                    print(f"Error processing entry {line_num}: {str(e)}")
                    continue

        return total_entries, successful_conversions


def main():
    """Main conversion function"""
    input_file = '/Users/jiawei/Downloads/Project/Data/OR-Instruct-Data-3K.jsonl'
    output_file = '/Users/jiawei/Downloads/Project/Data/OR-Instruct-Data-3K-Gurobipy.jsonl'

    print("=" * 60)
    print("COPTPY to Gurobipy Dataset Converter")
    print("=" * 60)
    print(f"\nInput file: {input_file}")
    print(f"Output file: {output_file}")
    print("\nStarting conversion...\n")

    # Create converter instance
    converter = CoptpyToGurobiConverter()

    # Convert dataset
    total, successful = converter.convert_dataset(input_file, output_file)

    # Print results
    print("\n" + "=" * 60)
    print("Conversion Complete!")
    print("=" * 60)
    print(f"Total entries: {total}")
    print(f"Successfully converted: {successful}")
    print(f"Failed conversions: {total - successful}")
    print(f"Success rate: {(successful/total)*100:.2f}%")
    print(f"\nOutput saved to: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
