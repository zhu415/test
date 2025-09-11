import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import os

class ConvertibleBondXMLProcessor:
    def __init__(self):
        self.tree = None
        self.root = None
        self.expiry_date = None
        
    def load_xml(self, filepath):
        """Load XML file"""
        try:
            self.tree = ET.parse(filepath)
            self.root = self.tree.getroot()
            print(f"✓ Successfully loaded XML: {filepath}")
            return True
        except Exception as e:
            print(f"✗ Error loading XML: {e}")
            return False
    
    def prettify_xml(self, elem):
        """Return a pretty-printed XML string for the Element."""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def find_convertible_bond(self):
        """Find convertibleBond section and extract expiry date"""
        cb_element = self.root.find('.//convertibleBond')
        if cb_element is None:
            print("⚠️ WARNING: <convertibleBond> section not found!")
            return False
        
        print("✓ Found <convertibleBond> section")
        
        expiry_element = cb_element.find('.//ExpiryDate')
        if expiry_element is not None:
            self.expiry_date = expiry_element.text
            print(f"✓ Found expiry date: {self.expiry_date}")
        else:
            print("⚠️ WARNING: ExpiryDate not found in convertibleBond section")
            
        return cb_element
    
    def comment_out_element(self, parent, element):
        """Comment out an XML element"""
        comment_text = ET.tostring(element, encoding='unicode')
        comment = ET.Comment(comment_text)
        parent.insert(list(parent).index(element), comment)
        parent.remove(element)
    
    def process_not_callable(self, cb_element):
        """Process for not callable type - comment out CallSchedule if exists"""
        call_schedule = cb_element.find('.//CallSchedule')
        if call_schedule is not None:
            # Create comment with the CallSchedule content
            comment_text = ET.tostring(call_schedule, encoding='unicode')
            comment = ET.Comment(comment_text)
            
            # Find parent and replace with comment
            parent = cb_element
            for elem in cb_element.iter():
                if call_schedule in elem:
                    parent = elem
                    break
            
            parent.insert(list(parent).index(call_schedule), comment)
            parent.remove(call_schedule)
            print("✓ CallSchedule section has been commented out")
        else:
            print("ℹ️ CallSchedule section not found - no modification needed")
    
    def process_callable(self, cb_element, call_type, start_date, end_date, 
                        call_price=1000, call_notice_period=None,
                        trigger=None, trigger_knocked_days=None, 
                        trigger_lookback_days=None, trigger_reset=None):
        """Process for callable types (hard or soft)"""
        
        # Validate end date against expiry date
        if self.expiry_date and end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                expiry_dt = datetime.strptime(self.expiry_date, "%Y-%m-%d")
                if end_dt > expiry_dt:
                    print(f"✗ ERROR: End date {end_date} exceeds expiry date {self.expiry_date}")
                    return False
            except ValueError as e:
                print(f"✗ Error parsing dates: {e}")
        
        # Find or create CallSchedule
        call_schedule = cb_element.find('.//CallSchedule')
        
        if call_schedule is None:
            # Create new CallSchedule section
            call_schedule = ET.SubElement(cb_element, 'CallSchedule')
            print("✓ Created new CallSchedule section")
        else:
            # Clear existing CallSchedule for updating
            call_schedule.clear()
            call_schedule.tag = 'CallSchedule'
            print("✓ Found existing CallSchedule section - updating")
        
        # Add basic elements
        ET.SubElement(call_schedule, 'StartDate').text = start_date
        ET.SubElement(call_schedule, 'EndDate').text = end_date
        ET.SubElement(call_schedule, 'CallPrice').text = str(call_price)
        
        # Add CallNoticePeriod if provided
        if call_notice_period is not None:
            ET.SubElement(call_schedule, 'CallNoticePeriod').text = str(call_notice_period)
        
        # Add soft call specific elements
        if call_type.lower() == 'soft':
            if trigger is not None:
                ET.SubElement(call_schedule, 'Trigger').text = str(trigger)
            if trigger_knocked_days is not None:
                ET.SubElement(call_schedule, 'TriggerKnockedDays').text = str(trigger_knocked_days)
            if trigger_lookback_days is not None:
                ET.SubElement(call_schedule, 'TriggerLookbackDays').text = str(trigger_lookback_days)
            if trigger_reset is not None:
                ET.SubElement(call_schedule, 'TriggerReset').text = str(trigger_reset).lower()
            print("✓ Added soft call parameters")
        else:
            print("✓ Configured for hard call (no trigger parameters)")
        
        return True
    
    def save_modified_xml(self, original_filepath, call_type, additional_info=""):
        """Save modified XML with descriptive filename"""
        # Create output filename
        base_name = os.path.splitext(os.path.basename(original_filepath))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Map call types to abbreviations
        type_map = {
            'not callable': 'non',
            'soft': 'soft',
            'hard': 'hard'
        }
        
        type_abbr = type_map.get(call_type.lower(), call_type.lower())
        
        if additional_info:
            output_filename = f"{base_name}_{type_abbr}_{additional_info}_{timestamp}.xml"
        else:
            output_filename = f"{base_name}_{type_abbr}_{timestamp}.xml"
        
        # Save the file
        self.tree.write(output_filename, encoding='utf-8', xml_declaration=True)
        print(f"✓ Saved modified XML as: {output_filename}")
        return output_filename
    
    def extract_output_info(self, output_xml_path):
        """Extract information from output XML"""
        try:
            tree = ET.parse(output_xml_path)
            root = tree.getroot()
            
            results = {}
            
            print(f"\n📄 Extracting from: {output_xml_path}")
            print("-" * 40)
            
            # Find Result section
            result_section = root.find('.//Result')
            if result_section is None:
                print("⚠️ WARNING: <Result> section not found in output XML")
                return results
            
            # Extract LatticeJumpDiffusionResults info
            ljd_section = result_section.find('.//LatticeJumpDiffusionResults')
            if ljd_section is not None:
                grid_delta = ljd_section.find('.//GridDelta')
                grid_gamma = ljd_section.find('.//GridGamma')
                
                if grid_delta is not None:
                    results['GridDelta'] = grid_delta.text
                    print(f"📊 GridDelta: {grid_delta.text}")
                
                if grid_gamma is not None:
                    results['GridGamma'] = grid_gamma.text
                    print(f"📊 GridGamma: {grid_gamma.text}")
            else:
                print("ℹ️ LatticeJumpDiffusionResults section not found")
            
            # Extract PresentValue info
            pv_section = result_section.find('.//PresentValue')
            if pv_section is not None:
                value = pv_section.find('.//Value')
                if value is not None:
                    results['PresentValue'] = value.text
                    print(f"💰 PresentValue: {value.text}")
            else:
                print("ℹ️ PresentValue section not found")
            
            print("-" * 40)
            return results
            
        except Exception as e:
            print(f"✗ Error extracting output info: {e}")
            return {}

