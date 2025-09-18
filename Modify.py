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



import os
import sys
import argparse
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

def modify_xml_file(xml_path, growth_spread_data, output_dir=None):
    """
    Modify a single XML file based on growth spread data.
    If output_dir is provided, save to that directory instead of overwriting.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Find MdSymbol to determine which data to use
        md_symbol_elem = root.find('.//MdSymbol')
        if md_symbol_elem is None:
            print(f"  ⚠ Warning: No MdSymbol found in {os.path.basename(xml_path)}")
            return False
        
        md_symbol = md_symbol_elem.text
        
        # Extract the matching part from MdSymbol
        match = re.match(r'^([^_]+)_.*', md_symbol)
        if not match:
            print(f"  ⚠ Warning: MdSymbol '{md_symbol}' doesn't match expected pattern")
            return False
        
        key_part = match.group(1)
        
        # Check if we have data for this symbol
        if key_part not in growth_spread_data:
            print(f"  ⚠ Warning: No growth spread data found for '{key_part}'")
            return False
        
        points_data = growth_spread_data[key_part]
        
        # Find BorrowShiftTermStructure section
        borrow_section = root.find('.//BorrowShiftTermStructure')
        if borrow_section is None:
            print(f"  ⚠ Warning: No BorrowShiftTermStructure section found")
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
        
        # Determine output path
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, os.path.basename(xml_path))
        else:
            output_path = xml_path
        
        # Save the modified XML with proper formatting
        save_formatted_xml(tree, output_path)
        print(f"  ✓ Modified with {len(points_data)} data points")
        return True
        
    except ET.ParseError as e:
        print(f"  ✗ XML parsing error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return False

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

def process_all_xmls(target_dir, info_xml_path, output_dir=None):
    """
    Main function to process all XML files in the target directory.
    
    Args:
        target_dir: Directory containing XML files to be modified
        info_xml_path: Path to the information XML file
        output_dir: Optional output directory for modified files (if None, overwrites originals)
    """
    # Validate inputs
    if not os.path.exists(target_dir):
        print(f"Error: Target directory '{target_dir}' does not exist")
        return 1
    
    if not os.path.isdir(target_dir):
        print(f"Error: '{target_dir}' is not a directory")
        return 1
    
    if not os.path.exists(info_xml_path):
        print(f"Error: Information XML file '{info_xml_path}' does not exist")
        return 1
    
    # Parse information XML
    print(f"📖 Parsing information XML: {info_xml_path}")
    try:
        growth_spread_data = parse_information_xml(info_xml_path)
        if not growth_spread_data:
            print("Warning: No growth spread data found in information XML")
        else:
            print(f"✓ Found growth spread data for: {', '.join(growth_spread_data.keys())}")
    except ET.ParseError as e:
        print(f"Error: Failed to parse information XML: {e}")
        return 1
    except Exception as e:
        print(f"Error: Unexpected error parsing information XML: {e}")
        return 1
    
    print(f"\n📁 Processing XML files in: {target_dir}")
    if output_dir:
        print(f"📤 Output directory: {output_dir}")
    else:
        print("⚠ Warning: Original files will be overwritten")
    
    # Process all XML files in target directory
    xml_files = [f for f in os.listdir(target_dir) if f.endswith('.xml')]
    
    if not xml_files:
        print("No XML files found in target directory")
        return 1
    
    print(f"Found {len(xml_files)} XML file(s) to process\n")
    
    modified_count = 0
    failed_count = 0
    
    for filename in xml_files:
        xml_path = os.path.join(target_dir, filename)
        
        # Skip if this is the information XML file
        if os.path.abspath(xml_path) == os.path.abspath(info_xml_path):
            print(f"⏭ Skipping information XML: {filename}")
            continue
        
        print(f"Processing: {filename}")
        
        if modify_xml_file(xml_path, growth_spread_data, output_dir):
            modified_count += 1
        else:
            failed_count += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Processing complete:")
    print(f"   - Successfully modified: {modified_count} file(s)")
    print(f"   - Failed/skipped: {failed_count} file(s)")
    print(f"   - Total processed: {len(xml_files)} file(s)")
    
    return 0

def main():
    """
    Main entry point with command-line argument parsing.
    """
    parser = argparse.ArgumentParser(
        description='Modify XML files based on growth spread information from a master XML file.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Modify XMLs in place (overwrites originals)
  python %(prog)s /path/to/xmls /path/to/info.xml
  
  # Save modified XMLs to a different directory
  python %(prog)s /path/to/xmls /path/to/info.xml -o /path/to/output
  
  # Process XMLs in current directory with info.xml in parent directory
  python %(prog)s . ../information.xml
        """
    )
    
    parser.add_argument(
        'target_dir',
        help='Directory containing XML files to be modified'
    )
    
    parser.add_argument(
        'info_xml',
        help='Path to the information XML file'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_dir',
        help='Output directory for modified files (if not specified, overwrites originals)',
        default=None
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Convert paths to absolute paths for clarity
    target_dir = os.path.abspath(args.target_dir)
    info_xml_path = os.path.abspath(args.info_xml)
    output_dir = os.path.abspath(args.output_dir) if args.output_dir else None
    
    if args.verbose:
        print(f"Target directory: {target_dir}")
        print(f"Information XML: {info_xml_path}")
        if output_dir:
            print(f"Output directory: {output_dir}")
        print()
    
    # Process the XML files
    exit_code = process_all_xmls(target_dir, info_xml_path, output_dir)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

