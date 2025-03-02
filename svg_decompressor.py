import base64
import zlib
import json
import xml.etree.ElementTree as ET

#%% Useful functions
def load_json(file_path): # Load decompressed JSON
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

def save_json(data, output_file): # Save extracted data to JSON
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

# %% Remove nulls from dictionary
def remove_nulls(d):
    """Recursively removes null (None) values from a dictionary or list, but keeps empty structures."""
    if isinstance(d, dict):
        return {k: remove_nulls(v) for k, v in d.items() if v is not None}
    elif isinstance(d, list):
        return [remove_nulls(v) for v in d]
    return d


# %% Decompress SVG
def decompress_svg(encoded):
    encoded = encoded.replace('-', '+').replace('_', '/')
    decoded_bytes = base64.b64decode(encoded)

    for wbits in [15, -15, 31]:
        try:
            decompressed_svg = zlib.decompress(decoded_bytes, wbits=wbits)
            break
        except Exception:
            continue

    return decompressed_svg.decode("utf-8")


# %% Extract player info
def extract_player_info(xml_root):
    """Extracts player class, ascendancy, and level."""
    player_info = {
        "level": "Unknown",
        "class": "Unknown",
        "ascendancy": "Unknown"
    }

    build_section = xml_root.find(".//Build")
    if build_section is not None:
        nested_build = build_section.find(".//Build")
        if nested_build is not None:
            attributes = nested_build.attrib
        else:
            attributes = build_section.attrib

        player_info["level"] = attributes.get("level", "Unknown")
        player_info["class"] = attributes.get("className", "Unknown")
        player_info["ascendancy"] = attributes.get("ascendClassName", "Unknown")

    return player_info


# %% Extract player stats
def extract_player_stats(xml_root):
    """Extracts player stats as a dictionary."""
    stats_dict = {}
    for stat in xml_root.findall(".//PlayerStat"):
        stat_name = stat.attrib.get("stat", "Unknown Stat")
        stat_value = stat.attrib.get("value", "Unknown")
        if stat_name != "Unknown Stat":
            stats_dict[stat_name] = stat_value
    return stats_dict


# %% Extract passive tree
def extract_passive_tree(xml_root):
    """Extracts passive skill tree data."""
    passive_tree = {
        "nodes": [],
    }

    tree_section = xml_root.find(".//Tree")
    if tree_section is None:
        return passive_tree

    spec_element = tree_section.find(".//Spec")
    if spec_element is None:
        return passive_tree

    nodes_attr = spec_element.attrib.get("nodes", "")
    if nodes_attr:
        passive_tree["nodes"] = nodes_attr.split(",")

    return passive_tree


# %% Extract skills
def extract_skills(xml_root):
    """Extracts skills and their socketed gems."""
    skills = []
    skills_section = xml_root.find(".//Skills")
    if skills_section is None:
        return skills

    for skill in skills_section.findall(".//Skill"):
        skill_attrs = skill.attrib
        skill_label = skill_attrs.get("label", skill.text.strip() if skill.text else "Unknown Skill")
        skill_data = {
            "label": skill_label,
            "enabled": skill_attrs.get("enabled", "false"),
            "gems": []
        }
        for gem in skill.findall(".//Gem"):
            gem_attrs = gem.attrib
            skill_data["gems"].append({
                "name": gem_attrs.get("nameSpec", "Unknown Gem"),
                "level": gem_attrs.get("level", "Unknown"),
                "quality": gem_attrs.get("quality", "Unknown"),
                "enabled": gem_attrs.get("enabled", "false")
            })
        skills.append(skill_data)
    return skills


# %% Extract items
def extract_items(xml_root):
    """Extracts item data from the decompressed XML file."""
    structured_items = []
    for item in xml_root.findall(".//Items/Item"):
        item_attrs = item.attrib
        item_data = {
            "id": item_attrs.get("id", "Unknown"),
            "name": "Unknown",
            "rarity": item_attrs.get("rarity", "Unknown"),
            "level": item_attrs.get("level", "Unknown"),
            "quality": item_attrs.get("quality", "Unknown"),
            "sockets": item_attrs.get("sockets", "None"),
            "details": []
        }
        item_text = item.text.strip() if item.text else ""
        item_data["details"] = item_text.split("\n") if item_text else []
        item_data["name"] = item_data["details"][0] if item_data["details"] else "Unknown"
        structured_items.append(item_data)
    return structured_items


# %% Decompress SVG, Parse XML, Save to JSON/XML
def decompress_and_parse(file_path):
    with open(file_path, "r") as file:
        encoded = file.read().strip()

    decompressed_file = decompress_svg(encoded)

    root = ET.fromstring(decompressed_file)
    parsed_data = {
        "PathOfBuilding2": {
            "PlayerInfo": extract_player_info(root),
            "PlayerStats": extract_player_stats(root),
            "PassiveTree": extract_passive_tree(root),
            "Skills": extract_skills(root),
            "Items": extract_items(root)
        }
    }

    save_json(parsed_data, "decompressed_build.json")

#%% Simplification of the structure
def extract_data(decompressed_data): # Extract and structure the data
    structured_data = {
        "PlayerInfo": decompressed_data["PathOfBuilding2"].get("PlayerInfo", {}),
        "PlayerStats": decompressed_data["PathOfBuilding2"].get("PlayerStats", {}),
        "PassiveTree": decompressed_data["PathOfBuilding2"].get("PassiveTree", {}),
        "Skills": decompressed_data["PathOfBuilding2"].get("Skills", []),
        "Items": decompressed_data["PathOfBuilding2"].get("Items", [])
    }
    return structured_data

#%% Main
if __name__ == "__main__":
    decompress_and_parse("build.txt")

    input_file = "decompressed_build.json"
    output_file = "structured_build.json"

    decompressed_data = load_json(input_file)
    structured_data = extract_data(decompressed_data)
    save_json(structured_data, output_file)

    print(f"Structured data saved to {output_file}")