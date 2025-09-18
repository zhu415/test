# Example 1: Basic usage
results = process_xml_files(
    target_dir='path/to/xml/directory',
    info_xml_path='path/to/information.xml'
)

# Example 2: Save to a different directory (preserves originals)
results = process_xml_files(
    target_dir='path/to/xml/directory',
    info_xml_path='path/to/information.xml',
    output_dir='path/to/output/directory'
)

# Example 3: Quick process with automatic output directory
results = quick_process(
    target_dir='path/to/xml/directory',
    info_xml_path='path/to/information.xml',
    save_to_new_dir=True  # Creates 'modified_xmls' subdirectory
)

# Example 4: Process without verbose output
results = process_xml_files(
    target_dir='path/to/xml/directory',
    info_xml_path='path/to/information.xml',
    verbose=False
)

# Example 5: Analyze an XML file structure (for debugging)
analyze_xml_structure('path/to/sample.xml', show_content=True)

# Example 6: Check processing results
print(f"Successfully modified: {results['success']}")
print(f"Failed files: {results['failed']}")
print(f"Available growth spread keys: {results['growth_spread_keys']}")

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
from pathlib import Path

def validate_and_fix_xml(xml_content):
    """
    Attempt to fix common XML issues.
    """
    # Remove any content after the last closing tag
    # Find the last occurrence of a closing tag that looks like a root element
    import re
    
    # Try to find the actual root closing tag
    # This pattern looks for </SomethingRoot> or similar
    root_pattern = r'</[\w]+>\s*$'
    match = re.search(root_pattern, xml_content)
    
    if match:
        # Truncate content after the root closing tag
        end_pos = match.end()
        xml_content = xml_content[:end_pos]
    
    return xml_content

