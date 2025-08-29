#!/usr/bin/env python3
"""
Java to XML Template Converter
Converts Java code to be embedded in XML template for C++ library consumption
"""

import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
import os
from typing import Optional, List

class JavaToXMLConverter:
    def __init__(self):
        self.java_code = ""
        self.modified_code = ""
        self.xml_template = None
    
    def read_java_file(self, java_file_path: str) -> bool:
        """Read the Java source file"""
        try:
            with open(java_file_path, 'r', encoding='utf-8') as file:
                self.java_code = file.read()
            print(f"Successfully read Java file: {java_file_path}")
            return True
        except FileNotFoundError:
            print(f"Error: Java file '{java_file_path}' not found")
            return False
        except Exception as e:
            print(f"Error reading Java file: {e}")
            return False
    
    def escape_for_xml(self, code: str) -> str:
        """Escape Java code for XML embedding"""
        # Replace XML special characters
        code = code.replace('&', '&amp;')
        code = code.replace('<', '&lt;')
        code = code.replace('>', '&gt;')
        code = code.replace('"', '&quot;')
        code = code.replace("'", '&apos;')
        return code
    
    def remove_package_declaration(self, code: str) -> str:
        """Remove package declaration if present"""
        return re.sub(r'^\s*package\s+[^;]+;\s*\n?', '', code, flags=re.MULTILINE)
    
    def modify_imports(self, code: str) -> str:
        """Modify imports for C++ library compatibility"""
        # Remove standard Java imports that might not be available
        lines = code.split('\n')
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Keep only essential imports
            if stripped.startswith('import '):
                # You can customize this based on your C++ library's Java bindings
                if any(allowed in stripped for allowed in [
                    'java.util.List',
                    'java.util.ArrayList', 
                    'java.util.Map',
                    'java.util.HashMap',
                    'java.lang.String',
                    'java.lang.Integer'
                ]):
                    filtered_lines.append(line)
                # Skip other imports
            else:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def wrap_in_class_if_needed(self, code: str) -> str:
        """Wrap standalone methods in a class if needed"""
        # Check if code already has a class definition
        if re.search(r'\bclass\s+\w+', code):
            return code
        
        # If no class found, wrap the code
        wrapped_code = """public class ScriptedJavaCode {
    
""" + self.indent_code(code, 4) + """
    
}"""
        return wrapped_code
    
    def indent_code(self, code: str, spaces: int) -> str:
        """Add indentation to code"""
        indent = ' ' * spaces
        lines = code.split('\n')
        indented_lines = [indent + line if line.strip() else line for line in lines]
        return '\n'.join(indented_lines)
    
    def add_compilation_hints(self, code: str) -> str:
        """Add compilation hints or modifications for C++ library"""
        # Add any necessary annotations or modifications
        hints = "// Generated for C++ library integration\n"
        hints += "// Ensure all methods are public and static if needed\n\n"
        return hints + code
    
    def process_java_code(self) -> str:
        """Apply all modifications to the Java code"""
        if not self.java_code:
            raise ValueError("No Java code loaded")
        
        # Start with original code
        modified = self.java_code
        
        # Apply transformations
        modified = self.remove_package_declaration(modified)
        modified = self.modify_imports(modified)
        modified = self.wrap_in_class_if_needed(modified)
        modified = self.add_compilation_hints(modified)
        
        # Store the modified code
        self.modified_code = modified
        return modified
    
    def create_xml_template(self, java_code: str, 
                          library_name: str = "DefaultLibrary",
                          version: str = "1.0") -> str:
        """Create XML template with embedded Java code"""
        
        # Escape the Java code for XML
        escaped_code = self.escape_for_xml(java_code)
        
        # Create XML structure
        root = ET.Element("cppLibraryConfig")
        root.set("version", version)
        
        # Library info
        lib_info = ET.SubElement(root, "libraryInfo")
        ET.SubElement(lib_info, "name").text = library_name
        ET.SubElement(lib_info, "version").text = version
        
        # Java configuration
        java_config = ET.SubElement(root, "javaConfiguration")
        
        # Scripted Java template section
        scripted_section = ET.SubElement(java_config, "scriptedJavaTemplate")
        scripted_section.text = escaped_code
        
        # Additional configuration options
        compile_options = ET.SubElement(java_config, "compileOptions")
        ET.SubElement(compile_options, "classpath").text = "."
        ET.SubElement(compile_options, "sourceVersion").text = "1.8"
        ET.SubElement(compile_options, "targetVersion").text = "1.8"
        
        # Convert to pretty-printed string
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def save_xml_file(self, xml_content: str, output_path: str) -> bool:
        """Save the XML content to file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(xml_content)
            print(f"XML file saved successfully: {output_path}")
            return True
        except Exception as e:
            print(f"Error saving XML file: {e}")
            return False
    
    def convert(self, java_file_path: str, xml_output_path: str, 
                library_name: str = "DefaultLibrary") -> bool:
        """Main conversion method"""
        # Read Java file
        if not self.read_java_file(java_file_path):
            return False
        
        # Process Java code
        try:
            processed_code = self.process_java_code()
        except Exception as e:
            print(f"Error processing Java code: {e}")
            return False
        
        # Create XML template
        xml_content = self.create_xml_template(
            processed_code, 
            library_name,
            "1.0"
        )
        
        # Save XML file
        return self.save_xml_file(xml_content, xml_output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Convert Java code to XML template for C++ library integration"
    )
    parser.add_argument("java_file", help="Path to the Java source file")
    parser.add_argument("-o", "--output", 
                       help="Output XML file path (default: <java_filename>.xml)")
    parser.add_argument("-l", "--library", default="DefaultLibrary",
                       help="Library name for XML template")
    parser.add_argument("--preview", action="store_true",
                       help="Preview the modified Java code without creating XML")
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        xml_output = args.output
    else:
        base_name = os.path.splitext(os.path.basename(args.java_file))[0]
        xml_output = f"{base_name}.xml"
    
    # Create converter
    converter = JavaToXMLConverter()
    
    if args.preview:
        # Preview mode - just show the modified Java code
        if converter.read_java_file(args.java_file):
            try:
                processed_code = converter.process_java_code()
                print("=" * 60)
                print("MODIFIED JAVA CODE PREVIEW:")
                print("=" * 60)
                print(processed_code)
                print("=" * 60)
            except Exception as e:
                print(f"Error processing Java code: {e}")
    else:
        # Full conversion
        success = converter.convert(args.java_file, xml_output, args.library)
        if success:
            print(f"Conversion completed successfully!")
            print(f"Input:  {args.java_file}")
            print(f"Output: {xml_output}")
        else:
            print("Conversion failed!")


if __name__ == "__main__":
    main()