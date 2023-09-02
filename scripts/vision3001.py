#!/usr/bin/env python3
#
# vision300.py

import pygame
import numpy as np
import cv2

# Define the size of the image
width, height = 3200, 900 

# Ratio of white to black pixels (0.1 means 10% white, 90% black)
ratio = 0.01

# Initialize Pygame
pygame.init()

# Set up some necessities
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36) # You can change None to a font file path to use a specific font

def blob_detection(binary_data, min_size=256):
    # Find connected components in the binary image
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_data, connectivity=8)

    blobs = []
    for i in range(1, num_labels):
        # Ignore small blobs
        if stats[i, cv2.CC_STAT_AREA] < min_size:
            continue

        # Add blob to list
        blob = {
            "label": i,
            "size": stats[i, cv2.CC_STAT_AREA],
            "centroid": (centroids[i, 0], centroids[i, 1]),
            "bbox": (
                stats[i, cv2.CC_STAT_LEFT],
                stats[i, cv2.CC_STAT_TOP],
                stats[i, cv2.CC_STAT_WIDTH],
                stats[i, cv2.CC_STAT_HEIGHT],
            ),
        }
        blobs.append(blob)

    return blobs

def decay_blobs(old_blobs, new_blobs, decay_rate=.01):
    # Create a list to hold the updated blobs
    updated_blobs = []

    # For each old blob
    for old_blob in old_blobs:
        # Check if it is in the new blobs
        match = next((blob for blob in new_blobs if blob["label"] == old_blob["label"]), None)

        # If the blob is in the new blobs, keep it and don't decay
        if match:
            updated_blobs.append(old_blob)
            new_blobs.remove(match)  # Remove the matched blob from the new blobs
        else:
            # If the blob is not in the new blobs, decay it
            old_blob["size"] *= (1 - decay_rate)

            # Only keep the blob if it's size is still above a certain threshold (e.g., 1)
            if old_blob["size"] > 1:
                updated_blobs.append(old_blob)

    # Add any remaining new blobs to the updated blobs list
    updated_blobs.extend(new_blobs)

    return updated_blobs

def draw_blobs(blobs, width, height):
    # Create a new surface
    surface = pygame.Surface((width, height))
    surface.fill((0, 0, 0))  # Fill the surface with black

    # Draw each blob onto the surface
    for blob in blobs:
        # Determine the color and size of the blob
        green_intensity = int(blob["size"])  # Use blob size to determine green intensity
        green_intensity = min(255, max(0, green_intensity))  # Clamp intensity between 0 and 255
        color = (0, green_intensity, 0)  # Green color, with intensity based on blob size
        radius = 1  # Fixed radius

        # Draw the blob
        pygame.draw.circle(surface, color, (int(blob["centroid"][0]), int(blob["centroid"][1])), radius)

    return surface

def detect_and_draw_text(image):
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Use Tesseract to detect text
    text = pytesseract.image_to_string(gray)

    print(text)

    # Draw the text on the image
    cv2.putText(image, text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

# Create an array of random numbers using the specified ratio
def create_static(height, width, ratio):
    # Create an array of random floats from a uniform distribution
    random_floats = np.random.uniform(0, 1, (height, width))

    # Create a binary mask where values less than the ratio are True (these will become our white pixels)
    mask = random_floats < ratio

    # Use the mask to create an array of black and white pixels
    static_data = np.where(mask, 255, 0).astype(np.uint8)

    return static_data

def display_help_menu():
    help_text = [
        "Help Menu:",
        "Up Arrow: Increase ratio of white pixels",
        "Down Arrow: Decrease ratio of white pixels",
        "H: Show this help menu",
        "Space: Pause/Resume"
    ]
    for i, line in enumerate(help_text):
        text_surface = font.render(line, True, (255, 255, 255)) # White text
        screen.blit(text_surface, (10, 10 + 40*i)) # 40 pixels line height

# Blobs from previous frames
old_blobs = []

# Main loop
running = True
paused = False
help_menu = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                ratio = min(1.0, ratio + 0.005)
            elif event.key == pygame.K_DOWN:
                ratio = max(0.0, ratio - 0.005)
            elif event.key == pygame.K_h:
                help_menu = not help_menu # Toggle help menu
            elif event.key == pygame.K_SPACE:
                paused = not paused  # Toggle pause

    if not paused:
        # Generate static data
        static_data = create_static(height, width, ratio)

        # Threshold static data to binary
        _, binary_data = cv2.threshold(static_data, 127, 255, cv2.THRESH_BINARY)

        # Detect blobs in binary data
        blobs = blob_detection(binary_data)

        # Compare old blobs to new blobs and decay if not persisting
        old_blobs = decay_blobs(old_blobs, blobs)

        if blobs:
            # Draw blobs
            blob_surface = draw_blobs(old_blobs, width, height)
            screen.blit(blob_surface, (0, 0))
        else:
            # Draw static
            static_surface = pygame.surfarray.make_surface(static_data)
            screen.blit(pygame.transform.scale(static_surface, (width, height)), (0, 0))

    if help_menu:
        display_help_menu()

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
