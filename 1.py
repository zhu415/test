import os
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_info_xml(info_xml_path):
    """Parse info.xml and extract GrowthSpread data"""
    growth_spread_data = {}
    
    try:
        # First, try standard XML parsing
        tree = ET.parse(info_xml_path)
        root = tree.getroot()
        
        # Find all GrowthSpread sections
        for growth_spread in root.findall('.//GrowthSpread'):
            process_growth_spread(growth_spread, growth_spread_data)
            
    except ET.ParseError as e:
        print(f"Standard XML parsing failed: {e}")
        print("Attempting to fix malformed XML...")
        
        # Try to fix malformed XML
        try:
            with open(info_xml_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Method 1: Wrap content in a root element if multiple roots exist
            if content.count('<?xml') > 1:
                # Multiple XML declarations - remove extra ones
                parts = content.split('<?xml')
                content = '<?xml' + parts[1]  # Keep first XML declaration
                for part in parts[2:]:
                    # Remove XML declaration from subsequent parts
                    if '?>' in part:
                        content += part[part.index('?>') + 2:]
            
            # Check if we need a root wrapper
            lines = content.strip().split('\n')
            root_elements = []
            in_element = False
            current_element = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('<?xml') or line.startswith('<!--'):
                    continue
                if line.startswith('<') and not line.startswith('</'):
                    if not in_element and not line.endswith('/>'):
                        # This might be a root element
                        element_name = line.split()[0].replace('<', '').replace('>', '')
                        if not any(line.strip().startswith('</' + element_name) for line in lines[lines.index(line):]):
                            # Likely a root element without proper closing
                            root_elements.append(element_name)
            
            # If we have multiple potential root elements, wrap in a container
            if len(root_elements) > 1 or content.count('<GrowthSpread>') > 1:
                print("Detected multiple root elements, wrapping in container...")
                # Remove any existing root wrapper and create new one
                content = content.strip()
                if not content.startswith('<root>'):
                    content = '<root>\n' + content + '\n</root>'
            
            # Parse the fixed content
            root = ET.fromstring(content)
            
            # Find all GrowthSpread sections
            for growth_spread in root.findall('.//GrowthSpread'):
                process_growth_spread(growth_spread, growth_spread_data)
                
        except Exception as e2:
            print(f"Failed to fix malformed XML: {e2}")
            # Last resort: try to extract GrowthSpread sections manually
            try:
                print("Attempting manual extraction...")
                with open(info_xml_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Find all GrowthSpread sections using string manipulation
                import re
                growth_spread_pattern = r'<GrowthSpread>(.*?)</GrowthSpread>'
                matches = re.findall(growth_spread_pattern, content, re.DOTALL)
                
                for match in matches:
                    # Wrap each match in GrowthSpread tags and parse
                    growth_spread_xml = f'<GrowthSpread>{match}</GrowthSpread>'
                    try:
                        growth_spread_elem = ET.fromstring(growth_spread_xml)
                        process_growth_spread(growth_spread_elem, growth_spread_data)
                    except ET.ParseError:
                        print(f"Failed to parse individual GrowthSpread section")
                        continue
                        
            except Exception as e3:
                print(f"Manual extraction also failed: {e3}")
                raise e3
    
    return growth_spread_data

def process_growth_spread(growth_spread, growth_spread_data):
    """Process a single GrowthSpread element"""
    underlier_id_elem = growth_spread.find('UnderlierID')
    if underlier_id_elem is not None:
        underlier_id = underlier_id_elem.text.strip()
        
        # Extract GrowthSpreadPoints
        growth_spread_points = growth_spread.find('GrowthSpreadPoints')
        if growth_spread_points is not None:
            gspt_data = []
            for gspt in growth_spread_points.findall('gspt'):
                # Extract required attributes
                tex = gspt.get('Tex', '')
                text_type = gspt.get('type', '')
                val = gspt.get('Val', '')
                
                # Create tenor from Tex + lowercase of type
                tenor = tex + text_type.lower()
                
                gspt_data.append({
                    'tenor': tenor,
                    'value': val
                })
            
            growth_spread_data[underlier_id] = gspt_data

def modify_xml_file(xml_file_path, growth_spread_data):
    """Modify a single XML file based on growth spread data"""
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        # Find MdSymbol
        md_symbol_elem = root.find('.//MdSymbol')
        if md_symbol_elem is None:
            print(f"No MdSymbol found in {xml_file_path}")
            return False
        
        md_symbol = md_symbol_elem.text.strip()
        
        # Check if we have corresponding data
        if md_symbol not in growth_spread_data:
            print(f"No matching data found for MdSymbol: {md_symbol}")
            return False
        
        # Find BorrowShiftTermStructure section
        borrow_shift_elem = root.find('.//BorrowShiftTermStructure')
        if borrow_shift_elem is None:
            print(f"No BorrowShiftTermStructure found in {xml_file_path}")
            return False
        
        # Remove existing Tenor and Value elements
        for elem in borrow_shift_elem.findall('Tenor'):
            borrow_shift_elem.remove(elem)
        for elem in borrow_shift_elem.findall('Value'):
            borrow_shift_elem.remove(elem)
        
        # Add new Tenor and Value elements based on growth spread data
        gspt_data = growth_spread_data[md_symbol]
        
        for data_point in gspt_data:
            # Create Tenor element
            tenor_elem = ET.Element('Tenor')
            tenor_elem.text = data_point['tenor']
            borrow_shift_elem.append(tenor_elem)
            
            # Create Value element
            value_elem = ET.Element('Value')
            value_elem.text = data_point['value']
            borrow_shift_elem.append(value_elem)
        
        # Save the modified XML
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)
        print(f"Successfully modified: {xml_file_path}")
        return True
        
    except ET.ParseError as e:
        print(f"Error parsing {xml_file_path}: {e}")
        return False
    except Exception as e:
        print(f"Error processing {xml_file_path}: {e}")
        return False

def modify_xmls_in_directory(directory_path, info_xml_path):
    """Main function to modify all XMLs in directory based on info.xml"""
    
    # Parse info.xml
    print(f"Parsing info.xml from: {info_xml_path}")
    try:
        growth_spread_data = parse_info_xml(info_xml_path)
        print(f"Found data for {len(growth_spread_data)} UnderlierIDs")
    except Exception as e:
        print(f"Error parsing info.xml: {e}")
        return
    
    # Find all XML files in directory (excluding info.xml)
    directory = Path(directory_path)
    xml_files = [f for f in directory.glob('*.xml') if f.name != 'info.xml']
    
    if not xml_files:
        print(f"No XML files found in directory: {directory_path}")
        return
    
    print(f"Found {len(xml_files)} XML files to process")
    
    # Process each XML file
    modified_count = 0
    for xml_file in xml_files:
        print(f"\nProcessing: {xml_file.name}")
        if modify_xml_file(xml_file, growth_spread_data):
            modified_count += 1
    
    print(f"\n=== Summary ===")
    print(f"Total XML files processed: {len(xml_files)}")
    print(f"Successfully modified: {modified_count}")
    print(f"Failed to modify: {len(xml_files) - modified_count}")

# Example usage
if __name__ == "__main__":
    # Set your paths here
    directory_path = "/path/to/your/xml/directory"  # Directory containing XMLs to modify
    info_xml_path = "/path/to/info.xml"             # Path to info.xml
    
    # Alternatively, if info.xml is in the same directory as the XMLs to modify:
    # info_xml_path = os.path.join(directory_path, "info.xml")
    
    modify_xmls_in_directory(directory_path, info_xml_path)
