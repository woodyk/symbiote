#!/usr/bin/env python3
#
# matrix_rain.py

import random
import pygame
import pygame.freetype

# Matrix parameters
num_streams = 100
speed = .01
min_speed = 0.01
max_speed = 5.0
font_size = 12 
font_color = (255, 255, 255, 255) # White
font_decay_color = (0, 255, 0, 255) # Green
font_intensity_decay = 0.05

# Initialize Pygame
pygame.init()
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
font = pygame.freetype.SysFont('Courier', font_size)

# Create streams
streams = []
for _ in range(num_columns):
    speed = random.uniform(min_speed, max_speed)
    x = _ * font_size
    y = random.randint(-height, 0)
    streams.append((speed, x, y))


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
    ]

    # Render the help text
    for i, line in enumerate(help_text):
        font.render_to(surface, (10, 10 + 20*i), line, (255, 255, 255))  # White text

    return surface

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                max_speed = min(10, max_speed + 0.01)
            elif event.key == pygame.K_DOWN:
                max_speed = max(0.5, max_speed - 0.01)
            elif event.key == pygame.K_LEFT:
                font_intensity_decay = max(0.01, font_intensity_decay - 0.01)
            elif event.key == pygame.K_RIGHT:
                font_intensity_decay = min(1.0, font_intensity_decay + 0.01)
            elif event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS:
                font_size += 2
                font = pygame.freetype.SysFont('Courier', font_size)
            elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                font_size = max(2, font_size - 2)
                font = pygame.freetype.SysFont('Courier', font_size)
            elif event.key == pygame.K_h:
                help_menu = not help_menu  # Toggle help menu
            elif event.key == pygame.K_EQUALS:
                font_size += 2
                font = pygame.freetype.SysFont('Courier', font_size)
            elif event.key == pygame.K_MINUS:
                font_size = max(2, font_size - 2)
                font = pygame.freetype.SysFont('Courier', font_size)

    # Clear screen
    screen.fill((0, 0, 0))

    # Update and draw streams
    new_streams = []
    for speed, x, y in streams:
        # Draw characters
        for i in range(int(y), height, font_size):
            intensity = min(1, max(0, (i - y) / height))
            color = [int(c * intensity) for c in font_color]
            decay_color = [int(c * (1 - intensity)) for c in font_decay_color]
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
    clock.tick(30)

pygame.quit()