# ===============================================
# JUPYTER NOTEBOOK USAGE EXAMPLES
# ===============================================

# Step 1: Create processor instance
processor = ConvertibleBondXMLProcessor()

# -----------------------------------------------
# EXAMPLE 1: Process "Not Callable" bond
# -----------------------------------------------
def process_not_callable_example(input_file):
    """Example for processing not callable bond"""
    print("=" * 50)
    print("Processing NOT CALLABLE Bond")
    print("=" * 50)
    
    # Load the XML
    if not processor.load_xml(input_file):
        return None
    
    # Find convertible bond section
    cb_element = processor.find_convertible_bond()
    if not cb_element:
        return None
    
    # Process as not callable
    processor.process_not_callable(cb_element)
    
    # Save the modified XML
    output_file = processor.save_modified_xml(input_file, "not callable", "example")
    return output_file

# -----------------------------------------------
# EXAMPLE 2: Process "Hard Call" bond
# -----------------------------------------------
def process_hard_call_example(input_file):
    """Example for processing hard call bond"""
    print("=" * 50)
    print("Processing HARD CALL Bond")
    print("=" * 50)
    
    # Load the XML
    if not processor.load_xml(input_file):
        return None
    
    # Find convertible bond section
    cb_element = processor.find_convertible_bond()
    if not cb_element:
        return None
    
    # Process as hard call
    processor.process_callable(
        cb_element,
        call_type="hard",
        start_date="2026-09-15",
        end_date="2028-09-15",
        call_price=1000,
        call_notice_period=40  # Optional - remove if not needed
    )
    
    # Save the modified XML
    output_file = processor.save_modified_xml(input_file, "hard", "example")
    return output_file

