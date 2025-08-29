import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import html

class JavaToXMLTemplateConverter:
“”“Converter that wraps Java code in a specific XML template structure”””

```
def __init__(self):
    self.java_content = ""
    
def read_java_file(self, file_path):
    """Read the Java source file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            self.java_content = f.read()
        return True
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False

def create_xml_template(self, name, version, simple_class_name, dependency="Ang/libamgx"):
    """
    Create the XML template with the specified structure
    
    Args:
        name: Name for the component
        version: Version string
        simple_class_name: Simple class name
        dependency: Dependency string (default: Ang/libamgx)
    
    Returns:
        XML string with proper formatting
    """
    # Create the root element
    root = ET.Element("Component")
    
    # Create JavaDynamicIndexTemplate
    template = ET.SubElement(root, "JavaDynamicIndexTemplate")
    
    # Add Name element
    name_elem = ET.SubElement(template, "Name")
    name_elem.text = name
    
    # Add Version element
    version_elem = ET.SubElement(template, "Version")
    version_elem.text = version
    
    # Add SimpleClassName element
    class_elem = ET.SubElement(template, "SimpleClassName")
    class_elem.text = simple_class_name
    
    # Add Dependency element
    dependency_elem = ET.SubElement(template, "Dependency")
    dependency_elem.text = dependency
    
    # Add SourceCode element with the Java content
    # Preserve the entire Java file including imports and package declarations
    source_elem = ET.SubElement(template, "SourceCode")
    # Use CDATA or escape the Java code to preserve it exactly
    source_elem.text = self.java_content
    
    # Convert to string with pretty printing
    xml_string = self.prettify_xml(root)
    return xml_string

def prettify_xml(self, elem):
    """Return a pretty-printed XML string for the Element"""
    rough_string = ET.tostring(elem, encoding='unicode', method='xml')
    reparsed = minidom.parseString(rough_string)
    
    # Get the pretty printed version
    pretty_xml = reparsed.toprettyxml(indent="    ", encoding=None)
    
    # Remove the XML declaration line as we'll add our own
    lines = pretty_xml.split('\n')
    if lines[0].startswith('<?xml'):
        lines = lines[1:]
    
    # Remove empty lines
    lines = [line.rstrip() for line in lines if line.strip()]
    
    # Add XML declaration
    result = '<?xml version="1.0" encoding="UTF-8"?>\n' + '\n'.join(lines)
    
    return result

def convert(self, java_file_path, output_xml_path, name, version, 
            simple_class_name, dependency="Ang/libamgx"):
    """
    Main conversion method
    
    Args:
        java_file_path: Path to input Java file
        output_xml_path: Path for output XML file
        name: Component name
        version: Component version
        simple_class_name: Simple class name
        dependency: Dependency (default: Ang/libamgx)
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Read the Java file
    if not self.read_java_file(java_file_path):
        return False
    
    try:
        # Create the XML template
        xml_content = self.create_xml_template(
            name=name,
            version=version,
            simple_class_name=simple_class_name,
            dependency=dependency
        )
        
        # Write to output file
        with open(output_xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        return True
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

def preview(self, java_file_path, name, version, simple_class_name, dependency="Ang/libamgx"):
    """Preview the XML output without saving to file"""
    if not self.read_java_file(java_file_path):
        return None
    
    try:
        xml_content = self.create_xml_template(
            name=name,
            version=version,
            simple_class_name=simple_class_name,
            dependency=dependency
        )
        return xml_content
    except Exception as e:
        print(f"Error during preview: {e}")
        return None
```

def convert_java_to_xml_template(java_file_path,
output_xml_path=None,
name=“MyComponent”,
version=“1.0.0”,
simple_class_name=“MyClass”,
dependency=“Ang/libamgx”,
preview_only=False):
“””
Convert Java code to XML template with custom structure

