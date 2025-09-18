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