# -----------------------------------------------
# EXAMPLE 3: Process "Soft Call" bond
# -----------------------------------------------
def process_soft_call_example(input_file):
    """Example for processing soft call bond"""
    print("=" * 50)
    print("Processing SOFT CALL Bond")
    print("=" * 50)
    
    # Load the XML
    if not processor.load_xml(input_file):
        return None
    
    # Find convertible bond section
    cb_element = processor.find_convertible_bond()
    if not cb_element:
        return None
    
    # Process as soft call
    processor.process_callable(
        cb_element,
        call_type="soft",
        start_date="2026-09-15",
        end_date="2028-09-15",
        call_price=1000,
        call_notice_period=40,  # Optional - remove if not needed
        trigger=105,
        trigger_knocked_days=20,
        trigger_lookback_days=30,
        trigger_reset=True
    )
    
    # Save the modified XML
    output_file = processor.save_modified_xml(input_file, "soft", "example")
    return output_file

# -----------------------------------------------
# EXAMPLE 4: Extract output information
# -----------------------------------------------
def extract_output_example(output_file):
    """Example for extracting information from output XML"""
    print("=" * 50)
    print("Extracting Output Information")
    print("=" * 50)
    
    results = processor.extract_output_info(output_file)
    return results

# ===============================================
# QUICK START - Copy and modify these cells
# ===============================================

# Cell 1: Initialize and load your input file
print("🚀 Quick Start Examples\n")
print("Copy these cells and modify the parameters as needed:\n")

# Cell 2: For NOT CALLABLE bond
print("""
# For NOT CALLABLE bond:
processor = ConvertibleBondXMLProcessor()
processor.load_xml("your_input.xml")
cb_element = processor.find_convertible_bond()
if cb_element:
    processor.process_not_callable(cb_element)
    output_file = processor.save_modified_xml("your_input.xml", "not callable")
""")

# Cell 3: For HARD CALL bond
print("""
# For HARD CALL bond:
processor = ConvertibleBondXMLProcessor()
processor.load_xml("your_input.xml")
cb_element = processor.find_convertible_bond()
if cb_element:
    processor.process_callable(
        cb_element,
        call_type="hard",
        start_date="2026-09-15",
        end_date="2028-09-15",
        call_price=1000,
        call_notice_period=40  # Optional
    )
    output_file = processor.save_modified_xml("your_input.xml", "hard", "test1")
""")

# Cell 4: For SOFT CALL bond
print("""
# For SOFT CALL bond:
processor = ConvertibleBondXMLProcessor()
processor.load_xml("your_input.xml")
cb_element = processor.find_convertible_bond()
if cb_element:
    processor.process_callable(
        cb_element,
        call_type="soft",
        start_date="2026-09-15",
        end_date="2028-09-15",
        call_price=1000,
        call_notice_period=40,  # Optional
        trigger=105,
        trigger_knocked_days=20,
        trigger_lookback_days=30,
        trigger_reset=True
    )
    output_file = processor.save_modified_xml("your_input.xml", "soft", "test1")
""")

# Cell 5: For extracting output
print("""
# For extracting output information:
processor = ConvertibleBondXMLProcessor()
results = processor.extract_output_info("your_output.xml")
print(f"\\nExtracted values: {results}")
""")
