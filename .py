from lxml import etree
from datetime import datetime, timedelta
import os

def modify_xml_file(input_xml_path, index_name, output_dir=".", date_step=1):
    """
    Modify XML file for leveraged ETF product while preserving original formatting.
    
    Parameters:
    -----------
    input_xml_path : str
        Path to the input XML file
    index_name : str
        Name of the index to insert
    output_dir : str
        Directory to save output files (default: current directory)
    date_step : int
        Step size for date increments in days (default: 1 for daily, 7 for weekly, etc.)
    """
    
    # Parse the XML file - lxml preserves formatting better
    parser = etree.XMLParser(remove_blank_text=False, strip_cdata=False)
    tree = etree.parse(input_xml_path, parser)
    root = tree.getroot()
    
    # ========== Step 1: Find all BuildDate elements ==========
    build_dates = {}
    
    def find_build_dates(element, path=""):
        """Recursively find all BuildDate elements and their parent paths"""
        for child in element:
            current_path = f"{path}/{child.tag}" if path else child.tag
            
            if child.tag == "BuildDate":
                date_value = child.text.strip() if child.text else ""
                if date_value not in build_dates:
                    build_dates[date_value] = []
                # Store path without 'Component' as it's uniform
                clean_path = current_path.replace("/Component/", "").replace("Component/", "")
                build_dates[date_value].append(clean_path)
            
            find_build_dates(child, current_path)
    
    find_build_dates(root)
    
    # Check if all BuildDates are the same
    if len(build_dates) > 1:
        print("WARNING: Different BuildDate values found:")
        for date_val, paths in build_dates.items():
            print(f"  Date: {date_val}")
            for path in paths:
                # Extract parent sections (exclude BuildDate itself)
                parent_sections = " - ".join([p for p in path.split("/")[:-1] if p != "Component"])
                print(f"    Location: {parent_sections}")
        raise ValueError("BuildDate values are not consistent across the document")
    
    # Get the BuildDate
    build_date_str = list(build_dates.keys())[0].strip()
    build_date = datetime.strptime(build_date_str, "%Y-%m-%d")
    print(f"BuildDate: {build_date_str}")
    
    # ========== Step 2: Find DataSource in CalibratedForward/MarketData ==========
    expiry_date_str = None
    
    for calibrated_forward in root.iter("CalibratedForward"):
        for market_data in calibrated_forward.findall("MarketData"):
            data_source = market_data.find("DataSource")
            if data_source is not None and data_source.text:
                # Check if the text contains a date
                text = data_source.text.strip()
                try:
                    # Try to parse as date
                    datetime.strptime(text, "%Y-%m-%d")
                    expiry_date_str = text
                    break
                except ValueError:
                    continue
        if expiry_date_str:
            break
    
    if not expiry_date_str:
        raise ValueError("Could not find ExpiryDate in CalibratedForward/MarketData/DataSource")
    
    expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
    print(f"ExpiryDate: {expiry_date_str}")
    
    # ========== Step 3: Find Model name in Calculate section ==========
    model_name = None
    calculate_elem = root.find(".//Calculate")
    
    if calculate_elem is None:
        raise ValueError("Could not find <Calculate> section")
    
    model_elem = calculate_elem.find("Model")
    if model_elem is not None and model_elem.text:
        model_name = model_elem.text.strip()
    else:
        raise ValueError("Could not find <Model> in <Calculate> section")
    
    print(f"Model Name: {model_name}")
    
    # ========== Step 4: Generate dates from BuildDate to ExpiryDate ==========
    date_list = []
    current_date = build_date
    while current_date <= expiry_date:
        date_list.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=date_step)
    
    print(f"Generated {len(date_list)} dates from {build_date_str} to {expiry_date_str} (step: {date_step} days)")
    
    # ========== Step 5: Create three versions with different DateToMatch ==========
    date_to_match_options = [
        ("BuildDate", build_date_str),
        ("ExpiryDate", expiry_date_str),
        ("Empty", None)
    ]
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for option_name, date_value in date_to_match_options:
        # Create a deep copy by re-parsing to ensure complete independence
        tree_copy = etree.parse(input_xml_path, parser)
        root_copy = tree_copy.getroot()
        
        # Find Calculate element in the copy
        calculate_elem_copy = root_copy.find(".//Calculate")
        
        if calculate_elem_copy is None:
            raise ValueError("Could not find <Calculate> element in the copy")
        
        # Find the parent of Calculate
        parent = calculate_elem_copy.getparent()
        
        if parent is None:
            raise ValueError("Could not find parent of <Calculate> element")
        
        print(f"\n{option_name}: Found Calculate element, parent is <{parent.tag}>")
        
        # Create IndexValuation element with proper indentation
        index_valuation = etree.Element("IndexValuation")
        
        # Add Index element (4 spaces indentation)
        index_elem = etree.SubElement(index_valuation, "Index")
        index_elem.text = index_name
        
        # Add Model element (4 spaces indentation)
        model_elem_new = etree.SubElement(index_valuation, "Model")
        model_elem_new.text = model_name
        
        # Add multiple Date elements (4 spaces indentation for each)
        for date_str in date_list:
            date_elem = etree.SubElement(index_valuation, "Date")
            date_elem.text = date_str
        
        # Find index of Calculate in parent
        calc_index = list(parent).index(calculate_elem_copy)
        print(f"{option_name}: Calculate is at index {calc_index} in parent")
        
        # Insert IndexValuation right before Calculate
        parent.insert(calc_index, index_valuation)
        print(f"{option_name}: Inserted IndexValuation at index {calc_index}")
        
        # Modify DateToMatch in CalibratedForward
        for calibrated_forward in root_copy.iter("CalibratedForward"):
            date_to_match_elem = calibrated_forward.find("DateToMatch")
            
            if option_name == "Empty":
                # Remove DateToMatch if it exists
                if date_to_match_elem is not None:
                    calibrated_forward.remove(date_to_match_elem)
                    print(f"{option_name}: Removed DateToMatch from CalibratedForward")
            else:
                # Set or create DateToMatch
                if date_to_match_elem is None:
                    date_to_match_elem = etree.SubElement(calibrated_forward, "DateToMatch")
                    print(f"{option_name}: Created new DateToMatch element")
                date_to_match_elem.text = date_value
                print(f"{option_name}: Set DateToMatch to {date_value}")
        
        # Save the file - first to a temporary location to manually add indentation
        output_filename = f"{index_name}_{option_name}.xml"
        output_path = os.path.join(output_dir, output_filename)
        
        # Convert to string for manual indentation formatting
        xml_string = etree.tostring(tree_copy, encoding='unicode', xml_declaration=False)
        
        # Add proper indentation to IndexValuation section
        # This is a bit hacky but preserves the rest of the formatting
        xml_string = xml_string.replace('<IndexValuation>', '  <IndexValuation>\n')
        xml_string = xml_string.replace('</IndexValuation>', '  </IndexValuation>\n')
        xml_string = xml_string.replace('<Index>', '    <Index>')
        xml_string = xml_string.replace('<Model>', '    <Model>')
        xml_string = xml_string.replace('</Model>', '</Model>\n')
        xml_string = xml_string.replace('<Date>', '    <Date>')
        xml_string = xml_string.replace('</Date>', '</Date>\n')
        
        # Write with XML declaration
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write(xml_string)
        
        print(f"Saved: {output_path}")
    
    print("\nAll files generated successfully!")
    return True

# Example usage:
if __name__ == "__main__":
    # Daily dates (default)
    modify_xml_file(
        input_xml_path="your_input_file.xml",
        index_name="SPX500",
        output_dir="./output",
        date_step=1  # Daily
    )
    
    # Weekly dates
    modify_xml_file(
        input_xml_path="your_input_file.xml",
        index_name="SPX500_Weekly",
        output_dir="./output",
        date_step=7  # Weekly
    )
