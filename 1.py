import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
from pathlib import Path

def parse_information_xml(info_xml_path):
    """
    Parse the information XML and extract GrowthSpread data.
    Handles multiple GrowthSpreadPoints sections within each GrowthSpread.
    """
    try:
        tree = ET.parse(info_xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"❌ Error parsing XML: {e}")
        # Try to parse with iterparse for problematic files
        return parse_information_xml_iterative(info_xml_path)
    
    growth_spread_data = {}
    
    # Find all GrowthSpread sections
    for growth_spread in root.findall('.//GrowthSpread'):
        underlier_id_elem = growth_spread.find('UnderlierID')
        if underlier_id_elem is not None and underlier_id_elem.text:
            underlier_id = underlier_id_elem.text
            
            # Extract the "someString" part from pattern "someString_otherString.anotherString"
            match = re.match(r'^([^_]+)_.*', underlier_id)
            if match:
                key_part = match.group(1)
                
                # Find ALL GrowthSpreadPoints sections within this GrowthSpread
                all_points = []
                for points_elem in growth_spread.findall('.//GrowthSpreadPoints'):
                    if points_elem.text:
                        points_data = parse_growth_spread_points(points_elem.text)
                        all_points.extend(points_data)  # Add all points from this section
                
                if all_points:
                    growth_spread_data[key_part] = all_points
                    print(f"   ✅ Found data for: {key_part} ({len(all_points)} total points)")
    
    return growth_spread_data

def parse_information_xml_iterative(info_xml_path):
    """
    Parse XML iteratively for problematic files.
    Handles multiple GrowthSpreadPoints sections.
    """
    growth_spread_data = {}
    current_growth_spread = None
    current_underlier_key = None
    current_points = []
    
    try:
        context = ET.iterparse(info_xml_path, events=('start', 'end'))
        context = iter(context)
        
        for event, elem in context:
            if event == 'start':
                if elem.tag == 'GrowthSpread':
                    # Starting a new GrowthSpread section
                    current_growth_spread = elem
                    current_points = []
                    current_underlier_key = None
                    
            elif event == 'end':
                if elem.tag == 'UnderlierID' and current_growth_spread is not None:
                    if elem.text:
                        underlier_id = elem.text
                        match = re.match(r'^([^_]+)_.*', underlier_id)
                        if match:
                            current_underlier_key = match.group(1)
                
                elif elem.tag == 'GrowthSpreadPoints' and current_growth_spread is not None:
                    # Found a GrowthSpreadPoints section
                    if elem.text:
                        points_data = parse_growth_spread_points(elem.text)
                        current_points.extend(points_data)
                
                elif elem.tag == 'GrowthSpread':
                    # Ending a GrowthSpread section - save the accumulated data
                    if current_underlier_key and current_points:
                        growth_spread_data[current_underlier_key] = current_points
                        print(f"   ✅ Found data for: {current_underlier_key} ({len(current_points)} total points)")
                    
                    # Reset for next GrowthSpread
                    current_growth_spread = None
                    current_underlier_key = None
                    current_points = []
                    
                    # Clear the element to save memory
                    elem.clear()
        
        print(f"📊 Total keys extracted: {len(growth_spread_data)}")
        return growth_spread_data
        
    except ET.ParseError as e:
        print(f"❌ Iterative parsing failed: {e}")
        return extract_growth_spread_manually(info_xml_path)

