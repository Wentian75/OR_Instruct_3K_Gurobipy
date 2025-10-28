# Quick Start Guide - Using the Converted Gurobipy Dataset

## ✅ Conversion Complete!

Your OR-Instruct dataset has been successfully converted from COPTPY to Gurobipy.

## 📁 Key Files

### Dataset Files
- **`OR-Instruct-Data-3K-Gurobipy.jsonl`** ← **USE THIS for fine-tuning!**
- `OR-Instruct-Data-3K.jsonl` (original COPTPY version, kept for reference)

### Documentation
- `CONVERSION_SUMMARY.md` - Detailed conversion report
- `sample_comparison.txt` - Before/after example
- `conversion_validation_report.txt` - Quality metrics

### Scripts (for future use)
- `coptpy_to_gurobipy_converter.py` - Main conversion tool
- `validate_conversion.py` - Quality check tool
- `test_conversion.py` - Sample testing tool

## 🚀 Quick Usage Examples

### 1. Load and Inspect the Dataset

```python
import json

# Load the converted dataset
with open('OR-Instruct-Data-3K-Gurobipy.jsonl', 'r') as f:
    dataset = [json.loads(line) for line in f]

print(f"Total entries: {len(dataset)}")

# View first entry
entry = dataset[0]
print("\nPROMPT:")
print(entry['prompt'][:200], "...")
print("\nCOMPLETION:")
print(entry['completion'][:500], "...")
```

### 2. Extract Code Examples

```python
import json
import re

# Extract Gurobipy code from entries
def extract_code(entry):
    completion = entry['completion']
    match = re.search(r'```python\n(.*?)\n```', completion, re.DOTALL)
    return match.group(1) if match else None

with open('OR-Instruct-Data-3K-Gurobipy.jsonl', 'r') as f:
    for i, line in enumerate(f):
        if i >= 5:  # First 5 examples
            break
        entry = json.loads(line)
        code = extract_code(entry)
        print(f"\n=== Example {i+1} ===")
        print(code[:300], "...")
```

### 3. Prepare for Fine-tuning

```python
import json
from sklearn.model_selection import train_test_split

# Load dataset
with open('OR-Instruct-Data-3K-Gurobipy.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

# Split into train/validation/test (80/10/10)
train_data, temp = train_test_split(data, test_size=0.2, random_state=42)
val_data, test_data = train_test_split(temp, test_size=0.5, random_state=42)

print(f"Training set: {len(train_data)} entries")
print(f"Validation set: {len(val_data)} entries")
print(f"Test set: {len(test_data)} entries")

# Save splits
with open('train.jsonl', 'w') as f:
    for entry in train_data:
        f.write(json.dumps(entry) + '\n')

with open('val.jsonl', 'w') as f:
    for entry in val_data:
        f.write(json.dumps(entry) + '\n')

with open('test.jsonl', 'w') as f:
    for entry in test_data:
        f.write(json.dumps(entry) + '\n')

print("\n✓ Dataset split into train/val/test!")
```

### 4. Format for Qwen3:8b Fine-tuning

Depending on your training framework, you may need to format the data:

```python
import json

# Example: Format for standard fine-tuning
def format_for_training(entry):
    return {
        "instruction": entry['prompt'],
        "output": entry['completion']
    }

# Or for chat format
def format_for_chat(entry):
    return {
        "messages": [
            {"role": "user", "content": entry['prompt']},
            {"role": "assistant", "content": entry['completion']}
        ]
    }

# Load and format
with open('OR-Instruct-Data-3K-Gurobipy.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

formatted_data = [format_for_training(entry) for entry in data]

# Save formatted data
with open('formatted_for_qwen.jsonl', 'w') as f:
    for entry in formatted_data:
        f.write(json.dumps(entry) + '\n')

print("✓ Formatted dataset ready for training!")
```

## 🔍 Verify Conversion Quality

### Run Validation
```bash
python validate_conversion.py
```

This will show:
- Conversion statistics
- Quality metrics
- Random sample inspection
- Any issues found

### View Sample Comparison
```bash
cat sample_comparison.txt
```

Shows before/after comparison of an actual entry.

## 📊 Conversion Statistics Summary

```
Total Entries: 3,000
Success Rate: 100%

API Conversions:
✓ Imports: 100%
✓ Constants: 100%
✓ Methods: 100%
✓ Text references: 92.2%

Preservation:
✓ Mathematical models: 100%
✓ Problem descriptions: 100%
```

## 🎯 Next Steps for Fine-tuning

1. **Choose your split** (if needed):
   ```bash
   python -c "
   import json
   from sklearn.model_selection import train_test_split

   with open('OR-Instruct-Data-3K-Gurobipy.jsonl', 'r') as f:
       data = [json.loads(line) for line in f]

   train, temp = train_test_split(data, test_size=0.2, random_state=42)
   val, test = train_test_split(temp, test_size=0.5, random_state=42)

   for split, name in [(train, 'train'), (val, 'val'), (test, 'test')]:
       with open(f'{name}.jsonl', 'w') as f:
           for entry in split:
               f.write(json.dumps(entry) + '\n')

   print('✓ Created train.jsonl, val.jsonl, test.jsonl')
   "
   ```

2. **Configure Qwen3:8b fine-tuning** with your preferred framework:
   - Hugging Face Transformers
   - LLaMA Factory
   - Ollama
   - Or your custom training pipeline

3. **Start training** with the Gurobipy dataset!

4. **Evaluate** if the model generates valid Gurobipy code

## 💡 Tips

- **Dataset Quality**: 92.2% of entries are completely clean of COPTPY references
- **Remaining References**: The 7.8% with residual 'coptpy' mentions are in explanatory text and don't affect code functionality
- **Mathematical Models**: All preserved perfectly (100%)
- **File Size**: Nearly identical to original (17.43 MB vs 17.42 MB)

## ❓ Troubleshooting

### If you need to re-run conversion:
```bash
python coptpy_to_gurobipy_converter.py
```

### If you want to test specific samples:
```bash
python test_conversion.py
```

### To check a specific entry:
```python
import json

entry_num = 42  # Change this

with open('OR-Instruct-Data-3K-Gurobipy.jsonl', 'r') as f:
    for i, line in enumerate(f):
        if i == entry_num:
            entry = json.loads(line)
            print(entry['completion'])
            break
```

## 📚 Additional Resources

- `CONVERSION_SUMMARY.md` - Comprehensive conversion report
- `CLAUDE.md` - Original dataset documentation
- Gurobipy documentation: https://www.gurobi.com/documentation/

---

**You're all set! The dataset is ready for fine-tuning Qwen3:8b to generate Gurobipy optimization code! 🎉**
