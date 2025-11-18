#!/usr/bin/env python3
"""
Interactive tool for substituting incorrect code in JSONL dataset
"""

import json
import os
from typing import Dict, Any, Optional

class CodeSubstitutionTool:
    def __init__(self, jsonl_file_path: str):
        """
        Initialize the tool with the path to the JSONL file
        
        Args:
            jsonl_file_path: Path to the JSONL file containing the dataset
        """
        self.jsonl_file_path = jsonl_file_path
        self.data = []
        self.load_data()
    
    def load_data(self):
        """Load data from the JSONL file"""
        try:
            with open(self.jsonl_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data_point = json.loads(line.strip())
                        self.data.append(data_point)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Error parsing line {line_num}: {e}")
            
            print(f"Successfully loaded {len(self.data)} records from {self.jsonl_file_path}")
            
        except FileNotFoundError:
            print(f"Error: File {self.jsonl_file_path} not found!")
            raise
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
    
    def save_data(self, backup: bool = True):
        """
        Save the modified data back to the JSONL file
        
        Args:
            backup: Whether to create a backup of the original file
        """
        if backup:
            backup_path = f"{self.jsonl_file_path}.backup"
            if not os.path.exists(backup_path):
                # Only create backup if it doesn't exist
                import shutil
                shutil.copy2(self.jsonl_file_path, backup_path)
                print(f"Backup created: {backup_path}")
        
        try:
            with open(self.jsonl_file_path, 'w', encoding='utf-8') as f:
                for data_point in self.data:
                    json.dump(data_point, f, ensure_ascii=False)
                    f.write('\n')
            
            print(f"Successfully saved {len(self.data)} records to {self.jsonl_file_path}")
            
        except Exception as e:
            print(f"Error saving data: {e}")
            raise
    
    def get_record_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get a record by its index (0-based)
        
        Args:
            index: The index of the record (0-based)
            
        Returns:
            The record at the specified index, or None if index is invalid
        """
        if 0 <= index < len(self.data):
            return self.data[index]
        else:
            print(f"Error: Index {index} is out of range (0-{len(self.data)-1})")
            return None
    
    def extract_code_from_completion(self, completion: str) -> str:
        """
        Extract Python code from the completion text
        
        Args:
            completion: The completion text containing code
            
        Returns:
            Extracted Python code
        """
        # Look for code blocks marked with ```python
        import re
        
        # Find all code blocks
        code_blocks = re.findall(r'```python\n(.*?)\n```', completion, re.DOTALL)
        
        if code_blocks:
            # Join all code blocks if multiple exist
            return '\n\n# ===== Code Block Separator =====\n\n'.join(code_blocks)
        else:
            # If no clear code blocks, try to find any code-like content
            # This is a fallback and might need adjustment based on actual data format
            lines = completion.split('\n')
            code_lines = []
            in_code_section = False
            
            for line in lines:
                if 'import' in line or 'def ' in line or 'class ' in line or line.strip().startswith('#'):
                    in_code_section = True
                if in_code_section:
                    code_lines.append(line)
                if line.strip() == '' and in_code_section and len(code_lines) > 5:
                    # End of code section
                    break
            
            return '\n'.join(code_lines) if code_lines else "No clear code block found"
    
    def substitute_code_interactive(self):
        """
        Interactive method to substitute code
        """
        print("=== Code Substitution Tool ===")
        print(f"Dataset contains {len(self.data)} records (indices 0-{len(self.data)-1})")
        
        while True:
            try:
                # Get index from user
                index_input = input(f"\nEnter the index of the sample to modify (0-{len(self.data)-1}, or 'quit' to exit): ").strip()
                
                if index_input.lower() in ['quit', 'q', 'exit']:
                    print("Exiting...")
                    break
                
                index = int(index_input)
                
                # Get the record
                record = self.get_record_by_index(index)
                if record is None:
                    continue
                
                # Display the original data
                print(f"\n{'='*80}")
                print(f"RECORD #{index}")
                print(f"{'='*80}")
                
                print("\n--- PROMPT ---")
                print(record.get('prompt', 'No prompt found')[:500] + "..." if len(record.get('prompt', '')) > 500 else record.get('prompt', 'No prompt found'))
                
                print("\n--- ORIGINAL CODE ---")
                original_code = self.extract_code_from_completion(record.get('completion', ''))
                print(original_code)
                
                print(f"\n{'='*80}")
                
                # Ask if user wants to substitute
                substitute = input("Do you want to substitute the code for this record? (y/n): ").strip().lower()
                
                if substitute == 'y':
                    print("\nPlease enter the correct code (end with '###END###' on a new line):")
                    
                    new_code_lines = []
                    while True:
                        line = input()
                        if line.strip() == "###END###":
                            break
                        new_code_lines.append(line)
                    
                    new_code = '\n'.join(new_code_lines)
                    
                    if new_code.strip():
                        # Substitute the code in the completion
                        # We need to replace the Python code block in the completion
                        original_completion = record['completion']
                        
                        # Find and replace the code block
                        import re
                        
                        # Pattern to find Python code blocks
                        pattern = r'(```python\n)(.*?)(\n```)'
                        
                        def replace_code(match):
                            return f"{match.group(1)}{new_code}{match.group(3)}"
                        
                        new_completion = re.sub(pattern, replace_code, original_completion, flags=re.DOTALL)
                        
                        # If no code block was found, append the new code
                        if new_completion == original_completion:
                            new_completion += f"\n\n## Updated Python Code:\n```python\n{new_code}\n```"
                        
                        # Update the record
                        self.data[index]['completion'] = new_completion
                        
                        print(f"\n✅ Code successfully updated for record #{index}")
                        
                        # Ask if user wants to save
                        save_now = input("Save changes to file now? (y/n): ").strip().lower()
                        if save_now == 'y':
                            self.save_data()
                    else:
                        print("❌ No code provided, skipping substitution.")
                
                # Ask if user wants to continue
                continue_editing = input("\nContinue with another record? (y/n): ").strip().lower()
                if continue_editing != 'y':
                    break
                    
            except ValueError:
                print("❌ Please enter a valid integer index.")
            except KeyboardInterrupt:
                print("\n\nOperation cancelled by user.")
                break
            except Exception as e:
                print(f"❌ An error occurred: {e}")
        
        # Final save option
        save_final = input("\nSave all changes before exiting? (y/n): ").strip().lower()
        if save_final == 'y':
            self.save_data()
    
    def substitute_code_by_index(self, index: int, new_code: str) -> bool:
        """
        Programmatically substitute code for a specific index
        
        Args:
            index: The index of the record to modify
            new_code: The new code to substitute
            
        Returns:
            True if successful, False otherwise
        """
        record = self.get_record_by_index(index)
        if record is None:
            return False
        
        try:
            original_completion = record['completion']
            
            # Find and replace the code block
            import re
            
            # Pattern to find Python code blocks
            pattern = r'(```python\n)(.*?)(\n```)'
            
            def replace_code(match):
                return f"{match.group(1)}{new_code}{match.group(3)}"
            
            new_completion = re.sub(pattern, replace_code, original_completion, flags=re.DOTALL)
            
            # If no code block was found, append the new code
            if new_completion == original_completion:
                new_completion += f"\n\n## Updated Python Code:\n```python\n{new_code}\n```"
            
            # Update the record
            self.data[index]['completion'] = new_completion
            
            print(f"✅ Code successfully updated for record #{index}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating record #{index}: {e}")
            return False


def main():
    """
    Main function to run the interactive tool
    """
    import sys
    
    # Default file path
    default_file = "/Users/jiawei/Downloads/Project/Data/OR-Instruct-Data-3K-Gurobipy.jsonl"
    
    if len(sys.argv) > 1:
        jsonl_file = sys.argv[1]
    else:
        jsonl_file = default_file
    
    try:
        tool = CodeSubstitutionTool(jsonl_file)
        tool.substitute_code_interactive()
        
    except Exception as e:
        print(f"Failed to initialize tool: {e}")


if __name__ == "__main__":
    main()
