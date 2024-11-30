#!/usr/bin/env python3
#
# test.py

import os
import subprocess
import threading
import asyncio
from time import sleep, strftime
from collections import OrderedDict

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.box import DOUBLE
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

# Initialize the console
console = Console()

# Global state for TUI elements
class Widget:
    def __init__(self, name, content, position):
        self.name = name
        self.content = content  # Function that returns Rich renderable
        self.position = position  # Tuple (row, column)
        self.visible = True

class WidgetManager:
    def __init__(self):
        self.widgets = OrderedDict()
        self.lock = threading.Lock()
        self.positions = {}  # Track positions to avoid overlap
        self.next_position = (1, 1)  # Starting position

    def add_widget(self, name, content_func):
        with self.lock:
            if name in self.widgets:
                console.print(f"Widget '{name}' already exists.", style="bold yellow")
                return
            position = self.get_next_position()
            widget = Widget(name, content_func, position)
            self.widgets[name] = widget
            console.print(f"Added widget '{name}' at position {position}", style="bold green")

    def remove_widget(self, name):
        with self.lock:
            if name in self.widgets:
                del self.widgets[name]
                console.print(f"Removed widget '{name}'", style="bold green")
            else:
                console.print(f"Widget '{name}' not found.", style="bold yellow")

    def clear_widgets(self):
        with self.lock:
            self.widgets.clear()
            console.print("Cleared all widgets.", style="bold green")

    def get_next_position(self):
        # Simple grid positioning: top-left, top-right, bottom-left, bottom-right, etc.
        # This can be enhanced to handle more complex layouts
        existing_positions = {widget.position for widget in self.widgets.values()}
        # Example positions (row, column): top-left, top-right, bottom-left, bottom-right, center
        predefined_positions = [
            (1, 1),  # Top-left
            (1, 80),  # Top-right (assuming 80 cols)
            (20, 1),  # Bottom-left (assuming 24 rows)
            (20, 80),  # Bottom-right
            (10, 40),  # Center
        ]
        for pos in predefined_positions:
            if pos not in existing_positions:
                return pos
        # If all predefined positions are taken, stack vertically with padding
        last_row, last_col = self.next_position
        new_pos = (last_row + 5, last_col)
        self.next_position = new_pos
        return new_pos

    def render_widgets(self):
        with self.lock:
            return Group(*[
                Align(
                    self.widgets[name].content(),
                    align="left",
                    vertical="top",
                )
                for name in self.widgets
            ])

# Initialize Widget Manager
widget_manager = WidgetManager()

# Function to execute shell commands
def execute_shell(command, output_callback):
    try:
        result = subprocess.run(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.stdout:
            output_callback(result.stdout)
        if result.stderr:
            output_callback(result.stderr, style="bold red")
    except Exception as e:
        output_callback(f"Error: {e}", style="bold red")

# Clock widget generator
def pop_clock():
    current_time = strftime("%H:%M:%S")
    return Panel(
        Align.center(Text(current_time, style="bold green")),
        title="Clock",
        border_style="green",
        box=DOUBLE
    )

# Popup widget generator
def pop_shell(shell_command):
    output_lines = []

    def collect_output():
        try:
            result = subprocess.run(
                shell_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if result.stdout:
                output_lines.append(result.stdout)
            if result.stderr:
                output_lines.append(f"[bold red]{result.stderr}[/bold red]")
        except Exception as e:
            output_lines.append(f"Error: {e}")

    # Execute the command and collect output
    collect_output()
    content = "\n".join(output_lines)
    return Panel(
        Align.left(Text(content)),
        title=f"Popup: {shell_command}",
        border_style="cyan",
        box=DOUBLE
    )

# Function to manage live TUI rendering
def render_tui(loop, layout, stop_event):
    with Live(layout, refresh_per_second=10, console=console, screen=True):
        while not stop_event.is_set():
            # Update widgets
            widgets = widget_manager.render_widgets()
            layout["widgets"].update(widgets)
            loop.call_soon_threadsafe(asyncio.create_task, asyncio.sleep(0.1))
            sleep(0.1)

# Asynchronous function to update dynamic widgets like clock
async def dynamic_widget_updater():
    while True:
        # Currently, widgets handle their own updates
        await asyncio.sleep(1)

# Main function with asynchronous event loop
def main():
    current_time = strftime("%H:%M:%S")
    tt = Panel(
        Align.center(Text(current_time, style="bold green")),
        title="Clock",
        border_style="green",
        box=DOUBLE
    )
    pop_shell("ls -al")
    console.print(tt)
    console_text = Text.from_markup("[blue]test[/blue][green]some[/green]")
    console.print(console_text)
if __name__ == "__main__":
    main()