def extract_growth_spread_manually(info_xml_path):
    """
    Manual extraction using regex for badly formed XML.
    Handles multiple GrowthSpreadPoints sections.
    """
    print("🔧 Attempting manual extraction...")
    growth_spread_data = {}
    
    try:
        with open(info_xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all GrowthSpread sections
        growth_spread_pattern = r'<GrowthSpread>(.*?)</GrowthSpread>'
        growth_spreads = re.findall(growth_spread_pattern, content, re.DOTALL)
        
        for gs_content in growth_spreads:
            # Extract UnderlierID
            underlier_match = re.search(r'<UnderlierID>(.*?)</UnderlierID>', gs_content)
            if underlier_match:
                underlier_id = underlier_match.group(1)
                
                # Extract the key part
                key_match = re.match(r'^([^_]+)_.*', underlier_id)
                if key_match:
                    key_part = key_match.group(1)
                    
                    # Find ALL GrowthSpreadPoints sections
                    all_points = []
                    points_pattern = r'<GrowthSpreadPoints>(.*?)</GrowthSpreadPoints>'
                    all_points_sections = re.findall(points_pattern, gs_content, re.DOTALL)
                    
                    for points_text in all_points_sections:
                        points_data = parse_growth_spread_points(points_text)
                        all_points.extend(points_data)
                    
                    if all_points:
                        growth_spread_data[key_part] = all_points
                        print(f"   ✅ Manually extracted: {key_part} ({len(all_points)} total points)")
        
        print(f"📊 Manual extraction found: {len(growth_spread_data)} keys")
        return growth_spread_data
        
    except Exception as e:
        print(f"❌ Manual extraction failed: {e}")
        return {}

def parse_growth_spread_points(points_text):
    """
    Parse a single GrowthSpreadPoints text to extract Tex and Val values.
    Each line should have pattern like:
    <gspt dateType="F" Tex="intValue" type="singleCharacter" Val="decimalValue" ...>
    """
    if not points_text:
        return []
    
    points = []
    
    # Handle both newline-separated and continuous XML tags
    # First try to find individual gspt tags
    gspt_pattern = r'<gspt[^>]*?Tex="(\d+)"[^>]*?type="(\w)"[^>]*?Val="([\d.-]+)"[^>]*?>'
    matches = re.findall(gspt_pattern, points_text)
    
    if matches:
        for tex_value, type_char, val_value in matches:
            tenor = tex_value + type_char.lower()
            points.append((tenor, val_value))
    else:
        # Fallback to line-by-line parsing
        lines = points_text.strip().split('\n')
        for line in lines:
            if not line.strip():
                continue
                
            tex_match = re.search(r'Tex="(\d+)"', line)
            type_match = re.search(r'type="(\w)"', line)
            val_match = re.search(r'Val="([\d.-]+)"', line)
            
            if tex_match and type_match and val_match:
                tex_value = tex_match.group(1)
                type_char = type_match.group(1).lower()
                val_value = val_match.group(1)
                
                tenor = tex_value + type_char
                points.append((tenor, val_value))
    
    return points

def modify_xml_file(xml_path, growth_spread_data, output_dir=None):
    """
    Modify a single XML file based on growth spread data.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Find MdSymbol to determine which data to use
        md_symbol_elem = root.find('.//MdSymbol')
        if md_symbol_elem is None:
            return False, f"No MdSymbol found"
        
        md_symbol = md_symbol_elem.text
        if not md_symbol:
            return False, f"MdSymbol is empty"
        
        # Extract the matching part from MdSymbol
        match = re.match(r'^([^_]+)_.*', md_symbol)
        if not match:
            return False, f"MdSymbol '{md_symbol}' doesn't match expected pattern"
        
        key_part = match.group(1)
        
        # Check if we have data for this symbol
        if key_part not in growth_spread_data:
            return False, f"No growth spread data for '{key_part}'"
        
        points_data = growth_spread_data[key_part]
        
        # Find BorrowShiftTermStructure section
        borrow_section = root.find('.//BorrowShiftTermStructure')
        if borrow_section is None:
            return False, "No BorrowShiftTermStructure section found"
        
        # Remove ALL existing Tenor and Value elements
        tenors_removed = 0
        values_removed = 0
        for elem in list(borrow_section):
            if elem.tag == 'Tenor':
                borrow_section.remove(elem)
                tenors_removed += 1
            elif elem.tag == 'Value':
                borrow_section.remove(elem)
                values_removed += 1
        
        # Add new Tenor and Value elements from ALL GrowthSpreadPoints
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
        
        # Save the modified XML
        save_formatted_xml(tree, output_path)
        return True, f"Replaced {tenors_removed} old values with {len(points_data)} new points"
        
    except ET.ParseError as e:
        return False, f"XML parsing error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def save_formatted_xml(tree, filepath):
    """
    Save XML with proper formatting and indentation.
    """
    xml_str = ET.tostring(tree.getroot(), encoding='unicode')
    dom = minidom.parseString(xml_str)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(dom.toprettyxml(indent="  "))

def process_xml_files(target_dir, info_xml_path, output_dir=None, verbose=True):
    """
    Main function to process all XML files in the target directory.
    """
    results = {
        'success': [],
        'failed': [],
        'growth_spread_keys': [],
        'total_processed': 0,
        'details': {}
    }
    
    # Convert to Path objects
    target_dir = Path(target_dir)
    info_xml_path = Path(info_xml_path)
    
    # Validate inputs
    if not target_dir.exists():
        print(f"❌ Error: Target directory '{target_dir}' does not exist")
        return results
    
    if not target_dir.is_dir():
        print(f"❌ Error: '{target_dir}' is not a directory")
        return results
    
    if not info_xml_path.exists():
        print(f"❌ Error: Information XML file '{info_xml_path}' does not exist")
        return results
    
    # Parse information XML
    if verbose:
        print(f"📖 Parsing information XML: {info_xml_path}")
    
    growth_spread_data = parse_information_xml(str(info_xml_path))
    results['growth_spread_keys'] = list(growth_spread_data.keys())
    
    if not growth_spread_data:
        print("⚠️  Warning: No growth spread data found in information XML")
        return results
    
    # Store details about the data found
    for key, points in growth_spread_data.items():
        results['details'][key] = len(points)
    
    if verbose:
        print(f"\n✅ Found growth spread data for {len(growth_spread_data)} keys:")
        for key, count in results['details'].items():
            print(f"   • {key}: {count} data points")
    
    if verbose:
        print(f"\n📁 Processing XML files in: {target_dir}")
        if output_dir:
            print(f"📤 Output directory: {output_dir}")
        else:
            print("⚠️  Warning: Original files will be overwritten")
        print("-" * 60)
    
    # Process all XML files
    xml_files = list(target_dir.glob('*.xml'))
    
    if not xml_files:
        print("No XML files found in target directory")
        return results
    
    if verbose:
        print(f"Found {len(xml_files)} XML file(s) to process\n")
    
    for xml_path in xml_files:
        # Skip if this is the information XML file
        if xml_path.resolve() == info_xml_path.resolve():
            if verbose:
                print(f"⏭️  Skipping information XML: {xml_path.name}")
            continue
        
        results['total_processed'] += 1
        
        if verbose:
            print(f"📄 Processing: {xml_path.name}")
        
        success, message = modify_xml_file(str(xml_path), growth_spread_data, output_dir)
        
        if success:
            results['success'].append(xml_path.name)
            if verbose:
                print(f"   ✅ {message}")
        else:
            results['failed'].append((xml_path.name, message))
            if verbose:
                print(f"   ❌ {message}")
    
    # Print summary
    if verbose:
        print("\n" + "=" * 60)
        print("📊 PROCESSING SUMMARY:")
        print(f"   ✅ Successfully modified: {len(results['success'])} file(s)")
        print(f"   ❌ Failed/skipped: {len(results['failed'])} file(s)")
        print(f"   📁 Total processed: {results['total_processed']} file(s)")
        
        if results['failed'] and verbose:
            print("\n❌ Failed files:")
            for filename, reason in results['failed']:
                print(f"   - {filename}: {reason}")
    
    return results

def inspect_growth_spread_structure(info_xml_path):
    """
    Inspect the structure of GrowthSpread sections in the information XML.
    Useful for debugging and understanding the XML structure.
    """
    print(f"🔍 Inspecting GrowthSpread structure in: {info_xml_path}\n")
    
    try:
        with open(info_xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find a sample GrowthSpread section
        growth_spread_match = re.search(r'<GrowthSpread>(.*?)</GrowthSpread>', content, re.DOTALL)
        
        if growth_spread_match:
            sample = growth_spread_match.group(0)
            print("Sample GrowthSpread section:")
            print("=" * 60)
            
            # Pretty print the sample
            lines = sample.split('\n')
            for i, line in enumerate(lines[:50], 1):  # Show first 50 lines
                print(f"{i:3}: {line.rstrip()}")
            
            if len(lines) > 50:
                print(f"... ({len(lines) - 50} more lines)")
            
            # Count GrowthSpreadPoints sections in this sample
            points_count = sample.count('<GrowthSpreadPoints>')
            print(f"\n📊 Number of GrowthSpreadPoints sections in this sample: {points_count}")
            
            # Show a sample GrowthSpreadPoints content
            points_match = re.search(r'<GrowthSpreadPoints>(.*?)</GrowthSpreadPoints>', sample, re.DOTALL)
            if points_match:
                print("\nSample GrowthSpreadPoints content:")
                print("-" * 40)
                print(points_match.group(1)[:500])  # Show first 500 characters
                
        else:
            print("No GrowthSpread sections found in the file")
            
    except Exception as e:
        print(f"❌ Error inspecting file: {e}")

# Quick processing function
def quick_process(target_dir, info_xml_path, save_to_new_dir=False):
    """
    Quick processing with sensible defaults.
    """
    output_dir = None
    if save_to_new_dir:
        output_dir = os.path.join(target_dir, 'modified_xmls')
        print(f"💾 Modified files will be saved to: {output_dir}\n")
    
    return process_xml_files(target_dir, info_xml_path, output_dir)



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
        # Get UnderlierID
        underlier_id = growth_spread.find('UnderlierID')
        if underlier_id is not None and underlier_id.text:
            # Extract the first part before underscore
            match = re.match(r'^([^_]+)_', underlier_id.text)
            if match:
                base_name = match.group(1)
                
                # Parse GrowthSpreadPoints
                growth_points = []
                points_element = growth_spread.find('GrowthSpreadPoints')
                if points_element is not None and points_element.text:
                    # Parse each line in GrowthSpreadPoints
                    lines = points_element.text.strip().split('\n')
                    for line in lines:
                        # Extract Tex and Val values using regex
                        tex_match = re.search(r'Tex="(\d+)"', line)
                        type_match = re.search(r'text type="([a-zA-Z])"', line)
                        val_match = re.search(r'Val="([0-9.]+)"', line)
                        
                        if tex_match and type_match and val_match:
                            tex_value = tex_match.group(1)
                            type_char = type_match.group(1).lower()
                            val_value = val_match.group(1)
                            
                            growth_points.append({
                                'tenor': f"{tex_value}{type_char}",
                                'value': val_value
                            })
                
                growth_spread_data[base_name] = growth_points
    
    return growth_spread_data

def modify_xml_file(xml_path, growth_spread_data):
    """
    Modify a single XML file based on growth spread data.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Get MdSymbol value
        md_symbol = root.find('.//MdSymbol')
        if md_symbol is None or not md_symbol.text:
            print(f"Warning: No MdSymbol found in {xml_path}")
            return False
        
        # Extract the base name from MdSymbol
        match = re.match(r'^([^_]+)_', md_symbol.text)
        if not match:
            print(f"Warning: MdSymbol pattern not matched in {xml_path}")
            return False
        
        base_name = match.group(1)
        
        # Check if we have growth spread data for this base name
        if base_name not in growth_spread_data:
            print(f"Warning: No growth spread data found for {base_name} in {xml_path}")
            return False
        
        # Find BorrowShiftTermStructure section
        borrow_section = root.find('.//BorrowShiftTermStructure')
        if borrow_section is None:
            print(f"Warning: No BorrowShiftTermStructure section found in {xml_path}")
            return False
        
        # Remove existing Tenor and Value tags
        for tenor in borrow_section.findall('Tenor'):
            borrow_section.remove(tenor)
        for value in borrow_section.findall('Value'):
            borrow_section.remove(value)
        
        # Add new Tenor and Value tags based on growth spread data
        growth_points = growth_spread_data[base_name]
        for point in growth_points:
            # Create and add Tenor element
            tenor_elem = ET.SubElement(borrow_section, 'Tenor')
            tenor_elem.text = point['tenor']
            
            # Create and add Value element
            value_elem = ET.SubElement(borrow_section, 'Value')
            value_elem.text = point['value']
        
        # Save the modified XML
        output_path = xml_path.replace('.xml', '_modified.xml')
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        print(f"Successfully modified and saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {xml_path}: {str(e)}")
        return False

def process_all_xmls(info_xml_name='information.xml'):
    """
    Main function to process all XML files in the current directory.
    """
    current_dir = Path('.')
    
    # Find the information XML file
    info_xml_path = current_dir / info_xml_name
    if not info_xml_path.exists():
        print(f"Error: Information XML file '{info_xml_name}' not found!")
        return
    
    print(f"Parsing information from {info_xml_name}...")
    growth_spread_data = parse_information_xml(info_xml_path)
    
    if not growth_spread_data:
        print("No growth spread data found in information XML!")
        return
    
    print(f"Found growth spread data for: {', '.join(growth_spread_data.keys())}")
    
    # Process all XML files except the information XML
    xml_files = [f for f in current_dir.glob('*.xml') 
                 if f.name != info_xml_name and not f.name.endswith('_modified.xml')]
    
    if not xml_files:
        print("No XML files to modify found in current directory!")
        return
    
    print(f"\nProcessing {len(xml_files)} XML file(s)...")
    
    success_count = 0
    for xml_file in xml_files:
        print(f"\nProcessing: {xml_file.name}")
        if modify_xml_file(str(xml_file), growth_spread_data):
            success_count += 1
    
    print(f"\n{'='*50}")
    print(f"Processing complete: {success_count}/{len(xml_files)} files modified successfully")

# Alternative function if GrowthSpreadPoints contains child elements instead of text
def parse_information_xml_alternative(info_xml_path):
    """
    Alternative parser if GrowthSpreadPoints contains child elements.
    """
    tree = ET.parse(info_xml_path)
    root = tree.getroot()
    
    growth_spread_data = {}
    
    for growth_spread in root.findall('.//GrowthSpread'):
        underlier_id = growth_spread.find('UnderlierID')
        if underlier_id is not None and underlier_id.text:
            match = re.match(r'^([^_]+)_', underlier_id.text)
            if match:
                base_name = match.group(1)
                
                growth_points = []
                points_element = growth_spread.find('GrowthSpreadPoints')
                if points_element is not None:
                    # Look for child elements with gspt tag
                    for gspt in points_element.findall('.//gspt'):
                        tex_value = gspt.get('Tex')
                        val_value = gspt.get('Val')
                        # Try to find type attribute (might be in different format)
                        type_char = gspt.get('type', '')
                        if not type_char:
                            # Try to extract from other attributes
                            for attr_value in gspt.attrib.values():
                                if len(attr_value) == 1 and attr_value.isalpha():
                                    type_char = attr_value.lower()
                                    break
                        
                        if tex_value and val_value and type_char:
                            growth_points.append({
                                'tenor': f"{tex_value}{type_char}",
                                'value': val_value
                            })
                
                growth_spread_data[base_name] = growth_points
    
    return growth_spread_data

if __name__ == "__main__":
    # Run the main processing function
    process_all_xmls()
    
    # If you need to specify a different information XML filename:
    # process_all_xmls('your_info_file.xml')
