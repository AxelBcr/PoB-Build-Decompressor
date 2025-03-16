import base64
import os
import zlib
import json
import xml.etree.ElementTree as ET
import re

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
        item_text = item.text.strip() if item.text else ""
        item_lines = item_text.split("\n") if item_text else []

        def extract_attr(attr_name):
            for line in item_lines:
                if attr_name in line:
                    return line.split(": ")[-1].strip()
            return "Unknown"

        item_data = {
            "id": item_attrs.get("id", "Unknown"),
            "name": item_lines[1] if len(item_lines) > 1 else "Unknown",  # Extract actual item name
            "type": item_lines[2] if len(item_lines) > 2 else "Unknown",  # Extract item type
            "rarity": item_lines[0] if len(item_lines) > 0 else "Unknown",  # Extract Rarity
            "level": extract_attr("Item Level"),
            "required_level": extract_attr("LevelReq"),
            "quality": extract_attr("Quality"),
            "sockets": extract_attr("Sockets"),
            "rune": extract_attr("Rune"),
            "modifiers": [line for line in item_lines if not any(
                kw in line for kw in [item_lines[0], item_lines[1], item_lines[2],
                "Item Level", "Quality", "Sockets", "Rarity", "LevelReq", "Rune"])]
        }
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

#%% Extract nodes from tree files
def extract_nodes_as_list(filename):
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    # Locate the nodes block.
    start_marker = "nodes={"
    start_index = content.find(start_marker)
    if start_index == -1:
        print("Could not find 'nodes={' in the file.")
        return {}
    parse_start = start_index + len(start_marker)

    # Use brace counting to extract the entire nodes block.
    brace_count = 1
    pos = parse_start
    while pos < len(content) and brace_count > 0:
        if content[pos] == '{':
            brace_count += 1
        elif content[pos] == '}':
            brace_count -= 1
        pos += 1

    nodes_block = content[parse_start: pos - 1].strip()

    node_dict = {}
    idx = 0
    pattern_entry = r"\[(\d+)\]\s*=\s*\{"
    while True:
        m = re.search(pattern_entry, nodes_block[idx:])
        if not m:
            break  # no more node entries
        # Table key (not used) is m.group(1)
        node_start = idx + m.end()  # position just after the opening '{'
        brace_count = 1
        pos2 = node_start
        while pos2 < len(nodes_block) and brace_count > 0:
            if nodes_block[pos2] == '{':
                brace_count += 1
            elif nodes_block[pos2] == '}':
                brace_count -= 1
            pos2 += 1
        node_content = nodes_block[node_start: pos2 - 1]

        # Extract the "skill" field (node id) and "name" field.
        skill_match = re.search(r"\bskill\s*=\s*(\d+)", node_content)
        name_match = re.search(r'\bname\s*=\s*"([^"]+)"', node_content)

        # Extract stats block if present.
        stats_list = []
        stats_match = re.search(r"\bstats\s*=\s*\{(.*?)\}", node_content, re.DOTALL)
        if stats_match:
            stats_block = stats_match.group(1)
            stats_list = re.findall(r'"([^"]+)"', stats_block)

        if skill_match and name_match:
            skill_id = int(skill_match.group(1))
            node_name = name_match.group(1)
            # Store as [name, stat] where stat is the list of stats.
            node_dict[skill_id] = [node_name, stats_list]
        # Move idx past this node entry.
        idx = node_start + len(node_content)

    return node_dict

#%% ID transform for passive tree
def id_transform(nodes_data):

    # Load structured_build.json
    with open("structured_build.json", "r") as build_file:
        build_data = json.load(build_file)

    # Extract Passive Tree Nodes
    passive_tree_nodes = build_data.get("PassiveTree", {}).get("nodes", [])

    # Create the mapping dictionary
    node_mapping = {}
    for node_id in passive_tree_nodes:
        node_id_str = int(node_id)  # Convert to string for consistency with nodes.json keys
        if node_id_str in nodes_data.keys():
            node_name = nodes_data[node_id_str][0]
            node_stats = nodes_data[node_id_str][1]
            node_mapping[node_id_str] = [node_name, node_stats]
        else:
            node_mapping[node_id_str] = ["Unknown", []]  # Handle missing nodes

    # Replace nodes structure in structured_build.json
    build_data["PassiveTree"]["nodes"] = node_mapping

    # Save the updated structured_build.json
    with open("structured_build.json", "w") as out_file:
        json.dump(build_data, out_file, indent=4)

#%% Main
if __name__ == "__main__":
    # Decompress and parse build.txt, then save to structured_build.json
    decompress_and_parse("build.txt")

    input_file = "decompressed_build.json" #Please don't change
    output_file = "structured_build.json" #Please don't change

    decompressed_data = load_json(input_file)
    structured_data = extract_data(decompressed_data)
    save_json(structured_data, output_file)

    os.remove(input_file) # Remove decompressed file

    # Load nodes and save to nodes.json
    nodes = extract_nodes_as_list("tree.lua")

    # ID transform for passive tree
    id_transform(nodes)

    print(f"Structured data saved to {output_file}")
