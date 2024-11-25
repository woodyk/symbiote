#!/usr/bin/env python3
#
# unicode-tool.py

import unicodedata

def get_all_unicode_blocks():
    """Generate all Unicode blocks and their ranges."""
    unicode_blocks = {}
    current_block = None
    start_codepoint = None

    for codepoint in range(0x110000):  # Unicode range 0x0000 to 0x10FFFF
        try:
            block = unicodedata.name(chr(codepoint)).split(" ")[0]
        except ValueError:
            block = None  # Unassigned codepoints

        if block != current_block:
            if current_block is not None and start_codepoint is not None:
                unicode_blocks[current_block] = (start_codepoint, codepoint - 1)
            current_block = block
            start_codepoint = codepoint if block is not None else None

    return unicode_blocks

def list_unicode_blocks(blocks):
    """List all Unicode blocks with their ranges."""
    print("All Unicode Blocks:")
    for block, (start, end) in blocks.items():
        print(f"{block}: U+{start:04X} to U+{end:04X}")

def search_unicode_blocks(blocks, search_term):
    """Search for Unicode blocks based on a term."""
    matches = {block: (start, end) for block, (start, end) in blocks.items() if search_term.lower() in block.lower()}
    if matches:
        print(f"Blocks matching '{search_term}':")
        for block, (start, end) in matches.items():
            print(f"{block}: U+{start:04X} to U+{end:04X}")
    else:
        print(f"No matches found for '{search_term}'.")

def print_characters_in_block(block_name, blocks, columns=30):
    """Print characters in a specified Unicode block."""
    if block_name not in blocks:
        print(f"Error: Block '{block_name}' not found.")
        return
    start, end = blocks[block_name]
    characters = [chr(i) for i in range(start, end + 1) if chr(i).isprintable()]
    for i, char in enumerate(characters):
        if (i + 1) % columns == 0:
            print(char)  # Print character and move to the next line
        else:
            print(char, end=" ")  # Print character with a space
    print()

def main():
    unicode_blocks = get_all_unicode_blocks()

    while True:
        print("\nMenu:")
        print("1. List all Unicode blocks")
        print("2. Search for a Unicode block")
        print("3. Print characters in a block")
        print("4. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            list_unicode_blocks(unicode_blocks)
        elif choice == "2":
            search_term = input("Enter search term: ").strip()
            search_unicode_blocks(unicode_blocks, search_term)
        elif choice == "3":
            block_name = input("Enter block name (as listed): ").strip()
            print_characters_in_block(block_name, unicode_blocks)
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

