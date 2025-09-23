import xml.etree.ElementTree as ET
import os
import re

def duplicate_tenor_values(file_path, xml_file_name, data_frequency):
    """
    Duplicates Tenor and Value tags in an XML file based on data frequency.
    
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
    
    # Find existing Tenor and Value elements
    tenor_elem = borrow_shift.find('Tenor')
    value_elem = borrow_shift.find('Value')
    
    if tenor_elem is None or value_elem is None:
        raise ValueError("Tenor or Value element not found in BorrowShiftTermStructure")
    
    # Extract the current tenor value and parse it
    current_tenor = tenor_elem.text
    tenor_match = re.match(r'(\d+)([dmy])', current_tenor)
    if not tenor_match:
        raise ValueError(f"Invalid tenor format: {current_tenor}. Expected format: Nd, Nm, or Ny")
    
    tenor_value = int(tenor_match.group(1))
    tenor_unit = tenor_match.group(2)
    
    # Parse the frequency
    freq_match = re.match(r'(\d+)([dm])', data_frequency)
    if not freq_match:
        raise ValueError(f"Invalid frequency format: {data_frequency}. Expected format: Nd or Nm")
    
    freq_value = int(freq_match.group(1))
    freq_unit = freq_match.group(2)
    
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
    
    # Convert frequency to days
    def convert_freq_to_days(value, unit):
        if unit == 'd':
            return value
        elif unit == 'm':
            return value * 30  # Approximate days in a month
        else:
            raise ValueError(f"Unsupported frequency unit: {unit}")
    
    total_days = convert_to_days(tenor_value, tenor_unit)
    freq_days = convert_freq_to_days(freq_value, freq_unit)
    
    # Calculate number of duplications
    num_duplications = total_days // freq_days
    
    # Get the value to duplicate
    current_value = value_elem.text
    
    # Find the position to insert new elements (after existing Tenor)
    tenor_index = list(borrow_shift).index(tenor_elem)
    value_index = list(borrow_shift).index(value_elem)
    
    # Remove existing Tenor and Value elements
    borrow_shift.remove(tenor_elem)
    borrow_shift.remove(value_elem)
    
    # Create new Tenor and Value elements
    new_tenors = []
    new_values = []
    
    for i in range(1, num_duplications):
        # Create new tenor value based on frequency unit
        if freq_unit == 'd':
            new_tenor_text = f"{i * freq_value}d"
        elif freq_unit == 'm':
            new_tenor_text = f"{i * freq_value}m"
        
        # Create new Tenor element
        new_tenor = ET.Element('Tenor')
        new_tenor.text = new_tenor_text
        new_tenors.append(new_tenor)
        
        # Create new Value element
        new_value = ET.Element('Value')
        new_value.text = current_value
        new_values.append(new_value)
    
    # Add the original tenor at the end
    original_tenor = ET.Element('Tenor')
    original_tenor.text = current_tenor
    new_tenors.append(original_tenor)
    
    original_value = ET.Element('Value')
    original_value.text = current_value
    new_values.append(original_value)
    
    # Insert all new Tenor elements first (in sorted order)
    insert_position = tenor_index
    for tenor in new_tenors:
        borrow_shift.insert(insert_position, tenor)
        insert_position += 1
    
    # Then insert all Value elements
    for value in new_values:
        borrow_shift.insert(insert_position, value)
        insert_position += 1
    
    # Create output filename
    name_without_ext = os.path.splitext(xml_file_name)[0]
    output_filename = f"{name_without_ext}_modified.xml"
    output_path = os.path.join(file_path, output_filename)
    
    # Write the modified XML to a new file
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    return output_path

# Example usage:
if __name__ == "__main__":
    # Example scenarios:
    
    # Scenario 1: 3-year tenor with daily frequency
    # duplicate_tenor_values("/path/to/xml", "input.xml", "1d")
    # Input: Tenor="3y", frequency="1d" → Creates ~1095 daily tenors (1d, 2d, ..., 1095d)
    
    # Scenario 2: 3-year tenor with monthly frequency  
    # duplicate_tenor_values("/path/to/xml", "input.xml", "1m")
    # Input: Tenor="3y", frequency="1m" → Creates ~36 monthly tenors (1m, 2m, ..., 36m)
    
    # Scenario 3: 24-month tenor with daily frequency
    # duplicate_tenor_values("/path/to/xml", "input.xml", "1d") 
    # Input: Tenor="24m", frequency="1d" → Creates ~720 daily tenors (1d, 2d, ..., 720d)
    
    # Scenario 4: 1000-day tenor with monthly frequency
    # duplicate_tenor_values("/path/to/xml", "input.xml", "1m")
    # Input: Tenor="1000d", frequency="1m" → Creates ~33 monthly tenors (1m, 2m, ..., 33m)
    
    file_path = "."  # Current directory
    xml_file = "example.xml"
    frequency = "1d"  # Daily frequency
    
    try:
        output_file = duplicate_tenor_values(file_path, xml_file, frequency)
        print(f"Modified XML saved to: {output_file}")
        print(f"Processing completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
