import re

def replace_tenor_value(xml_content, new_tenor, new_value):
    # Pattern to match the Borrow section and capture parts
    pattern = r'(<Borrow>.*?<Tenor>).*?(</Tenor>.*?<Value>).*?(</Value>.*?</Borrow>)'
    
    # Find and replace
    def replacement(match):
        before_tenor = match.group(1)  # Everything up to and including <Tenor>
        between_tags = match.group(2)  # </Tenor> to <Value>
        after_value = match.group(3)   # </Value> and everything after
        
        return f"{before_tenor}{new_tenor}{between_tags}{new_value}{after_value}"
    
    result = re.sub(pattern, replacement, xml_content, flags=re.DOTALL)
    return result

# Example usage
xml_content = """<Borrow>
<Tag1>some content</Tag1>
<Tenor>old_tenor_value</Tenor>
<Value>old_value_content</Value>
<Tag2>more content</Tag2>
</Borrow>"""

new_tenor = "new_tenor_value"
new_value = "new_value_content"

updated_xml = replace_tenor_value(xml_content, new_tenor, new_value)
print(updated_xml)
