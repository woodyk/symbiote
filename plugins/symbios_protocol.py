#!/usr/bin/env python3
#
# symbios_protocol.py

import asyncio
import websockets
import zlib
import numpy as np

class SymbiosPlugin:
    def __init__(self, address="localhost", port=8765):
        self.uri = f"ws://{address}:{port}"
        self.websocket = None

    async def connect(self):
        self.websocket = await websockets.connect(self.uri)

    async def disconnect(self):
        if self.websocket:
            await self.websocket.close()

    async def send_frame(self, frame_data):
        # Convert the frame data to a byte array
        byte_data = frame_data.tobytes()

        # Compress the byte data
        compressed_data = zlib.compress(byte_data)

        # Send the compressed data
        await self.websocket.send(compressed_data)

    async def receive_frame(self, width, height):
        # Receive the compressed data
        compressed_data = await self.websocket.recv()

        # Decompress the data
        byte_data = zlib.decompress(compressed_data)

        # Convert the byte data back to a numpy array
        frame_data = np.frombuffer(byte_data, dtype=np.uint8).reshape((height, width, 3))

        return frame_data
