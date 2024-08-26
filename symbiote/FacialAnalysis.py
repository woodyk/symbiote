#!/usr/bin/env python3
#
# FacialAnalysis.py

import os
import json
import cv2
import requests
from deepface import DeepFace
from PIL import Image, ImageDraw, ImageFont

class FaceAnalyzer:
    def __init__(self, backend='opencv'):
        self.backend = backend

    def load_image(self, image_source):
        if image_source.startswith(('http://', 'https://')):
            img = Image.open(requests.get(image_source, stream=True).raw)
        else:
            img = Image.open(image_source)
        return img

    def analyze_faces(self, image_source):
        try:
            analysis_results = DeepFace.analyze(
                img_path=image_source,
                actions=['emotion', 'age', 'gender', 'race'],
                enforce_detection=True,
                detector_backend=self.backend,
                silent=True
            )
            return analysis_results
        except Exception as e:
            print(f"An error occurred while analyzing the photo: {e}")
            return None

    def draw_boxes(self, image, analysis_results):
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()  # Use the default font

        for i, result in enumerate(analysis_results):
            region = result['region']
            box = (region['x'], region['y'], region['x'] + region['w'], region['y'] + region['h'])

            draw.rectangle(box, outline="red", width=3)

            label_text = f"Person {i+1}\nGender: {result['dominant_gender']}, Age: {result['age']}"
            text_bbox = draw.textbbox((0, 0), label_text, font=font)
            text_size = (text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1])
            text_location = (box[0], box[1] - text_size[1] - 10 if box[1] - text_size[1] - 10 > 0 else box[1])

            background_box = [text_location[0] - 5, text_location[1] - 5, text_location[0] + text_size[0] + 5, text_location[1] + text_size[1] + 5]
            draw.rectangle(background_box, fill=(0, 0, 0, 128))

            draw.text(text_location, label_text, fill="white", font=font)

        return image

    def analyze_photo(self, image_source):
        image = self.load_image(image_source)
        analysis_results = self.analyze_faces(image_source)
        
        if analysis_results is None:
            return None, None

        labeled_image = self.draw_boxes(image, analysis_results)
        return labeled_image, analysis_results

    def display_image(self, image):
        image.show()

# Example usage:
if __name__ == "__main__":
    image_source = "https://www.jazzastudios.com/cdn/shop/products/FaceRefCover1.jpg?v=1659943039&width=1920"

    analyzer = FaceAnalyzer(backend='mtcnn')
    labeled_image, analysis_results = analyzer.analyze_photo(image_source)

    if labeled_image:
        analyzer.display_image(labeled_image)
        print(json.dumps(analysis_results, indent=4))

