#!/usr/bin/env python3
"""
LP Conversion Validation Tool

Validates the converted LP format dataset for:
- Structural integrity (JSONL format, required fields)
- LP format validity (sections, syntax)
- Content preservation (mathematical model, prompts)
- Completeness checks

Author: Claude Code
Date: 2025-11-21
"""

import json
import re
from typing import Dict, List, Tuple
from collections import Counter


class LPValidator:
    """Validates LP format dataset"""

    def __init__(self):
        self.stats = {
            'total_entries': 0,
            'valid_jsonl': 0,
            'has_prompt': 0,
            'has_completion': 0,
            'has_math_model': 0,
            'has_lp_format': 0,
            'has_objective': 0,
            'has_subject_to': 0,
            'has_bounds': 0,
            'has_end': 0,
            'has_integer_vars': 0,
            'has_binary_vars': 0,
            'optimization_sense': Counter(),
            'errors': []
        }

    def extract_lp_content(self, completion: str) -> str:
        """Extract LP format content from completion"""
        pattern = r'```lp\n(.*?)\n```'
        match = re.search(pattern, completion, re.DOTALL)
        if match:
            return match.group(1)
        return ""

    def validate_lp_format(self, lp_content: str) -> Tuple[bool, List[str]]:
        """
        Validate LP format structure

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        if not lp_content:
            return False, ["LP content is empty"]

        # Check for required sections
        has_objective = bool(re.search(r'(Maximize|Minimize)', lp_content, re.IGNORECASE))
        has_subject_to = 'Subject To' in lp_content or 'Subject to' in lp_content
        has_end = lp_content.strip().endswith('End')

        if not has_objective:
            issues.append("Missing objective function (Maximize/Minimize)")
        if not has_subject_to:
            issues.append("Missing 'Subject To' section")
        if not has_end:
            issues.append("Missing 'End' marker")

        # Check for variable declarations in objective or constraints
        has_variables = bool(re.search(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', lp_content))
        if not has_variables:
            issues.append("No variables found in LP content")

        is_valid = len(issues) == 0
        return is_valid, issues

    def validate_entry(self, line: str, line_num: int) -> Dict:
        """Validate a single JSONL entry"""
        result = {
            'line': line_num,
            'valid_json': False,
            'has_prompt': False,
            'has_completion': False,
            'has_math_model': False,
            'has_lp_format': False,
            'lp_valid': False,
            'lp_issues': [],
            'has_objective': False,
            'has_subject_to': False,
            'has_bounds': False,
            'has_end': False,
            'has_integer': False,
            'has_binary': False,
            'optimization_sense': None,
            'error': None
        }

        # Check JSON validity
        try:
            entry = json.loads(line.strip())
            result['valid_json'] = True
        except json.JSONDecodeError as e:
            result['error'] = f"JSON decode error: {str(e)}"
            return result

        # Check required fields
        result['has_prompt'] = 'prompt' in entry and len(entry['prompt']) > 0
        result['has_completion'] = 'completion' in entry and len(entry['completion']) > 0

        if not result['has_completion']:
            return result

        completion = entry['completion']

        # Check for mathematical model section
        result['has_math_model'] = '## Mathematical Model' in completion

        # Extract and validate LP content
        lp_content = self.extract_lp_content(completion)
        result['has_lp_format'] = len(lp_content) > 0

        if lp_content:
            # Detailed LP validation
            lp_valid, lp_issues = self.validate_lp_format(lp_content)
            result['lp_valid'] = lp_valid
            result['lp_issues'] = lp_issues

            # Check specific sections
            result['has_objective'] = bool(re.search(r'(Maximize|Minimize)', lp_content, re.IGNORECASE))
            result['has_subject_to'] = 'Subject To' in lp_content
            result['has_bounds'] = 'Bounds' in lp_content
            result['has_end'] = lp_content.strip().endswith('End')
            result['has_integer'] = 'General' in lp_content or 'Integers' in lp_content
            result['has_binary'] = 'Binary' in lp_content or 'Binaries' in lp_content

            # Determine optimization sense
            if 'Maximize' in lp_content:
                result['optimization_sense'] = 'Maximize'
            elif 'Minimize' in lp_content:
                result['optimization_sense'] = 'Minimize'

        return result

    def validate_dataset(self, input_path: str, verbose: bool = True) -> Dict:
        """
        Validate entire LP format dataset

        Args:
            input_path: Path to LP format JSONL file
            verbose: Print progress messages

        Returns:
            Validation statistics dictionary
        """
        print(f"Validating LP format dataset: {input_path}")
        print("-" * 80)

        with open(input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                self.stats['total_entries'] += 1

                result = self.validate_entry(line, line_num)

                # Update statistics
                if result['valid_json']:
                    self.stats['valid_jsonl'] += 1
                if result['has_prompt']:
                    self.stats['has_prompt'] += 1
                if result['has_completion']:
                    self.stats['has_completion'] += 1
                if result['has_math_model']:
                    self.stats['has_math_model'] += 1
                if result['has_lp_format']:
                    self.stats['has_lp_format'] += 1
                if result['has_objective']:
                    self.stats['has_objective'] += 1
                if result['has_subject_to']:
                    self.stats['has_subject_to'] += 1
                if result['has_bounds']:
                    self.stats['has_bounds'] += 1
                if result['has_end']:
                    self.stats['has_end'] += 1
                if result['has_integer']:
                    self.stats['has_integer_vars'] += 1
                if result['has_binary']:
                    self.stats['has_binary_vars'] += 1
                if result['optimization_sense']:
                    self.stats['optimization_sense'][result['optimization_sense']] += 1

                # Record errors
                if result['error']:
                    self.stats['errors'].append({
                        'line': line_num,
                        'error': result['error']
                    })
                elif not result['lp_valid']:
                    self.stats['errors'].append({
                        'line': line_num,
                        'error': f"LP validation failed: {', '.join(result['lp_issues'])}"
                    })

                if verbose and line_num % 500 == 0:
                    print(f"Validated {line_num} entries...")

        print("-" * 80)
        self.print_summary()
        return self.stats

    def print_summary(self):
        """Print validation summary"""
        total = self.stats['total_entries']

        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)

        print(f"\nTotal Entries: {total}")
        print(f"\nStructural Validation:")
        print(f"  Valid JSONL:           {self.stats['valid_jsonl']:5} ({100*self.stats['valid_jsonl']/total:6.2f}%)")
        print(f"  Has Prompt:            {self.stats['has_prompt']:5} ({100*self.stats['has_prompt']/total:6.2f}%)")
        print(f"  Has Completion:        {self.stats['has_completion']:5} ({100*self.stats['has_completion']/total:6.2f}%)")

        print(f"\nContent Validation:")
        print(f"  Has Math Model:        {self.stats['has_math_model']:5} ({100*self.stats['has_math_model']/total:6.2f}%)")
        print(f"  Has LP Format:         {self.stats['has_lp_format']:5} ({100*self.stats['has_lp_format']/total:6.2f}%)")

        print(f"\nLP Format Validation:")
        print(f"  Has Objective:         {self.stats['has_objective']:5} ({100*self.stats['has_objective']/total:6.2f}%)")
        print(f"  Has Subject To:        {self.stats['has_subject_to']:5} ({100*self.stats['has_subject_to']/total:6.2f}%)")
        print(f"  Has Bounds:            {self.stats['has_bounds']:5} ({100*self.stats['has_bounds']/total:6.2f}%)")
        print(f"  Has End Marker:        {self.stats['has_end']:5} ({100*self.stats['has_end']/total:6.2f}%)")

        print(f"\nVariable Types:")
        print(f"  Integer Variables:     {self.stats['has_integer_vars']:5} ({100*self.stats['has_integer_vars']/total:6.2f}%)")
        print(f"  Binary Variables:      {self.stats['has_binary_vars']:5} ({100*self.stats['has_binary_vars']/total:6.2f}%)")

        print(f"\nOptimization Sense:")
        for sense, count in self.stats['optimization_sense'].most_common():
            print(f"  {sense:20} {count:5} ({100*count/total:6.2f}%)")

        if self.stats['errors']:
            print(f"\nErrors Found: {len(self.stats['errors'])}")
            print("\nFirst 10 Errors:")
            for i, error_info in enumerate(self.stats['errors'][:10], 1):
                print(f"  {i}. Line {error_info['line']}: {error_info['error']}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more errors")
        else:
            print(f"\n✓ No errors found - all entries valid!")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate LP format dataset'
    )
    parser.add_argument(
        '--input',
        default='OR-Instruct-Data-3k-LP.jsonl',
        help='Input LP format JSONL file (default: OR-Instruct-Data-3k-LP.jsonl)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )

    args = parser.parse_args()

    # Create validator
    validator = LPValidator()

    # Validate dataset
    stats = validator.validate_dataset(
        input_path=args.input,
        verbose=not args.quiet
    )

    # Exit with error code if there are errors
    if stats['errors']:
        exit(1)
    else:
        exit(0)


if __name__ == '__main__':
    main()
