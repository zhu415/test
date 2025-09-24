import xml.etree.ElementTree as ET
import os
import re
from typing import List, Tuple

def duplicate_tenor_values(file_path, xml_file_name, data_frequency):
“””
Duplicates Tenor and Value tags in an XML file based on data frequency.
Handles multiple Tenor-Value pairs with flat extrapolation before first tenor
and linear interpolation between tenor points.

```
Args:
    file_path (str): Path to the directory containing the XML file
    xml_file_name (str): Name of the XML file (with .xml extension)
    data_frequency (str): Frequency string (e.g., '1d' for daily, '1m' for monthly)

Supported Tenor formats:
    - 'Nd' for days (e.g., '30d', '365d')
    - 'Nm' for months (e.g., '12m', '24m')
    - 'Ny' for years (e.g., '1y', '3y', '10y')

Supported frequency formats:
    - 'Nd' for daily frequency (e.g., '1d')
    - 'Nm' for monthly frequency (e.g., '1m')

Returns:
    str: Path to the modified XML file
"""

# Construct full file path
full_path = os.path.join(file_path, xml_file_name)

# Parse the XML file
tree = ET.parse(full_path)
root = tree.getroot()

# Find the BorrowShiftTermStructure element
borrow_shift = root.find('BorrowShiftTermStructure')
if borrow_shift is None:
    raise ValueError("BorrowShiftTermStructure element not found in XML")

# Parse the frequency
freq_match = re.match(r'(\d+)([dm])', data_frequency)
if not freq_match:
    raise ValueError(f"Invalid frequency format: {data_frequency}. Expected format: Nd or Nm")

freq_value = int(freq_match.group(1))
freq_unit = freq_match.group(2)

# Convert frequency to days
def convert_freq_to_days(value, unit):
    if unit == 'd':
        return value
    elif unit == 'm':
        return value * 30  # Approximate days in a month
    else:
        raise ValueError(f"Unsupported frequency unit: {unit}")

freq_days = convert_freq_to_days(freq_value, freq_unit)

# Convert tenor to days for calculation
def convert_to_days(value, unit):
    if unit == 'd':
        return value
    elif unit == 'm':
        return value * 30  # Approximate days in a month
    elif unit == 'y':
        return value * 365  # Approximate days in a year
    else:
        raise ValueError(f"Unsupported unit: {unit}")

# Parse tenor string to get numeric value and unit
def parse_tenor(tenor_str):
    tenor_match = re.match(r'(\d+)([dmy])', tenor_str)
    if not tenor_match:
        raise ValueError(f"Invalid tenor format: {tenor_str}. Expected format: Nd, Nm, or Ny")
    return int(tenor_match.group(1)), tenor_match.group(2)

# Find all Tenor and Value elements
tenor_elements = []
value_elements = []

# Look for Tenor1, Tenor2, etc. and Value1, Value2, etc.
i = 1
while True:
    tenor_elem = borrow_shift.find(f'Tenor{i}')
    value_elem = borrow_shift.find(f'Value{i}')
    
    if tenor_elem is None or value_elem is None:
        break
        
    tenor_elements.append(tenor_elem)
    value_elements.append(value_elem)
    i += 1

# If no numbered elements found, try single Tenor/Value
if not tenor_elements:
    tenor_elem = borrow_shift.find('Tenor')
    value_elem = borrow_shift.find('Value')
    
    if tenor_elem is not None and value_elem is not None:
        tenor_elements.append(tenor_elem)
        value_elements.append(value_elem)

if not tenor_elements:
    raise ValueError("No Tenor/Value pairs found in BorrowShiftTermStructure")

# Parse tenor-value pairs and convert to days
tenor_value_pairs: List[Tuple[int, float]] = []

for tenor_elem, value_elem in zip(tenor_elements, value_elements):
    tenor_str = tenor_elem.text
    value_str = value_elem.text
    
    tenor_num, tenor_unit = parse_tenor(tenor_str)
    tenor_days = convert_to_days(tenor_num, tenor_unit)
    value_float = float(value_str)
    
    tenor_value_pairs.append((tenor_days, value_float))

# Sort pairs by tenor days
tenor_value_pairs.sort(key=lambda x: x[0])

# Generate new tenor-value pairs
new_tenor_values: List[Tuple[int, float]] = []

# 1. Flat extrapolation before first tenor
first_tenor_days = tenor_value_pairs[0][0]
first_value = tenor_value_pairs[0][1]

current_days = freq_days
while current_days < first_tenor_days:
    new_tenor_values.append((current_days, first_value))
    current_days += freq_days

# 2. Add the original tenor points
for tenor_days, value in tenor_value_pairs:
    new_tenor_values.append((tenor_days, value))

# 3. Linear interpolation between tenor points
interpolated_pairs = []

for i in range(len(tenor_value_pairs) - 1):
    start_days, start_value = tenor_value_pairs[i]
    end_days, end_value = tenor_value_pairs[i + 1]
    
    # Find interpolation points
    current_days = start_days + freq_days
    while current_days < end_days:
        # Linear interpolation
        ratio = (current_days - start_days) / (end_days - start_days)
        interpolated_value = start_value + ratio * (end_value - start_value)
        interpolated_pairs.append((current_days, interpolated_value))
        current_days += freq_days

# Insert interpolated pairs into the main list
all_pairs = []

# Add flat extrapolation points
for days, value in new_tenor_values:
    if days < first_tenor_days:
        all_pairs.append((days, value))

# Add original and interpolated points in sorted order
remaining_pairs = [(days, value) for days, value in new_tenor_values if days >= first_tenor_days]
all_pairs.extend(remaining_pairs)
all_pairs.extend(interpolated_pairs)

# Sort all pairs by tenor days
all_pairs.sort(key=lambda x: x[0])

# Remove original Tenor/Value elements
elements_to_remove = tenor_elements + value_elements
for elem in elements_to_remove:
    borrow_shift.remove(elem)

# Find insertion point (where the first tenor element was)
if tenor_elements:
    insertion_point = list(borrow_shift).index(tenor_elements[0]) if tenor_elements[0] in borrow_shift else len(borrow_shift)
else:
    insertion_point = len(borrow_shift)

# Create and insert new Tenor elements
tenor_insert_pos = insertion_point
for days, _ in all_pairs:
    new_tenor = ET.Element('Tenor')
    
    # Convert days back to appropriate format based on frequency unit
    if freq_unit == 'd':
        new_tenor.text = f"{days}d"
    elif freq_unit == 'm':
        # Convert back to months if frequency was monthly
        months = days // 30
        new_tenor.text = f"{months}m"
    
    borrow_shift.insert(tenor_insert_pos, new_tenor)
    tenor_insert_pos += 1

# Create and insert new Value elements
value_insert_pos = tenor_insert_pos
for _, value in all_pairs:
    new_value = ET.Element('Value')
    new_value.text = str(value)
    borrow_shift.insert(value_insert_pos, new_value)
    value_insert_pos += 1

# Create output filename
name_without_ext = os.path.splitext(xml_file_name)[0]
output_filename = f"{name_without_ext}_modified.xml"
output_path = os.path.join(file_path, output_filename)

# Write the modified XML to a new file
tree.write(output_path, encoding='utf-8', xml_declaration=True)

return output_path
```

