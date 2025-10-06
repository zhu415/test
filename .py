import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Tuple


def parse_txt_file(txt_path: str) -> Dict[str, Dict]:
    """
    Parse the txt file to extract weights and borrow shift data.
    
    Returns:
        Dict with structure: {
            'IndexName': {
                'name': str,
                'weights': {component: weight},
                'borrow_shift': {tenor: value}
            }
        }
    """
    configs = {}
    
    with open(txt_path, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Parse the name line: {name} ({IndexName})
        if '(' in line and ')' in line:
            name_part = line[:line.rfind('(')].strip()
            index_name = line[line.rfind('(') + 1:line.rfind(')')].strip()
            
            configs[index_name] = {
                'name': name_part,
                'weights': {},
                'borrow_shift': {}
            }
            
            i += 1
            
            # Parse weights section
            if i < len(lines) and '- weights' in lines[i]:
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('-'):
                    weight_line = lines[i].strip()
                    if ':' in weight_line:
                        component, weight = weight_line.split(':', 1)
                        configs[index_name]['weights'][component.strip()] = float(weight.strip())
                    i += 1
            
            # Parse borrow shift section
            if i < len(lines) and '- borrow shift' in lines[i]:
                i += 1
                while i < len(lines) and lines[i].strip() and not '(' in lines[i]:
                    shift_line = lines[i].strip()
                    if ':' in shift_line:
                        tenor, value = shift_line.split(':', 1)
                        configs[index_name]['borrow_shift'][tenor.strip()] = float(value.strip())
                    i += 1
        else:
            i += 1
    
    return configs


def modify_xml_file(xml_path: str, config: Dict, update_time: datetime):
    """
    Modify a single XML file based on the configuration.
    
    Args:
        xml_path: Path to the XML file
        config: Configuration dict with 'weights' and 'borrow_shift'
        update_time: DateTime object for the UpdateTime field
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Find BenchmarkIndex element
    benchmark_index = root.find('BenchmarkIndex')
    if benchmark_index is None:
        print(f"Warning: No BenchmarkIndex found in {xml_path}")
        return
    
    # Update BenchmarkComponent and SourceWeight
    # Remove existing components and weights
    for component in benchmark_index.findall('BenchmarkComponent'):
        benchmark_index.remove(component)
    
    basket_methodology = benchmark_index.find('BasketMethodology')
    if basket_methodology is None:
        basket_methodology = ET.SubElement(benchmark_index, 'BasketMethodology')
    
    for weight_elem in basket_methodology.findall('SourceWeight'):
        basket_methodology.remove(weight_elem)
    
    # Add new components and weights
    insertion_point = list(benchmark_index).index(basket_methodology) if basket_methodology in benchmark_index else len(benchmark_index)
    
    for idx, (component, weight) in enumerate(config['weights'].items()):
        # Insert BenchmarkComponent before BasketMethodology
        component_elem = ET.Element('BenchmarkComponent')
        component_elem.text = component
        benchmark_index.insert(insertion_point + idx, component_elem)
        
        # Add SourceWeight inside BasketMethodology
        weight_elem = ET.SubElement(basket_methodology, 'SourceWeight')
        weight_elem.text = str(weight)
    
    # Update BorrowShiftTermStructure
    borrow_shift = basket_methodology.find('BorrowShiftTermStructure')
    if borrow_shift is None:
        borrow_shift = ET.SubElement(basket_methodology, 'BorrowShiftTermStructure')
    
    # Remove existing Tenor and Value elements
    for tenor in borrow_shift.findall('Tenor'):
        borrow_shift.remove(tenor)
    for value in borrow_shift.findall('Value'):
        borrow_shift.remove(value)
    
    # Add new Tenor and Value elements
    for tenor in config['borrow_shift'].keys():
        tenor_elem = ET.SubElement(borrow_shift, 'Tenor')
        tenor_elem.text = tenor
    
    for value in config['borrow_shift'].values():
        value_elem = ET.SubElement(borrow_shift, 'Value')
        value_elem.text = str(value)
    
    # Ensure Method element exists
    if borrow_shift.find('Method') is None:
        method_elem = ET.SubElement(borrow_shift, 'Method')
        method_elem.text = 'Additive'
    
    # Update UpdateTime
    update_time_elem = root.find('UpdateTime')
    if update_time_elem is None:
        update_time_elem = ET.SubElement(root, 'UpdateTime')
    update_time_elem.text = update_time.strftime('%Y-%m-%dT%H:%M:%S.000')
    
    # Write back to file
    tree.write(xml_path, encoding='utf-8', xml_declaration=True)
    print(f"Successfully updated {xml_path}")


def modify_xml_files_from_txt(xml_directory: str, txt_file: str, update_time_str: str):
    """
    Main function to modify XML files in a directory based on a txt configuration file.
    
    Args:
        xml_directory: Directory containing XML files
        txt_file: Path to the txt configuration file
        update_time_str: Update time in format 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD HH:MM'
    """
    # Parse update time
    try:
        if len(update_time_str.split(':')) == 2:
            update_time = datetime.strptime(update_time_str, '%Y-%m-%d %H:%M')
        else:
            update_time = datetime.strptime(update_time_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        print(f"Error: Invalid time format '{update_time_str}'. Use 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD HH:MM'")
        return
    
    # Parse txt file
    configs = parse_txt_file(txt_file)
    print(f"Parsed {len(configs)} configurations from {txt_file}")
    
    # Process each XML file
    for filename in os.listdir(xml_directory):
        if filename.endswith('.xml'):
            # Extract index name from filename (remove .xml extension)
            index_name = filename[:-4]
            
            if index_name in configs:
                xml_path = os.path.join(xml_directory, filename)
                print(f"\nProcessing {filename}...")
                modify_xml_file(xml_path, configs[index_name], update_time)
            else:
                print(f"Warning: No configuration found for {filename}")


# Example usage:
if __name__ == "__main__":
    # Example call
    modify_xml_files_from_txt(
        xml_directory="/path/to/xml/files",
        txt_file="/path/to/config.txt",
        update_time_str="2025-10-06 15:30:00"
    )
