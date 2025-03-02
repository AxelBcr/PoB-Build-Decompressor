# SVG Decompressor

## Special Note
This script was created to decompress SVG-encoded files from Path of Building. The main goal is to transform the data into something understandable to any algorithm, AI, or learning model... (but you can use it as you want !)

## Overview
This Python script decompresses a base64-encoded and zlib-compressed SVG file, parses its XML structure, and saves both the XML and a JSON representation of the data. It reads the encoded data from `build.txt`, decodes and decompresses it, parses the XML structure, removes null values, and saves the results into `decompressed_build.xml` and `decompressed_build.json`.

## Features
- Reads compressed and base64-encoded SVG data from a file
- Decodes the base64 string
- Attempts to decompress using multiple `wbits` values for robustness
- Converts XML to a structured dictionary while handling attributes and multiple child elements
- Filters out null values from the parsed XML data
- Saves the decompressed SVG content into an XML file
- Saves the structured XML data into a JSON file

## Installation
Ensure you have Python 3 installed, then clone the repository and navigate to the project directory:

```sh
git clone https://github.com/yourusername/svg-decompressor.git
cd svg-decompressor
```

## Usage
1. Place the base64-encoded compressed SVG data inside a file named `build.txt`.
2. Run the script:

```sh
python svg_decompressor.py
```

3. The decompressed SVG content will be saved in `decompressed_build.xml`, and its structured representation will be saved in `decompressed_build.json`.

## Dependencies
This script uses only standard Python libraries:
- `base64` for decoding
- `zlib` for decompression
- `json` for saving structured data
- `xml.etree.ElementTree` for XML parsing

No external dependencies are required.  

No advanced libraries are used, ensuring compatibility with AI models and environments that may have dependency restrictions.

## Code Explanation
- `remove_nulls(d)`: Recursively removes `None`, empty lists, and empty dictionaries from a data structure.
- `xml_to_dict(element)`: Converts an XML tree into a structured dictionary while handling attributes and multiple child elements.
- `decompress_svg(encoded)`:
  - Replaces URL-safe base64 characters.
  - Decodes base64 data.
  - Attempts to decompress using different `wbits` values (15, -15, 31) to handle variations in zlib compression.
- The script reads the encoded string from `build.txt`, decompresses it, parses it as XML, removes null values, and writes the output to `decompressed_build.xml` and `decompressed_build.json`.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss your ideas.

## Contact
For any questions or suggestions, feel free to reach out or open an issue on GitHub.  
Creator : [Axel Bouchaud--Roche](https://github.com/AxelBcr)
