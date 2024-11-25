#!/usr/bin/env python3
#
# character_browser.py

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.input.defaults import create_input
import unicodedata


class UnicodeViewer:
    def __init__(self, unicode_range_start, unicode_range_end, characters_per_page=50):
        self.console = Console()
        self.unicode_range_start = unicode_range_start
        self.unicode_range_end = unicode_range_end
        self.characters_per_page = characters_per_page
        self.current_page = 0
        self.character_list = self.generate_characters()

    def generate_characters(self):
        """Generate characters from the given Unicode range."""
        characters = []
        for code in range(self.unicode_range_start, self.unicode_range_end + 1):
            try:
                char = chr(code)
                name = unicodedata.name(char, "Unknown Character")
                characters.append((char, name))
            except ValueError:
                pass
        return characters

    def create_table(self):
        """Create a table for the current page of characters."""
        table = Table(show_header=True, header_style="bold magenta", expand=True)
        table.add_column("Character", style="cyan", no_wrap=True)
        table.add_column("Unicode Name", style="white", justify="left")

        start_index = self.current_page * self.characters_per_page
        end_index = start_index + self.characters_per_page
        characters_on_page = self.character_list[start_index:end_index]

        for char, name in characters_on_page:
            table.add_row(char, name)

        return table

    def render_panel(self):
        """Render the characters in a Rich Panel."""
        table = self.create_table()
        total_pages = (len(self.character_list) - 1) // self.characters_per_page + 1
        return Panel(
            table,
            title=f"[bold green]Unicode Viewer[/bold green] - Page {self.current_page + 1}/{total_pages}",
            border_style="blue",
        )

    def run(self):
        """Run the Unicode Viewer."""
        bindings = KeyBindings()

        @bindings.add("q")
        def quit_handler(event):
            event.app.exit()

        @bindings.add("j")
        def next_page(event):
            if self.current_page < (len(self.character_list) - 1) // self.characters_per_page:
                self.current_page += 1
                live.update(self.render_panel())

        @bindings.add("k")
        def previous_page(event):
            if self.current_page > 0:
                self.current_page -= 1
                live.update(self.render_panel())

        app = Application(
            full_screen=True,
            key_bindings=bindings,
            input=create_input(),
        )

        with Live(self.render_panel(), refresh_per_second=4, screen=True) as live:
            app.run()


# Example usage
if __name__ == "__main__":
    # Unicode range for Chinese characters
    # Common Chinese characters are in the range 4E00 to 9FFF
    chinese_range_start = 0x4E00
    chinese_range_end = 0x9FFF

    viewer = UnicodeViewer(chinese_range_start, chinese_range_end)
    viewer.run()

