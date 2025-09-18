import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re

def parse_information_xml(info_xml_path):
    """
    Parse the information XML and extract GrowthSpread data.
    Returns a dictionary with underlierID patterns as keys.
    """
    tree = ET.parse(info_xml_path)
    root = tree.getroot()
    
    growth_spread_data = {}
    
    # Find all GrowthSpread sections
    for growth_spread in root.findall('.//GrowthSpread'):
        underlier_id_elem = growth_spread.find('UnderlierID')
        if underlier_id_elem is not None:
            underlier_id = underlier_id_elem.text
            
            # Extract the "someString" part from pattern "someString_otherString.anotherString"
            match = re.match(r'^([^_]+)_.*', underlier_id)
            if match:
                key_part = match.group(1)
                
                # Parse GrowthSpreadPoints
                points_elem = growth_spread.find('GrowthSpreadPoints')
                if points_elem is not None and points_elem.text:
                    points_data = parse_growth_spread_points(points_elem.text)
                    growth_spread_data[key_part] = points_data
    
    return growth_spread_data

def parse_growth_spread_points(points_text):
    """
    Parse the GrowthSpreadPoints text to extract Tex and Val values.
    Returns a list of tuples (tenor, value).
    """
    points = []
    lines = points_text.strip().split('\n')
    
    for line in lines:
        # Parse pattern: <gspt dateType="F" Tex="intValue" text type="singleCharacter" Val="decimalValue" ...>
        # Using regex to extract Tex and Val values
        tex_match = re.search(r'Tex="(\d+)"', line)
        type_match = re.search(r'type="(\w)"', line)
        val_match = re.search(r'Val="([\d.-]+)"', line)
        
        if tex_match and type_match and val_match:
            tex_value = tex_match.group(1)
            type_char = type_match.group(1).lower()
            val_value = val_match.group(1)
            
            # Tenor is Tex value + lowercase type character
            tenor = tex_value + type_char
            points.append((tenor, val_value))
    
    return points

def modify_xml_file(xml_path, growth_spread_data):
    """
    Modify a single XML file based on growth spread data.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Find MdSymbol to determine which data to use
    md_symbol_elem = root.find('.//MdSymbol')
    if md_symbol_elem is None:
        print(f"Warning: No MdSymbol found in {xml_path}")
        return False
    
    md_symbol = md_symbol_elem.text
    
    # Extract the matching part from MdSymbol
    match = re.match(r'^([^_]+)_.*', md_symbol)
    if not match:
        print(f"Warning: MdSymbol '{md_symbol}' doesn't match expected pattern")
        return False
    
    key_part = match.group(1)
    
    # Check if we have data for this symbol
    if key_part not in growth_spread_data:
        print(f"Warning: No growth spread data found for '{key_part}'")
        return False
    
    points_data = growth_spread_data[key_part]
    
    # Find BorrowShiftTermStructure section
    borrow_section = root.find('.//BorrowShiftTermStructure')
    if borrow_section is None:
        print(f"Warning: No BorrowShiftTermStructure section found in {xml_path}")
        return False
    
    # Remove existing Tenor and Value elements
    for elem in list(borrow_section):
        if elem.tag in ['Tenor', 'Value']:
            borrow_section.remove(elem)
    
    # Add new Tenor and Value elements based on growth spread points
    for tenor, value in points_data:
        tenor_elem = ET.SubElement(borrow_section, 'Tenor')
        tenor_elem.text = tenor
        
        value_elem = ET.SubElement(borrow_section, 'Value')
        value_elem.text = value
    
    # Save the modified XML with proper formatting
    save_formatted_xml(tree, xml_path)
    return True

def save_formatted_xml(tree, filepath):
    """
    Save XML with proper formatting and indentation.
    """
    # Convert to string and parse with minidom for pretty printing
    xml_str = ET.tostring(tree.getroot(), encoding='unicode')
    dom = minidom.parseString(xml_str)
    
    # Write formatted XML
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(dom.toprettyxml(indent="  "))

def process_all_xmls(info_xml_filename='information.xml'):
    """
    Main function to process all XML files in the current directory.
    """
    current_dir = os.getcwd()
    
    # Check if information XML exists
    info_xml_path = os.path.join(current_dir, info_xml_filename)
    if not os.path.exists(info_xml_path):
        print(f"Error: Information XML '{info_xml_filename}' not found in current directory")
        return
    
    # Parse information XML
    print(f"Parsing information XML: {info_xml_filename}")
    growth_spread_data = parse_information_xml(info_xml_path)
    print(f"Found growth spread data for: {list(growth_spread_data.keys())}")
    
    # Process all XML files except the information XML
    modified_count = 0
    for filename in os.listdir(current_dir):
        if filename.endswith('.xml') and filename != info_xml_filename:
            xml_path = os.path.join(current_dir, filename)
            print(f"\nProcessing: {filename}")
            
            if modify_xml_file(xml_path, growth_spread_data):
                print(f"✓ Successfully modified: {filename}")
                modified_count += 1
            else:
                print(f"✗ Could not modify: {filename}")
    
    print(f"\n{'='*50}")
    print(f"Processing complete. Modified {modified_count} XML file(s)")

if __name__ == "__main__":
    # You can specify a different information XML filename if needed
    process_all_xmls('information.xml')
    
    # Alternative: process with a specific information XML
    # process_all_xmls('my_info
