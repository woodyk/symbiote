#!/usr/bin/env python3
#
# symbiote/content_parse.py

import json
import spacy
import sys
import re
import os
import time
import subprocess
import magic
import textract

from nltk.sentiment import SentimentIntensityAnalyzer
from spacy.lang.en.stop_words import STOP_WORDS
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from dateutil.parser import parse
from collections import defaultdict

class utilities():
    def __init__(self):
        return

    def extractMetadata(self, file_path):
        """Extracts metadata from a file using exiftool"""
        file_path = os.path.expanduser(file_path)
        file_path = os.path.abspath(file_path)

        result = subprocess.run(['exiftool', '-j', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(f'exiftool failed with code {result.returncode}: {result.stderr.decode()}')

        metadata = json.loads(result.stdout.decode())[0]

        return metadata

    def is_valid_date(self, date_str):
        try:
            dt = parse(date_str, fuzzy=True)
            if dt.hour > 0 or dt.minute > 0:
                return True  # Time
            if dt.month > 0 and dt.day > 0 and dt.year > 0:
                return True  # Month Day Year
            return False
        except:
            return False

    def analyze_text(self, text, meta):
        self.nlp = spacy.load('en_core_web_sm')
        self.sia = SentimentIntensityAnalyzer()
        self.tokenizer = Tokenizer("english")

        text = text.decode('utf-8')

        doc = self.nlp(text)

        label_map = {'PERSON': 'PERSONS',
                     'NORP': 'NATIONALITIES',
                     'FAC': 'LANDMARKS',
                     'ORG': 'ORGANIZATIONS',
                     'GPE': 'LOCALITIES',
                     'LOC': 'LOCATIONS',
                     'PRODUCT': 'PRODUCTS',
                     'EVENT': 'EVENTS',
                     'WORK_OF_ART': 'ARTWORKS',
                     'LAW': 'LEGAL',
                     'LANGUAGE': 'LANGUAGES',
                     'DATE': 'DATES',
                     'TIME': 'TIMES',
                     '#PERCENT': 'PERCENTAGES',
                     'MONEY': 'CURRENCIES',
                     'QUANTITY': 'QUANTITIES',
                     '#ORDINAL': 'ORDINALS',
                     '#CARDINAL': 'CARDINALS',
                     }

        # Initialize a default dictionary to store entities
        entity_dict = defaultdict(lambda: defaultdict(int))

        # Iterate over the entities
        for ent in doc.ents:
            # Only include common labels
            if ent.label_ in label_map: 
                # Increment the count of the entity text for the given label
                entity_dict[label_map[ent.label_]][ent.text] += 1

        # Convert the defaultdict to a regular dict for JSON serialization
        entity_dict = {label: dict(entities) for label, entities in entity_dict.items()}

        sentiment = self.sia.polarity_scores(text)

        parser = PlaintextParser.from_string(text, self.tokenizer)
        stop_words = list(STOP_WORDS)
        summarizer = LsaSummarizer()
        summarizer.stop_words = stop_words
        summary = summarizer(parser.document, 10)
        main_idea = " ".join(str(sentence) for sentence in summary)

        entity_dict['FILE_META_DATA'] = meta
        entity_dict['SENTIMENT'] = sentiment
        entity_dict['SUMMARY'] = main_idea

        return entity_dict 

    def summarizeText(self, text):
        result = self.analyze_text(text, meta)
        return result

    def summarizeFile(self, file_path):
        text = self.extractText(file_path)

        meta = self.extractMetadata(file_path)
        result = self.analyze_text(text, meta)

        return result

    def extractText(self, file_path):
        mime_type = magic.from_file(file_path, mime=True)

        if re.search(r'^text\/', mime_type):
            with open(file_path, 'r') as f:
                content = f.read()

        elif re.search(r'^image\/', mime_type):
            content = textract.process(file_path, method='tesseract', language='eng')

        elif mime_type == "application/pdf":
            content = textract.process(file_path, method='tesseract', language='eng')

        else:
            content = textract.process(file_path)

        return content