def parse_information_xml_safe(info_xml_path):
    """
    Parse the information XML with error recovery for malformed XML.
    """
    print(f"📖 Attempting to parse: {info_xml_path}")
    
    # First, try to read and examine the file
    try:
        with open(info_xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse as-is first
        try:
            tree = ET.ElementTree(ET.fromstring(content))
            print("✅ XML parsed successfully")
            return parse_growth_spread_from_tree(tree)
        
        except ET.ParseError as e:
            print(f"⚠️ Initial parse failed: {e}")
            print("🔧 Attempting to fix XML...")
            
            # Try to fix common issues
            fixed_content = validate_and_fix_xml(content)
            
            try:
                tree = ET.ElementTree(ET.fromstring(fixed_content))
                print("✅ Fixed XML parsed successfully")
                return parse_growth_spread_from_tree(tree)
            
            except ET.ParseError:
                # If standard parsing fails, try a more aggressive approach
                print("🔧 Trying alternative parsing method...")
                return parse_information_xml_iterative(info_xml_path)
    
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return {}

def parse_information_xml_iterative(info_xml_path):
    """
    Parse XML iteratively to handle large or problematic files.
    This method is more forgiving of XML structure issues.
    """
    growth_spread_data = {}
    
    try:
        # Use iterparse for more control
        for event, elem in ET.iterparse(info_xml_path, events=('start', 'end')):
            if event == 'end' and elem.tag == 'GrowthSpread':
                # Process GrowthSpread element
                underlier_id_elem = elem.find('UnderlierID')
                if underlier_id_elem is not None and underlier_id_elem.text:
                    underlier_id = underlier_id_elem.text
                    
                    # Extract the "someString" part
                    match = re.match(r'^([^_]+)_.*', underlier_id)
                    if match:
                        key_part = match.group(1)
                        
                        # Parse GrowthSpreadPoints
                        points_elem = elem.find('GrowthSpreadPoints')
                        if points_elem is not None and points_elem.text:
                            points_data = parse_growth_spread_points(points_elem.text)
                            if points_data:  # Only add if we got valid data
                                growth_spread_data[key_part] = points_data
                                print(f"   ✅ Found data for: {key_part} ({len(points_data)} points)")
                
                # Clear the element to save memory
                elem.clear()
        
        print(f"📊 Total keys extracted: {len(growth_spread_data)}")
        return growth_spread_data
    
    except ET.ParseError as e:
        print(f"❌ Iterative parsing failed: {e}")
        # Try one more method - manual extraction
        return extract_growth_spread_manually(info_xml_path)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {}

def extract_growth_spread_manually(info_xml_path):
    """
    Manual extraction of GrowthSpread data using regex.
    Last resort for badly formed XML.
    """
    print("🔧 Attempting manual extraction...")
    growth_spread_data = {}
    
    try:
        with open(info_xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all GrowthSpread sections using regex
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
                    
                    # Extract GrowthSpreadPoints
                    points_match = re.search(r'<GrowthSpreadPoints>(.*?)</GrowthSpreadPoints>', gs_content, re.DOTALL)
                    if points_match:
                        points_text = points_match.group(1)
                        points_data = parse_growth_spread_points(points_text)
                        if points_data:
                            growth_spread_data[key_part] = points_data
                            print(f"   ✅ Manually extracted: {key_part} ({len(points_data)} points)")
        
        print(f"📊 Manual extraction found: {len(growth_spread_data)} keys")
        return growth_spread_data
    
    except Exception as e:
        print(f"❌ Manual extraction failed: {e}")
        return {}

def parse_growth_spread_from_tree(tree):
    """
    Extract GrowthSpread data from a parsed XML tree.
    """
    root = tree.getroot()
    growth_spread_data = {}
    
    # Find all GrowthSpread sections
    for growth_spread in root.findall('.//GrowthSpread'):
        underlier_id_elem = growth_spread.find('UnderlierID')
        if underlier_id_elem is not None and underlier_id_elem.text:
            underlier_id = underlier_id_elem.text
            
            # Extract the "someString" part
            match = re.match(r'^([^_]+)_.*', underlier_id)
            if match:
                key_part = match.group(1)
                
                # Parse GrowthSpreadPoints
                points_elem = growth_spread.find('GrowthSpreadPoints')
                if points_elem is not None and points_elem.text:
                    points_data = parse_growth_spread_points(points_elem.text)
                    if points_data:
                        growth_spread_data[key_part] = points_data
    
    return growth_spread_data

def parse_growth_spread_points(points_text):
    """
    Parse the GrowthSpreadPoints text to extract Tex and Val values.
    """
    if not points_text:
        return []
    
    points = []
    lines = points_text.strip().split('\n')
    
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
            
        # Parse pattern: <gspt dateType="F" Tex="intValue" text type="singleCharacter" Val="decimalValue" ...>
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

def inspect_xml_file(xml_path, num_lines=50):
    """
    Inspect the first few lines of an XML file to understand its structure.
    """
    print(f"\n🔍 Inspecting: {xml_path}")
    print("=" * 60)
    
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"Total lines in file: {len(lines)}")
        print(f"\nFirst {num_lines} lines:")
        print("-" * 40)
        
        for i, line in enumerate(lines[:num_lines], 1):
            print(f"{i:3}: {line.rstrip()}")
        
        # Check for content after line 20
        if len(lines) > 20:
            print(f"\n⚠️ Content around line 20:")
            for i in range(max(0, 18), min(len(lines), 25)):
                print(f"{i+1:3}: {lines[i].rstrip()}")
        
        # Look for root element
        root_found = False
        root_tag = None
        for i, line in enumerate(lines[:30]):
            if not root_found and '<' in line and not line.strip().startswith('<?'):
                match = re.search(r'<([^/>\s]+)', line)
                if match:
                    root_tag = match.group(1)
                    root_found = True
                    print(f"\n📌 Likely root element: <{root_tag}> at line {i+1}")
                    break
        
        # Look for closing root tag
        if root_tag:
            closing_pattern = f'</{root_tag}>'
            for i, line in enumerate(lines):
                if closing_pattern in line:
                    print(f"📌 Closing root found: {closing_pattern} at line {i+1}")
                    
                    # Check if there's content after this
                    if i < len(lines) - 1:
                        remaining = len(lines) - i - 1
                        print(f"\n⚠️ WARNING: {remaining} lines found after closing root tag!")
                        print("Content after closing tag:")
                        for j in range(i+1, min(i+6, len(lines))):
                            print(f"{j+1:3}: {lines[j].rstrip()}")
                    break
        
    except Exception as e:
        print(f"❌ Error inspecting file: {e}")

# Modified main processing function
def process_xml_files(target_dir, info_xml_path, output_dir=None, verbose=True):
    """
    Process XML files with improved error handling.
    """
    results = {
        'success': [],
        'failed': [],
        'growth_spread_keys': [],
        'total_processed': 0
    }
    
    # Convert to Path objects
    target_dir = Path(target_dir)
    info_xml_path = Path(info_xml_path)
    
    # Validate inputs
    if not target_dir.exists():
        print(f"❌ Error: Target directory '{target_dir}' does not exist")
        return results
    
    if not info_xml_path.exists():
        print(f"❌ Error: Information XML file '{info_xml_path}' does not exist")
        return results
    
    # Parse information XML with enhanced error handling
    growth_spread_data = parse_information_xml_safe(str(info_xml_path))
    results['growth_spread_keys'] = list(growth_spread_data.keys())
    
    if not growth_spread_data:
        print("\n⚠️ No growth spread data could be extracted from the information XML")
        print("Try running: inspect_xml_file(info_xml_path) to examine the file structure")
        return results
    
    if verbose:
        print(f"\n✅ Successfully extracted data for: {', '.join(growth_spread_data.keys())}")
        print(f"📁 Processing XML files in: {target_dir}")
        if output_dir:
            print(f"📤 Output directory: {output_dir}")
        print("-" * 60)
    
    # Continue with processing files...
    xml_files = list(target_dir.glob('*.xml'))
    
    for xml_path in xml_files:
        if xml_path.resolve() == info_xml_path.resolve():
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
    
    return results

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
        
        # Extract the matching part from MdSymbol
        match = re.match(r'^([^_]+)_.*', md_symbol)
        if not match:
            return False, f"MdSymbol '{md_symbol}' doesn't match pattern"
        
        key_part = match.group(1)
        
        # Check if we have data for this symbol
        if key_part not in growth_spread_data:
            return False, f"No data for '{key_part}'"
        
        points_data = growth_spread_data[key_part]
        
        # Find BorrowShiftTermStructure section
        borrow_section = root.find('.//BorrowShiftTermStructure')
        if borrow_section is None:
            return False, "No BorrowShiftTermStructure section"
        
        # Remove existing Tenor and Value elements
        for elem in list(borrow_section):
            if elem.tag in ['Tenor', 'Value']:
                borrow_section.remove(elem)
        
        # Add new elements
        for tenor, value in points_data:
            tenor_elem = ET.SubElement(borrow_section, 'Tenor')
            tenor_elem.text = tenor
            
            value_elem = ET.SubElement(borrow_section, 'Value')
            value_elem.text = value
        
        # Save
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, os.path.basename(xml_path))
        else:
            output_path = xml_path
        
        save_formatted_xml(tree, output_path)
        return True, f"Modified with {len(points_data)} points"
        
    except Exception as e:
        return False, f"Error: {e}"

def save_formatted_xml(tree, filepath):
    """
    Save XML with proper formatting.
    """
    xml_str = ET.tostring(tree.getroot(), encoding='unicode')
    dom = minidom.parseString(xml_str)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(dom.toprettyxml(indent="  "))


# First, inspect the problematic XML file to see what's wrong
inspect_xml_file('path/to/information.xml', num_lines=30)

# Then process with the enhanced error handling
results = process_xml_files(
    target_dir='path/to/xml/directory',
    info_xml_path='path/to/information.xml'
)

# If it still fails, try manual inspection and debugging
# This will show you exactly what's at line 20
with open('path/to/information.xml', 'r') as f:
    lines = f.readlines()
    for i in range(15, min(25, len(lines))):
        print(f"Line {i+1}: {lines[i].rstrip()}")
