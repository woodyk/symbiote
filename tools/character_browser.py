#!/usr/bin/env python3
#
# character_browser.py

import unicodedata
import os

def clear_console():
    """Clear the console screen for better display."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_unicode_block(start, end):
    """Generate characters from the given Unicode range."""
    return [(chr(i), f"U+{i:04X}") for i in range(start, end + 1) if chr(i).isprintable()]

def display_table(characters, columns=10):
    """Display characters in a table format."""
    rows = [characters[i:i + columns] for i in range(0, len(characters), columns)]
    for row in rows:
        char_row = " | ".join([f"{ch[0]:^4}" for ch in row])
        code_row = " | ".join([f"{ch[1]:^6}" for ch in row])
        print(char_row)
        print(code_row)
        print("-" * len(char_row))

def main():
    print("Character Set Viewer")
    print("You can browse Unicode characters by specifying a range or browsing predefined blocks.\n")
    
    while True:
        print("Options:")
        print("1. Enter Unicode range (e.g., 4E00-9FFF for Chinese characters).")
        print("2. Exit.")
        choice = input("Select an option: ").strip()

        if choice == "1":
            try:
                unicode_range = input("Enter the Unicode range (e.g., 4E00-9FFF): ").strip()
                start, end = (int(part, 16) for part in unicode_range.split('-'))
                characters = get_unicode_block(start, end)
                if not characters:
                    print("No characters found in the specified range.")
                    continue
                
                columns = int(input("Enter the number of columns for display (default 10): ") or "10")
                clear_console()
                print(f"Displaying characters from U+{start:04X} to U+{end:04X}:\n")

                page = 0
                page_size = 50
                while True:
                    start_idx = page * page_size
                    end_idx = start_idx + page_size
                    display_table(characters[start_idx:end_idx], columns)
                    
                    if end_idx >= len(characters):
                        print("\nEnd of range.")
                        break

                    nav = input("\nPress [Enter] for next page, 'b' for previous page, or 'q' to quit: ").strip().lower()
                    if nav == 'q':
                        break
                    elif nav == 'b' and page > 0:
                        page -= 1
                    else:
                        page += 1
            except ValueError:
                print("Invalid range or input. Please try again.")
        elif choice == "2":
            print("Exiting. Goodbye!")
            break
        else:
            print("Invalid option. Please select again.")

if __name__ == "__main__":
    main()

