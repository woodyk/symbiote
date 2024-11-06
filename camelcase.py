#!/usr/bin/env python3
#
# camelcase.py

import sys
import re
import os

def to_camel_case(name):
    """Convert a snake_case name to camelCase without capitalizing the first character."""
    parts = name.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])

def process_file(file_path):
    """Read the file, modify function names with underscores (that don't start with '_'),
       and replace calls to the modified function names."""
    modified_lines = []
    function_name_mapping = {}

    with open(file_path, 'r') as file:
        for line in file:
            # Match lines with function definitions
            match = re.match(r'^(\s*)def (\w+)\(', line)
            if match:
                # Extract indentation and function name
                indentation, func_name = match.groups()
                # Check if function name contains underscores and does not start with '_'
                if '_' in func_name and not func_name.startswith('_'):
                    # Convert function name to camel case if it meets criteria
                    camel_case_name = to_camel_case(func_name)
                    # Replace the function name in the line
                    line = line.replace(f'def {func_name}(', f'def {camel_case_name}(')
                    # Store the old and new function names for later replacements
                    function_name_mapping[func_name] = camel_case_name
            modified_lines.append(line)

    # Replace calls to the modified function names
    modified_content = ''.join(modified_lines)
    for old_name, new_name in function_name_mapping.items():
        # Match calls to the function (outside of definitions)
        modified_content = re.sub(rf'\b{old_name}\b', new_name, modified_content)

    return modified_content.splitlines(keepends=True)

def write_modified_file(file_path, modified_lines):
    """Write modified lines to a new file with '_camel_case' appended to the filename."""
    base, ext = os.path.splitext(file_path)
    new_file_path = f"{base}_camel_case{ext}"
    with open(new_file_path, 'w') as file:
        file.writelines(modified_lines)
    print(f"Modified file written to: {new_file_path}")

def main():
    # Check if filename was provided as a command-line argument
    if len(sys.argv) != 2:
        print("Usage: python script_name.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    # Check if the provided path is a valid .py file
    if not file_path.endswith('.py') or not os.path.isfile(file_path):
        print("Please provide a valid .py file path.")
        sys.exit(1)

    # Process the file
    modified_lines = process_file(file_path)
    # Write the modified content to a new file
    write_modified_file(file_path, modified_lines)

if __name__ == "__main__":
    main()