# Example usage:

if **name** == “**main**”:
# Example scenarios with multiple tenor-value pairs:

```
# Scenario 1: XML with Tenor1="6m", Value1="0.02", Tenor2="1y", Value2="0.025", frequency="1m"
# Results in:
# - Flat extrapolation: 1m, 2m, 3m, 4m, 5m (all with value 0.02)
# - Original: 6m (0.02), 12m (0.025)
# - Linear interpolation: 7m, 8m, 9m, 10m, 11m (linearly interpolated between 0.02 and 0.025)

# Scenario 2: XML with Tenor1="30d", Value1="0.01", Tenor2="90d", Value2="0.015", frequency="1d"
# Results in:
# - Flat extrapolation: 1d, 2d, ..., 29d (all with value 0.01)
# - Original: 30d (0.01), 90d (0.015)
# - Linear interpolation: 31d, 32d, ..., 89d (linearly interpolated)

file_path = "."  # Current directory
xml_file = "example.xml"
frequency = "1m"  # Monthly frequency

try:
    output_file = duplicate_tenor_values(file_path, xml_file, frequency)
    print(f"Modified XML saved to: {output_file}")
    print(f"Processing completed successfully!")
    print("\nFeatures applied:")
    print("- Flat extrapolation before first tenor point")
    print("- Linear interpolation between tenor points")
    print("- No extrapolation after last tenor point")
except Exception as e:
    print(f"Error: {e}")
```
