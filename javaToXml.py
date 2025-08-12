# Java to XML Template Converter for Jupyter Notebook
# Converts Java code to be embedded in XML template for C++ library consumption

import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
from typing import Optional, List
from IPython.display import display, HTML, Code
import ipywidgets as widgets
from pathlib import Path

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
            print(f"✅ Successfully read Java file: {java_file_path}")
            return True
        except FileNotFoundError:
            print(f"❌ Error: Java file '{java_file_path}' not found")
            return False
        except Exception as e:
            print(f"❌ Error reading Java file: {e}")
            return False
    
    def read_java_from_string(self, java_code: str):
        """Read Java code from string (useful for notebook cells)"""
        self.java_code = java_code
        print("✅ Java code loaded from string")
    
    def escape_for_xml(self, code: str) -> str:
        """Escape Java code for XML embedding"""
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
        lines = code.split('\n')
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import '):
                # Keep only essential imports
                if any(allowed in stripped for allowed in [
                    'java.util.List',
                    'java.util.ArrayList', 
                    'java.util.Map',
                    'java.util.HashMap',
                    'java.lang.String',
                    'java.lang.Integer',
                    'java.util.Arrays'
                ]):
                    filtered_lines.append(line)
            else:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def wrap_in_class_if_needed(self, code: str) -> str:
        """Wrap standalone methods in a class if needed"""
        if re.search(r'\bclass\s+\w+', code):
            return code
        
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
        """Add compilation hints for C++ library"""
        hints = "// Generated for C++ library integration\n"
        hints += "// Ensure all methods are public and static if needed\n\n"
        return hints + code
    
    def process_java_code(self) -> str:
        """Apply all modifications to the Java code"""
        if not self.java_code:
            raise ValueError("No Java code loaded")
        
        modified = self.java_code
        modified = self.remove_package_declaration(modified)
        modified = self.modify_imports(modified)
        modified = self.wrap_in_class_if_needed(modified)
        modified = self.add_compilation_hints(modified)
        
        self.modified_code = modified
        return modified
    
    def create_xml_template(self, java_code: str, 
                          library_name: str = "DefaultLibrary",
                          version: str = "1.0") -> str:
        """Create XML template with embedded Java code"""
        
        escaped_code = self.escape_for_xml(java_code)
        
        root = ET.Element("cppLibraryConfig")
        root.set("version", version)
        
        lib_info = ET.SubElement(root, "libraryInfo")
        ET.SubElement(lib_info, "name").text = library_name
        ET.SubElement(lib_info, "version").text = version
        
        java_config = ET.SubElement(root, "javaConfiguration")
        
        scripted_section = ET.SubElement(java_config, "scriptedJavaTemplate")
        scripted_section.text = escaped_code
        
        compile_options = ET.SubElement(java_config, "compileOptions")
        ET.SubElement(compile_options, "classpath").text = "."
        ET.SubElement(compile_options, "sourceVersion").text = "1.8"
        ET.SubElement(compile_options, "targetVersion").text = "1.8"
        
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def save_xml_file(self, xml_content: str, output_path: str) -> bool:
        """Save the XML content to file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(xml_content)
            print(f"✅ XML file saved successfully: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving XML file: {e}")
            return False
    
    def display_preview(self):
        """Display a preview of the modified Java code in Jupyter"""
        if not self.modified_code:
            print("❌ No processed code available. Run process_java_code() first.")
            return
        
        print("🔍 MODIFIED JAVA CODE PREVIEW:")
        print("=" * 60)
        display(Code(self.modified_code, language='java'))
        print("=" * 60)
    
    def display_xml_preview(self, xml_content: str):
        """Display a preview of the XML in Jupyter"""
        print("🔍 XML TEMPLATE PREVIEW:")
        print("=" * 60)
        display(Code(xml_content, language='xml'))
        print("=" * 60)
    
    def convert_from_file(self, java_file_path: str, xml_output_path: str = None, 
                         library_name: str = "DefaultLibrary", 
                         show_preview: bool = True) -> bool:
        """Convert from Java file with Jupyter-friendly output"""
        if not self.read_java_file(java_file_path):
            return False
        
        return self._complete_conversion(xml_output_path, library_name, show_preview, java_file_path)
    
    def convert_from_string(self, java_code: str, xml_output_path: str = None,
                           library_name: str = "DefaultLibrary",
                           show_preview: bool = True) -> bool:
        """Convert from Java code string with Jupyter-friendly output"""
        self.read_java_from_string(java_code)
        return self._complete_conversion(xml_output_path, library_name, show_preview)
    
    def _complete_conversion(self, xml_output_path: str, library_name: str, 
                           show_preview: bool, java_file_path: str = None) -> bool:
        """Complete the conversion process"""
        try:
            processed_code = self.process_java_code()
            
            if show_preview:
                self.display_preview()
            
            xml_content = self.create_xml_template(processed_code, library_name, "1.0")
            
            if show_preview:
                self.display_xml_preview(xml_content)
            
            if xml_output_path:
                return self.save_xml_file(xml_content, xml_output_path)
            else:
                if java_file_path:
                    base_name = os.path.splitext(os.path.basename(java_file_path))[0]
                    default_output = f"{base_name}.xml"
                else:
                    default_output = "output.xml"
                
                print(f"💡 No output path specified. You can save manually to '{default_output}'")
                return True
                
        except Exception as e:
            print(f"❌ Error during conversion: {e}")
            return False

# Convenience functions for quick usage in Jupyter

def convert_java_file(java_file_path: str, xml_output_path: str = None, 
                     library_name: str = "DefaultLibrary", show_preview: bool = True):
    """Quick function to convert a Java file"""
    converter = JavaToXMLConverter()
    return converter.convert_from_file(java_file_path, xml_output_path, library_name, show_preview)

def convert_java_code(java_code: str, xml_output_path: str = None,
                     library_name: str = "DefaultLibrary", show_preview: bool = True):
    """Quick function to convert Java code from string"""
    converter = JavaToXMLConverter()
    return converter.convert_from_string(java_code, xml_output_path, library_name, show_preview)

def create_interactive_converter():
    """Create an interactive widget for the converter"""
    
    # Widgets
    java_code_input = widgets.Textarea(
        value='public class Example {\n    public static void main(String[] args) {\n        System.out.println("Hello World!");\n    }\n}',
        placeholder='Paste your Java code here...',
        description='Java Code:',
        layout=widgets.Layout(width='100%', height='200px')
    )
    
    library_name_input = widgets.Text(
        value='MyLibrary',
        description='Library Name:',
        style={'description_width': 'initial'}
    )
    
    output_path_input = widgets.Text(
        value='output.xml',
        description='Output Path:',
        style={'description_width': 'initial'}
    )
    
    convert_button = widgets.Button(
        description='Convert',
        button_style='primary',
        icon='play'
    )
    
    output_area = widgets.Output()
    
    def on_convert_click(b):
        with output_area:
            output_area.clear_output()
            java_code = java_code_input.value
            library_name = library_name_input.value
            output_path = output_path_input.value if output_path_input.value.strip() else None
            
            if not java_code.strip():
                print("❌ Please enter some Java code")
                return
            
            convert_java_code(java_code, output_path, library_name, show_preview=True)
    
    convert_button.on_click(on_convert_click)
    
    # Layout
    ui = widgets.VBox([
        widgets.HTML("<h3>📝 Java to XML Converter</h3>"),
        java_code_input,
        widgets.HBox([library_name_input, output_path_input]),
        convert_button,
        output_area
    ])
    
    return ui

# Display usage instructions
print("🚀 Java to XML Converter for Jupyter Notebook")
print("=" * 50)
print("Available functions:")
print("1. convert_java_file(file_path, [output_path], [library_name])")
print("2. convert_java_code(java_code_string, [output_path], [library_name])")
print("3. create_interactive_converter() - Returns interactive widget")
print("\nExample usage:")
print("converter = JavaToXMLConverter()")
print("converter.convert_from_file('MyClass.java')")
