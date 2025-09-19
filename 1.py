import os
import xml.etree.ElementTree as ET
import re
from pathlib import Path

def parse_info_file(info_path):
    """
    Parse info.txt to extract GrowthSpread sections and their data.
    Returns a dictionary mapping UnderlierID to growth spread points.
    """
    growth_spreads = {}
    
    with open(info_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Find all GrowthSpread sections
    growth_spread_pattern = r'<GrowthSpread>(.*?)</GrowthSpread>'
    growth_spread_sections = re.findall(growth_spread_pattern, content, re.DOTALL)
    
    for section in growth_spread_sections:
        # Extract UnderlierID
        underlier_match = re.search(r'<UnderlierID>(.*?)</UnderlierID>', section)
        if not underlier_match:
            continue
        
        underlier_id = underlier_match.group(1).strip()
        
        # Extract GrowthSpreadPoints
        points_match = re.search(r'<GrowthSpreadPoints>(.*?)</GrowthSpreadPoints>', 
                                section, re.DOTALL)
        if not points_match:
            continue
        
        points_content = points_match.group(1)
        
        # Parse individual gspt lines
        gspt_pattern = r'<gspt[^>]*\s+Tex="(\d+)"[^>]*\s+text\s+type="(\w)"[^>]*\s+Val="([^"]+)"[^>]*/?>'
        gspt_matches = re.findall(gspt_pattern, points_content)
        
        growth_points = []
        for tex_val, text_type, val in gspt_matches:
            tenor = f"{tex_val}{text_type.lower()}"
            growth_points.append({
                'tenor': tenor,
                'value': val
            })
        
        growth_spreads[underlier_id] = growth_points
    
    return growth_spreads

def get_md_symbol(xml_tree):
    """Extract MdSymbol value from XML tree."""
    md_symbol_elem = xml_tree.find('.//MdSymbol')
    if md_symbol_elem is not None and md_symbol_elem.text:
        return md_symbol_elem.text.strip()
    return None

def update_borrow_shift_structure(xml_tree, growth_points):
    """
    Update BorrowShiftTermStructure section with new Tenor and Value pairs.
    """
    # Find BorrowShiftTermStructure element
    borrow_shift_elem = xml_tree.find('.//BorrowShiftTermStructure')
    
    if borrow_shift_elem is None:
        print("Warning: BorrowShiftTermStructure section not found")
        return False
    
    # Remove existing Tenor and Value elements
    tenors_to_remove = borrow_shift_elem.findall('Tenor')
    values_to_remove = borrow_shift_elem.findall('Value')
    
    for elem in tenors_to_remove + values_to_remove:
        borrow_shift_elem.remove(elem)
    
    # Add new Tenor and Value pairs
    for point in growth_points:
        # Create and add Tenor element
        tenor_elem = ET.Element('Tenor')
        tenor_elem.text = point['tenor']
        borrow_shift_elem.append(tenor_elem)
        
        # Create and add Value element
        value_elem = ET.Element('Value')
        value_elem.text = point['value']
        borrow_shift_elem.append(value_elem)
    
    return True

def process_xml_files(xml_directory, info_path, output_directory=None):
    """
    Process all XML files in the directory based on info.txt.
    """
    # If no output directory specified, use the same as input
    if output_directory is None:
        output_directory = xml_directory
    
    # Create output directory if it doesn't exist
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    
    # Parse info.txt
    print(f"Parsing info file: {info_path}")
    growth_spreads = parse_info_file(info_path)
    print(f"Found {len(growth_spreads)} GrowthSpread sections")
    
    # Process each XML file
    xml_files = [f for f in os.listdir(xml_directory) 
                 if f.lower().endswith('.xml')]
    
    print(f"Found {len(xml_files)} XML files to process")
    
    modified_count = 0
    for xml_file in xml_files:
        xml_path = os.path.join(xml_directory, xml_file)
        print(f"\nProcessing: {xml_file}")
        
        try:
            # Parse XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Get MdSymbol
            md_symbol = get_md_symbol(root)
            if not md_symbol:
                print(f"  Warning: No MdSymbol found in {xml_file}")
                continue
            
            print(f"  MdSymbol: {md_symbol}")
            
            # Check if we have matching growth spread data
            if md_symbol not in growth_spreads:
                print(f"  No matching UnderlierID found for {md_symbol}")
                continue
            
            # Update BorrowShiftTermStructure
            growth_points = growth_spreads[md_symbol]
            print(f"  Found {len(growth_points)} growth points to update")
            
            if update_borrow_shift_structure(root, growth_points):
                # Save modified XML
                output_path = os.path.join(output_directory, xml_file)
                tree.write(output_path, encoding='utf-8', xml_declaration=True)
                print(f"  Successfully modified and saved to: {output_path}")
                modified_count += 1
            else:
                print(f"  Failed to update BorrowShiftTermStructure")
                
        except ET.ParseError as e:
            print(f"  Error parsing XML: {e}")
        except Exception as e:
            print(f"  Unexpected error: {e}")
    
    print(f"\n{'='*50}")
    print(f"Processing complete!")
    print(f"Modified {modified_count} out of {len(xml_files)} XML files")
    print(f"Output directory: {output_directory}")

def main():
    # Configuration - Update these paths as needed
    XML_DIRECTORY = "path/to/xml/directory"  # Directory containing XMLs to modify
    INFO_FILE_PATH = "path/to/info.txt"      # Path to info.txt file
    OUTPUT_DIRECTORY = "path/to/output"      # Optional: specify different output directory
    
    # Run the processing
    process_xml_files(
        xml_directory=XML_DIRECTORY,
        info_path=INFO_FILE_PATH,
        output_directory=OUTPUT_DIRECTORY  # Use None to save in same directory
    )

if __name__ == "__main__":
    main()


gspt_pattern = r'<gspt[^>]*\s+tex="(\d+)"[^>]*\s+texType="(\w+)"[^>]*\s+val="([^"]+)"[^>]*/>'


def update_borrow_shift_structure(xml_tree, growth_points):
    """
    Update BorrowShiftTermStructure section with new Tenor and Value pairs.
    All Tenor tags come first, followed by all Value tags.
    """
    # Find BorrowShiftTermStructure element
    borrow_shift_elem = xml_tree.find('.//BorrowShiftTermStructure')
    
    if borrow_shift_elem is None:
        print("Warning: BorrowShiftTermStructure section not found")
        return False
    
    # Remove existing Tenor and Value elements
    tenors_to_remove = borrow_shift_elem.findall('Tenor')
    values_to_remove = borrow_shift_elem.findall('Value')
    
    for elem in tenors_to_remove + values_to_remove:
        borrow_shift_elem.remove(elem)
    
    # First, add all Tenor elements
    for point in growth_points:
        tenor_elem = ET.Element('Tenor')
        tenor_elem.text = point['tenor']
        borrow_shift_elem.append(tenor_elem)
    
    # Then, add all Value elements
    for point in growth_points:
        value_elem = ET.Element('Value')
        value_elem.text = point['value']
        borrow_shift_elem.append(value_elem)
    
    return True
