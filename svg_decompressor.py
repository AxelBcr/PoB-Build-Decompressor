#%% Imports
import base64
import zlib
import json
import xml.etree.ElementTree as ET

#%% Remove nulls from dictionary
def remove_nulls(d):
    """Recursively removes null (None) values from a dictionary or list."""
    if isinstance(d, dict):
        return {k: remove_nulls(v) for k, v in d.items() if v not in [None, [], {}]}
    elif isinstance(d, list):
        return [remove_nulls(v) for v in d if v not in [None, [], {}]]
    return d
#%% Convert XML to dictionary
def xml_to_dict(element):
    """Recursively converts an XML element into a dictionary."""
    parsed_dict = {}

    # Store attributes
    if element.attrib:
        parsed_dict["@attributes"] = element.attrib

    # Process child elements
    children = list(element)
    if children:
        child_dict = {}
        for child in children:
            child_data = xml_to_dict(child)
            tag = child.tag

            if tag in child_dict:
                # Convert into a list if multiple elements with the same tag exist
                if isinstance(child_dict[tag], list):
                    child_dict[tag].append(child_data)
                else:
                    child_dict[tag] = [child_dict[tag], child_data]
            else:
                child_dict[tag] = child_data

        parsed_dict.update(child_dict)
    else:
        # Assign text content if it's not empty
        text_content = element.text.strip() if element.text and element.text.strip() else None
        if text_content:
            parsed_dict["@text"] = text_content

    return {element.tag: parsed_dict}
#%% Decompress SVG
def decompress_svg(encoded):
    # Replace URL-safe base64 characters with standard ones
    encoded = encoded.replace('-', '+').replace('_', '/')

    # Decode the corrected base64 string
    decoded_bytes = base64.b64decode(encoded)

    for wbits in [15, -15, 31]:
        try:
            decompressed_svg = zlib.decompress(decoded_bytes, wbits=wbits)
            break
        except Exception as e:
            print(f"Decompression failed with wbits={wbits}: {e}")

    xml_data = decompressed_svg.decode("utf-8")

    return xml_data

#%% Main : Decompress SVG, Parse XML, Save to JSON/XML
# Read the compressed SVG from the file
with open("build.txt", "r") as file:
    encoded = file.read().strip()

# Decompress the SVG and save it to a decompressed XML file
with open("decompressed_build.xml", "w") as file:
    file.write(decompress_svg(encoded))

# Parse the decompressed XML
with open("decompressed_build.xml", "r") as file:
    xml_data = file.read()

# Parse the XML string into an ElementTree
root = ET.fromstring(xml_data)  # Convert string to an XML element

parsed_data = xml_to_dict(root)  # Pass the parsed element

parsed_data = remove_nulls(parsed_data) # Remove nulls

# Save the parsed data to a JSON file
with open("decompressed_build.json", "w") as file:
    json.dump(parsed_data, file, indent=4)