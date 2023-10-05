#!/usr/bin/env python3
#
# matrix_rain.py

import sys
import time
import random
import pygame
import pygame.freetype

# Color Codes
colors = {
    "red": (255, 0, 0, 255),
    "orange": (255, 165, 0, 255),
    "yellow": (255, 255, 0, 255),
    "green": (0, 128, 0, 255),
    "blue": (0, 0, 255, 255),
    "indigo": (75, 0, 130, 255),
    "violet": (127, 0, 255, 255),
    "white": (255, 255, 255, 255),
    "black": (0, 0, 0, 255),
}

# Matrix parameters
matrix = 0
num_streams = 5000
speed = .01
min_speed = 0.01
max_speed = 5.0
font_size = 12 
font_color = 'white' # White
font_decay_color = 'green' # Green
fade_intensity = 1  # The higher this value, the faster the trails will fade
new_stream = True

setting_message = None
setting_message_expiration = 0

# Initialize Pygame
pygame.init()
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
font = pygame.freetype.SysFont('Courier', font_size)

# Get screen resolution
info = pygame.display.Info()
width, height = info.current_w, info.current_h

# Frames per second
FPS = 30

# Calculate number of columns
num_columns = width // font_size

# Create streams
new_streams = []

# Modify the create_streams function to use the num_streams variable
def create_streams(matrix):
    streams = []
    if matrix == 0:
        for _ in range(num_streams):
            speed = random.uniform(min_speed, max_speed)
            x = random.randint(0, width)  # Random value within the width of the screen
            y = random.randint(0, height)  # Random value within the height of the screen
            color = list(colors[font_color])  # Make a copy of the color
            streams.append((speed, x, y, color))
    elif matrix == 1:
        for _ in range(num_streams):
            speed = random.uniform(min_speed, max_speed)
            x = random.randint(0, width)
            y = random.randint(0, height)
            streams.append((speed, x, y))

    return streams

# Help menu
help_menu = False

def display_help_menu():
    # Create a semi-transparent surface
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 128))  # Semi-transparent black

    # Create a font object
    font = pygame.freetype.SysFont('Courier', 16)

    # Define the help text
    help_text = [
        "Help Menu:",
        "UP: Increase speed",
        "DOWN: Decrease speed",
        "LEFT: Increase persistence",
        "RIGHT: Decrease persistence",
        "+: Increase font size",
        "-: Decrease font size",
        "H: Show/hide this help menu",
        "I: Increase fade intensity",
        "D: Decrease fade intensity",
        "K: Increase number of streams",
        "L: Decrease number of streams",

    ]

    # Render the help text
    for i, line in enumerate(help_text):
        font.render_to(surface, (10, 10 + 20*i), line, (255, 255, 255))  # White text

    return surface

def cycle_color(current):
    # Get a list of color names
    color_names = list(colors.keys())

    # Find the index of the current color
    current_index = color_names.index(current)

    # Get the next color in the list, wrapping around to the start if necessary
    next_index = (current_index + 1) % len(color_names)

    # Return the name and RGB values of the next color
    return color_names[next_index], colors[color_names[next_index]]

# Main loop
running = True
setting_message = False
count = 0
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                max_speed = min(10, max_speed + 0.01)
            elif event.key == pygame.K_DOWN:
                max_speed = max(0.5, max_speed - 0.01)
            elif event.key == pygame.K_h:
                help_menu = not help_menu  # Toggle help menu
            elif event.key == pygame.K_EQUALS:
                font_size += 2
                font = pygame.freetype.SysFont('Courier', font_size)
            elif event.key == pygame.K_MINUS:
                font_size = max(2, font_size - 2)
                font = pygame.freetype.SysFont('Courier', font_size)
            elif event.key == pygame.K_n:
                new_stream = True
                if matrix >= 1:
                    matrix = 0
                else:
                    matrix = matrix + 1
            elif event.key == pygame.K_i:
                fade_intensity = min(10, fade_intensity + 0.01)
            elif event.key == pygame.K_d:
                fade_intensity = max(0.01, fade_intensity - 0.01)
            elif event.key == pygame.K_k:
                num_streams = min(5000, num_streams + 100)  # Increase the number of streams
                setting_message = f"Number of streams: {num_streams}"
            elif event.key == pygame.K_l:
                num_streams = max(10, num_streams - 100)  # Decrease the number of streams
                setting_message = f"Number of streams: {num_streams}"
            elif event.key == pygame.K_4:
                # cycle font_color
                font_color, font_rgb = cycle_color(font_color)
                setting_message = f"Font color: {font_color}"
            elif event.key == pygame.K_5:
                # cycle font_decay_color
                font_decay_color, font_decay_rgb = cycle_color(font_decay_color)
                setting_message = f"Font color: {font_decay_color}"
            elif event.key == pygame.K_6:
                pass

    if setting_message:
        print(setting_message)
        setting_message = False
        new_stream = True

    if new_stream:
        streams = create_streams(matrix)
        new_stream = False

    # Clear screen
    screen.fill((0, 0, 0))

    # Clear screen with a semi-transparent black rectangle
    fade_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    fade_surface.fill((0, 0, 0, fade_intensity))
    screen.blit(fade_surface, (0, 0))

    # Update and draw streams
    new_streams = []
    if matrix == 0:
        for speed, x, y, color in streams:
            # Update color
            print(type(color[3]), type(fade_intensity))
            color[3] = max(0, color[3] - fade_intensity)  # Reduce alpha component

            # Draw character
            char = chr(random.randint(0x20, 0x7E))  # ASCII characters
            column = 0
            font.render_to(screen, (x, int(y)), char, color)

            # Update position
            y += speed
            if y > height:
                y = 0
                color = list(colors[font_color])  # Reset color
            new_streams.append((speed, x, y, color))
        streams = new_streams
    elif matrix == 1:
        for speed, x, y in streams:
            # Draw characters
            for i in range(int(y), height, font_size):
                intensity = min(1, max(0, (i - y) / height))
                color = [int(c * intensity) for c in font_color]
                decay_color = [int(c * (1 - intensity)) for c in colors[font_decay_color]]
                final_color = [c1 + c2 for c1, c2 in zip(color, decay_color)]
                char = chr(random.randint(0x20, 0x7E))  # ASCII characters
                font.render_to(screen, (x, i), char, final_color)
            
            # Update stream
            y += speed
            if y > height:
                y = random.randint(-height, 0)
            new_streams.append((speed, x, int(y)))
        streams = new_streams

    # Display help menu
    if help_menu:
        help_surface = display_help_menu()
        screen.blit(help_surface, (0, 0))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
