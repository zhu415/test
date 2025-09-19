import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re

def parse_info_xml(info_xml_path):
    """
    Parse info.xml and extract GrowthSpread data.
    Returns a dictionary with StringA as key and gspt data as value.
    """
    tree = ET.parse(info_xml_path)
    root = tree.getroot()
    
    growth_spread_data = {}
    
    # Find all GrowthSpread sections
    for growth_spread in root.findall('.//GrowthSpread'):
        underlier_elem = growth_spread.find('UnderlierID')
        if underlier_elem is not None:
            underlier_id = underlier_elem.text
            # Extract StringA from pattern StringA_StringB.StringC
            if underlier_id:
                match = re.match(r'^([^_]+)_', underlier_id)
                if match:
                    string_a = match.group(1)
                    
                    # Extract gspt data
                    gspt_list = []
                    growth_spread_points = growth_spread.find('GrowthSpreadPoints')
                    if growth_spread_points is not None:
                        for gspt in growth_spread_points.findall('gspt'):
                            tex = gspt.get('Tex', '')
                            text_type = gspt.get('type', '')
                            val = gspt.get('Val', '')
                            
                            if tex and text_type and val:
                                # Create Tenor value: Tex + lowercase of text type
                                tenor = tex + text_type.lower()
                                gspt_list.append({
                                    'tenor': tenor,
                                    'value': val
                                })
                    
                    growth_spread_data[string_a] = gspt_list
    
    return growth_spread_data

def get_string_a_from_symbol(md_symbol):
    """
    Extract StringA from MdSymbol pattern StringA_StringB.StringC
    """
    if md_symbol:
        match = re.match(r'^([^_]+)_', md_symbol)
        if match:
            return match.group(1)
    return None

def modify_xml_file(xml_path, growth_spread_data):
    """
    Modify a single XML file based on growth spread data.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Find MdSymbol to determine which GrowthSpread data to use
        md_symbol_elem = root.find('.//MdSymbol')
        if md_symbol_elem is None:
            return False
        
        md_symbol = md_symbol_elem.text
        string_a = get_string_a_from_symbol(md_symbol)
        
        if not string_a or string_a not in growth_spread_data:
            return False
        
        # Get the corresponding gspt data
        gspt_data = growth_spread_data[string_a]
        
        # Find BorrowShiftTermStructure section
        borrow_section = root.find('.//BorrowShiftTermStructure')
        if borrow_section is None:
            return False
        
        # Remove existing Tenor and Value tags
        for child in list(borrow_section):
            if child.tag in ['Tenor', 'Value']:
                borrow_section.remove(child)
        
        # Add new Tenor and Value tags based on gspt data
        for gspt_item in gspt_data:
            # Create and add Tenor element
            tenor_elem = ET.SubElement(borrow_section, 'Tenor')
            tenor_elem.text = gspt_item['tenor']
            
            # Create and add Value element
            value_elem = ET.SubElement(borrow_section, 'Value')
            value_elem.text = gspt_item['value']
        
        # Save the modified XML with proper formatting
        save_xml_with_formatting(tree, xml_path)
        return True
        
    except Exception as e:
        print(f"Error modifying {xml_path}: {str(e)}")
        return False

def save_xml_with_formatting(tree, output_path):
    """
    Save XML with proper indentation and formatting.
    """
    # Convert to string and parse with minidom for pretty printing
    xml_str = ET.tostring(tree.getroot(), encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    # Remove extra blank lines
    lines = pretty_xml.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    pretty_xml = '\n'.join(non_empty_lines)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)

def process_directory(directory_path, info_xml_path, output_directory=None):
    """
    Process all XML files in the directory.
    
    Args:
        directory_path: Path to directory containing XMLs to modify
        info_xml_path: Path to info.xml file
        output_directory: Optional output directory. If None, overwrites original files
    """
    # Parse info.xml to get growth spread data
    growth_spread_data = parse_info_xml(info_xml_path)
    
    if not growth_spread_data:
        print("No GrowthSpread data found in info.xml")
        return
    
    print(f"Found GrowthSpread data for: {list(growth_spread_data.keys())}")
    
    # Create output directory if specified and doesn't exist
    if output_directory and not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    # Process each XML file in the directory
    modified_count = 0
    for filename in os.listdir(directory_path):
        if filename.endswith('.xml') and filename != 'info.xml':
            input_path = os.path.join(directory_path, filename)
            
            # Determine output path
            if output_directory:
                output_path = os.path.join(output_directory, filename)
                # Copy and modify
                tree = ET.parse(input_path)
                tree.write(output_path)
                success = modify_xml_file(output_path, growth_spread_data)
            else:
                # Modify in place
                success = modify_xml_file(input_path, growth_spread_data)
            
            if success:
                modified_count += 1
                print(f"Modified: {filename}")
            else:
                print(f"Skipped: {filename} (no matching data or required elements)")
    
    print(f"\nTotal files modified: {modified_count}")

def main():
    # Configuration
    xml_directory = "/path/to/xml/directory"  # Directory containing XMLs to modify
    info_xml_path = "/path/to/info.xml"       # Path to info.xml
    output_directory = "/path/to/output"      # Optional: set to None to modify in place
    
    # Process the directory
    process_directory(xml_directory, info_xml_path, output_directory)

if __name__ == "__main__":
    main()