```
Args:
    java_file_path: Path to Java source file
    output_xml_path: Output XML path (auto-generated if None)
    name: Component name for XML template
    version: Version string for XML template
    simple_class_name: Simple class name for XML template
    dependency: Dependency string (default: Ang/libamgx)
    preview_only: If True, only preview without creating file

Returns:
    bool: Success status
"""

# Auto-generate output path if not provided
if output_xml_path is None:
    base_name = os.path.splitext(os.path.basename(java_file_path))[0]
    output_xml_path = f"{base_name}.xml"

# Create converter instance
converter = JavaToXMLTemplateConverter()

if preview_only:
    # Preview mode
    xml_content = converter.preview(
        java_file_path, name, version, simple_class_name, dependency
    )
    if xml_content:
        print("=" * 60)
        print("XML TEMPLATE PREVIEW:")
        print("=" * 60)
        print(xml_content)
        print("=" * 60)
        return True
    return False
else:
    # Full conversion
    success = converter.convert(
        java_file_path, output_xml_path, 
        name, version, simple_class_name, dependency
    )
    if success:
        print(f"✓ Conversion completed successfully!")
        print(f"  Input:  {java_file_path}")
        print(f"  Output: {output_xml_path}")
        print(f"  Component Name: {name}")
        print(f"  Version: {version}")
        print(f"  Class: {simple_class_name}")
        return True
    else:
        print("✗ Conversion failed!")
        return False
```

# ============================================================================

# USAGE EXAMPLES

# ============================================================================

# Example 1: Simple usage with all parameters

def example_simple():
convert_java_to_xml_template(
java_file_path=“MyClass.java”,
output_xml_path=“output/MyClass.xml”,
name=“MyCustomComponent”,
version=“2.1.0”,
simple_class_name=“MyClass”,
dependency=“Ang/libamgx”  # This is the default
)

# Example 2: Interactive mode

def interactive_mode():
“”“Interactive mode with user prompts”””
print(“Java to XML Template Converter”)
print(”-” * 40)

```
# Get Java file
java_file = input("Enter Java file path: ").strip()
if not os.path.exists(java_file):
    print(f"Error: File '{java_file}' not found!")
    return False

# Get component details
name = input("Enter component name: ").strip()
if not name:
    name = "DefaultComponent"

version = input("Enter version (e.g., 1.0.0): ").strip()
if not version:
    version = "1.0.0"

simple_class = input("Enter simple class name: ").strip()
if not simple_class:
    # Try to extract from filename
    simple_class = os.path.splitext(os.path.basename(java_file))[0]

dependency = input("Enter dependency (press Enter for 'Ang/libamgx'): ").strip()
if not dependency:
    dependency = "Ang/libamgx"

output_file = input("Enter output XML path (press Enter for auto): ").strip()
if not output_file:
    output_file = None

preview = input("Preview only? (y/n): ").strip().lower() == 'y'

# Run conversion
return convert_java_to_xml_template(
    java_file_path=java_file,
    output_xml_path=output_file,
    name=name,
    version=version,
    simple_class_name=simple_class,
    dependency=dependency,
    preview_only=preview
)
```

# Example 3: Batch processing

def batch_convert(java_files_config):
“””
Convert multiple Java files with their configurations

```
Args:
    java_files_config: List of dictionaries with file configurations
"""
results = []
for config in java_files_config:
    print(f"\nProcessing: {config['java_file']}")
    success = convert_java_to_xml_template(**config)
    results.append((config['java_file'], success))

# Summary
print("\n" + "=" * 50)
print("BATCH CONVERSION SUMMARY:")
for file, success in results:
    status = "✓ Success" if success else "✗ Failed"
    print(f"  {file}: {status}")
print("=" * 50)
```

# Example 4: Main entry point with configuration

if **name** == “**main**”:

```
# Configuration - MODIFY THESE VALUES
config = {
    "java_file_path": "src/MyApplication.java",  # <- Your Java file
    "output_xml_path": "output/MyApplication.xml",  # <- Output location
    "name": "MyApplicationComponent",  # <- Your component name
    "version": "1.5.2",  # <- Your version
    "simple_class_name": "MyApplication",  # <- Your class name
    "dependency": "Ang/libamgx",  # <- Keep default or change
    "preview_only": False  # <- Set True to preview only
}

# Run conversion with configuration
success = convert_java_to_xml_template(**config)

# Or run interactive mode
# interactive_mode()

# Or batch convert multiple files
# batch_files = [
#     {
#         "java_file_path": "Class1.java",
#         "name": "Component1",
#         "version": "1.0.0",
#         "simple_class_name": "Class1"
#     },
#     {
#         "java_file_path": "Class2.java",
#         "name": "Component2",
#         "version": "2.0.0",
#         "simple_class_name": "Class2"
#     }
# ]
# batch_convert(batch_files)
```
