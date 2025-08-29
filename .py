import os

# Assuming you have the JavaToXMLConverter class defined elsewhere

# If not, you’ll need to import it or define it here

# from your_module import JavaToXMLConverter

# Direct usage without argparse

def convert_java_to_xml(java_file_path, output_xml_path=None, library_name=“DefaultLibrary”, preview_only=False):
“””
Convert Java code to XML template

```
Args:
    java_file_path: Path to the Java source file
    output_xml_path: Output XML file path (optional, will auto-generate if not provided)
    library_name: Library name for XML template
    preview_only: If True, only preview the modified code without creating XML

Returns:
    bool: True if successful, False otherwise
"""

# Determine output path if not provided
if output_xml_path is None:
    base_name = os.path.splitext(os.path.basename(java_file_path))[0]
    output_xml_path = f"{base_name}.xml"

# Create converter instance
converter = JavaToXMLConverter()

if preview_only:
    # Preview mode - just show the modified Java code
    if converter.read_java_file(java_file_path):
        try:
            processed_code = converter.process_java_code()
            print("=" * 60)
            print("MODIFIED JAVA CODE PREVIEW:")
            print("=" * 60)
            print(processed_code)
            print("=" * 60)
            return True
        except Exception as e:
            print(f"Error processing Java code: {e}")
            return False
else:
    # Full conversion
    success = converter.convert(java_file_path, output_xml_path, library_name)
    if success:
        print(f"Conversion completed successfully!")
        print(f"Input:  {java_file_path}")
        print(f"Output: {output_xml_path}")
        return True
    else:
        print("Conversion failed!")
        return False
```

# Example usage - Method 1: Simple conversion with auto-generated output filename

if **name** == “**main**”:
# Specify your Java file path here
java_file = “path/to/your/MyClass.java”  # <– Change this to your Java file path

```
# Option 1: Basic conversion (output will be MyClass.xml in same directory)
convert_java_to_xml(java_file)

# Option 2: Specify custom output path
# convert_java_to_xml(java_file, "path/to/output/custom_name.xml")

# Option 3: With custom library name
# convert_java_to_xml(java_file, "output.xml", "MyCustomLibrary")

# Option 4: Preview only (no XML file created)
# convert_java_to_xml(java_file, preview_only=True)
```

# Example usage - Method 2: More explicit control

def main_direct():
# Configuration - MODIFY THESE PATHS
JAVA_INPUT_FILE = “src/main/java/Example.java”  # <– Your Java file path
XML_OUTPUT_FILE = “output/Example.xml”          # <– Your desired output path
LIBRARY_NAME = “MyLibrary”                      # <– Your library name

```
# Create directories if needed
output_dir = os.path.dirname(XML_OUTPUT_FILE)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Run the conversion
success = convert_java_to_xml(
    java_file_path=JAVA_INPUT_FILE,
    output_xml_path=XML_OUTPUT_FILE,
    library_name=LIBRARY_NAME,
    preview_only=False  # Set to True if you just want to preview
)

if success:
    print("\n✓ Conversion successful!")
else:
    print("\n✗ Conversion failed!")

return success
```

# Example usage - Method 3: Interactive

def interactive_conversion():
“”“Interactive mode - prompts for file paths”””
print(“Java to XML Converter”)
print(”-” * 30)

```
# Get input file
java_file = input("Enter Java file path: ").strip()
if not os.path.exists(java_file):
    print(f"Error: File '{java_file}' not found!")
    return False

# Get output file (optional)
output_file = input("Enter output XML path (press Enter for auto): ").strip()
if not output_file:
    output_file = None

# Get library name
library = input("Enter library name (press Enter for 'DefaultLibrary'): ").strip()
if not library:
    library = "DefaultLibrary"

# Ask for preview
preview = input("Preview only? (y/n, default: n): ").strip().lower() == 'y'

# Run conversion
return convert_java_to_xml(java_file, output_file, library, preview)
```

# Uncomment the method you want to use:

# interactive_conversion()

# main_direct()
