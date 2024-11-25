#!/usr/bin/env python3
#
# character_tui_analysis.py

import unicodedata

def generate_box_pattern(char):
    """
    Generate a simple box pattern using a specific character.

    Args:
        char (str): A single character to use in the box pattern.

    Returns:
        str: The generated box pattern as a string.
    """
    box_pattern = (
        f"{char*3}{char*2}{char*3}\n"
        f"{char}   {char}\n"
        f"{char*3}{char*2}{char*3}\n"
        f"{char}   {char}\n"
        f"{char*3}{char*2}{char*3}\n"
    )
    return box_pattern


def generate_panel_pattern(char, width=40, height=10):
    """
    Generate a panel with custom dimensions using a specific character.

    Args:
        char (str): A single character to use in the panel.
        width (int): Width of the panel (minimum 10).
        height (int): Height of the panel (minimum 5).

    Returns:
        tuple: A tuple containing the panel as a string and its Python-formatted definition.
    """
    # Ensure minimum dimensions
    width = max(width, 10)
    height = max(height, 5)

    # Panel components
    top_border = f"{char}─{char * (width - 4)}─{char}"
    bottom_border = f"{char}─{char * (width - 4)}─{char}"
    middle_row = f"{char} {' ' * (width - 4)} {char}"

    # Generate panel
    panel = [top_border]
    for _ in range(height - 2):
        panel.append(middle_row)
    panel.append(bottom_border)

    # Format panel into a single string
    panel_str = "\n".join(panel)

    # Python-formatted pattern
    python_pattern = 'Panel = """\n' + panel_str + '\n"""'

    return panel_str, python_pattern


def is_valid_unicode_character(codepoint):
    """
    Check if a Unicode character is valid for use in patterns.

    Args:
        codepoint (int): The Unicode codepoint.

    Returns:
        bool: True if the character is valid, False otherwise.
    """
    try:
        char = chr(codepoint)
        if unicodedata.category(char) in ["Cc", "Cf", "Cs", "Cn", "Zs"]:
            return False
        return True
    except Exception:
        return False


def test_panel_output(panel, python_pattern, char, name):
    """
    Display the panel and its Python-formatted definition for visual inspection.

    Args:
        panel (str): The rendered panel.
        python_pattern (str): The Python-formatted panel definition.
        char (str): The character used to generate the panel.
        name (str): The Unicode name of the character.
    """
    print("\n" + "=" * 10 + f" Panel Rendered for '{char}' ({name}) " + "=" * 10)
    print(panel)
    print("\n" + "=" * 10 + " Python Pattern " + "=" * 10)
    print(python_pattern)
    print("=" * 30)


def crawl_unicode_and_generate_panels(start=32, end=1114111, width=40, height=10, limit=None, save_to_file=False):
    """
    Crawl through Unicode characters and generate panels with custom dimensions.

    Args:
        start (int): Starting Unicode codepoint.
        end (int): Ending Unicode codepoint.
        width (int): Width of the panel.
        height (int): Height of the panel.
        limit (int): Maximum number of panels to generate (None for no limit).
        save_to_file (bool): Whether to save the panels to a file.
    """
    count = 0
    panels_data = []

    for codepoint in range(start, end + 1):
        if limit and count >= limit:
            break

        if is_valid_unicode_character(codepoint):
            char = chr(codepoint)
            name = unicodedata.name(char, "Unknown Name")
            try:
                panel, python_pattern = generate_panel_pattern(char, width, height)
                test_panel_output(panel, python_pattern, char, name)
                panels_data.append({"character": char, "name": name, "panel": panel, "pattern": python_pattern})
                count += 1
            except Exception as e:
                print(f"Error generating panel for {repr(char)}: {e}")

    if save_to_file:
        with open("unicode_panels.txt", "w", encoding="utf-8") as file:
            for panel_info in panels_data:
                file.write(f"Character: {panel_info['character']} ({panel_info['name']})\n")
                file.write(panel_info["panel"] + "\n\n")
        print("Panels saved to unicode_panels.txt")


if __name__ == "__main__":
    # Default range: All Unicode characters
    start_unicode = 32  # Space
    end_unicode = 1114111  # Maximum Unicode codepoint

    # Default panel dimensions
    panel_width = 40
    panel_height = 10

    # Limit for the number of panels to display
    panel_limit = None  # Set to a number to limit, or None for no limit

    # Save output to a file
    save_panels = True

    print("Crawling Unicode characters to generate panels...")
    crawl_unicode_and_generate_panels(
        start=start_unicode,
        end=end_unicode,
        width=panel_width,
        height=panel_height,
        limit=panel_limit,
        save_to_file=save_panels,
    )

