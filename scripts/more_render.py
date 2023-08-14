#!/usr/bin/env python3
#
# tt.py

import cv2
import numpy as np
import shapes_pb2
import queue
import threading
import time
import asyncio

class SymbiosRenderer:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.shapes = {}
        self.queue = queue.Queue()

    def render_shape(self, img, shape):
        if shape.type == shapes_pb2.Shape.SQUARE:
            cv2.rectangle(img, (shape.position.x, shape.position.y), (shape.position.x + shape.size.width, shape.position.y + shape.size.height), (255, 255, 255), -1)
        elif shape.type == shapes_pb2.Shape.CIRCLE:
            cv2.circle(img, (shape.position.x, shape.position.y), max(shape.size.width, shape.size.height) // 2, (255, 255, 255), -1)
        elif shape.type == shapes_pb2.Shape.LINE:
            cv2.line(img, (shape.position.x, shape.position.y), (shape.position.x + shape.size.width, shape.position.y + shape.size.height), (255, 255, 255), 1)

    def add_shape(self, shape_data):
        shape = shapes_pb2.Shape()
        shape.ParseFromString(shape_data)
        self.shapes[shape.id] = shape

    def delete_shape(self, shape_id):
        del self.shapes[shape_id]

    def update_shape(self, shape_data):
        shape = shapes_pb2.Shape()
        shape.ParseFromString(shape_data)
        self.shapes[shape.id] = shape

    def move_shape(self, shape_id, dx, dy):
        shape = self.shapes[shape_id]
        shape.position.x += dx
        shape.position.y += dy

    async def main_loop(self):
        while True:
            img = np.zeros((self.height, self.width, 3), np.uint8)

            while not self.queue.empty():
                action = self.queue.get()
                if action[0] == 'add':
                    self.add_shape(action[1])
                elif action[0] == 'delete':
                    self.delete_shape(action[1])
                elif action[0] == 'update':
                    self.update_shape(action[1])
                elif action[0] == 'move':
                    self.move_shape(action[1], action[2], action[3])

            for shape in self.shapes.values():
                if shape.visible:
                    self.render_shape(img, shape)

            cv2.imshow('SymbiosRenderer', img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cv2.destroyAllWindows()

# Create an instance of the SymbiosRenderer class
renderer = SymbiosRenderer()

# Create a new square shape
square = shapes_pb2.Shape()
square.id = "square1"
square.type = shapes_pb2.Shape.SQUARE
square.position.x = 50
square.position.y = 50
square.size.width = 100
square.size.height = 100
square.visible = True

# Add the square to the renderer
renderer.queue.put(('add', square.SerializeToString()))

# Start the renderer's main loop in a separate thread
asyncio.run(renderer.main_loop())

# Wait for a while
time.sleep(2)

# Move the square
renderer.queue.put(('move', 'square1', 100, 100))

# Wait for a while

# Update the square
square.position.x = 200
square.position.y = 200
renderer.queue.put(('update', square.SerializeToString()))

# Wait for a while
time.sleep(2)

# Delete the square
renderer.queue.put(('delete', 'square1'))

# Wait for a while
time.sleep(2)

# Stop the renderer's main loop
renderer.queue.put(('quit',))

