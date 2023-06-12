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
import hashlib

from nltk.sentiment import SentimentIntensityAnalyzer
from spacy.lang.en.stop_words import STOP_WORDS
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from postal.parser import parse_address
from dateutil.parser import parse
from collections import defaultdict
from elasticsearch import Elasticsearch, exceptions

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sumy")

class utilities():
    def __init__(self, settings):
        self.settings = settings
        return

    def getSHA256(self, file_path):
        with open(file_path, "rb") as f:
            digest = hashlib.file_digest(f, "sha256")
    
        return digest.hexdigest()

    def extractMetadata(self, file_path):
        """Extracts metadata from a file using exiftool"""
        file_path = os.path.expanduser(file_path)
        file_path = os.path.abspath(file_path)

        sha256 = self.getSHA256(file_path)

        result = subprocess.run(['exiftool', '-j', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(f'exiftool failed with code {result.returncode}: {result.stderr.decode()}')

        metadata = json.loads(result.stdout.decode())[0]
        metadata['SHA256'] = sha256

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

    def extractEmail(self, text):
        email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        matches = re.findall(email_pattern, text)
        
        return matches

    def extractURL(self, text):
        url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        matches = re.findall(url_pattern, text)

        return matches

    def extractPhone(self, text):
        phone_number_pattern = r"\b(\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})\b"
        matches = re.findall(phone_number_pattern, text)

        return matches

    def extractAddress(self, text):
        components = [ 'house_number', 'road', 'postcode', 'city', 'state' ]
        parsed_address = parse_address(text)
        addresses = []
        address = {} 

        for component in parsed_address:
            if component[1] in address:
                addresses.append(address)
                address = {} 
            if component[1] in components:
                address[component[1]] = component[0]

        return addresses

    def extractCreditCard(self, text):
        card_pattern = r'\b(?:\d[ -]*?){13,16}\b'
        matches = re.findall(card_pattern, text)

        return matches

    def extractSocialSecurity(self, text):
        ss_pattern = r'\b\d{3}-?\d{2}-?\d{4}\b'
        matches = re.findall(ss_pattern, text)

    def analyze_text(self, text, meta):
        self.nlp = spacy.load('en_core_web_sm')
        self.sia = SentimentIntensityAnalyzer()
        self.tokenizer = Tokenizer("english")

        try:
            text = text.decode('utf-8')
        except:
            pass

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

        # Document container
        content = {}

        # Iterate over the entities
        ent_count = {}
        for ent in doc.ents:
            # Only include common labels
            if ent.label_ in label_map: 
                # Increment the count of the entity text for the given label
                if label_map[ent.label_] not in content:
                    content[label_map[ent.label_]] = []
                elif ent.text not in content[label_map[ent.label_]]:
                    content[label_map[ent.label_]].append(ent.text)

        sentiment = self.sia.polarity_scores(text)

        parser = PlaintextParser.from_string(text, self.tokenizer)
        stop_words = list(STOP_WORDS)
        summarizer = LsaSummarizer()
        summarizer.stop_words = stop_words
        summary = summarizer(parser.document, 10)
        main_idea = " ".join(str(sentence) for sentence in summary)

        content['EPOCH'] = time.time()
        content['ADDRESSES'] = self.extractAddress(text)
        content['FILE_META_DATA'] = meta
        content['SENTIMENT'] = sentiment
        content['SUMMARY'] = main_idea

        if self.settings['perifious']:
            content['EMAILS'] = self.extractEmail(text)
            content['WEBSITES'] = self.extractURL(text)
            content['PHONE_NUMBERS'] = self.extractPhone(text)
            content['CREDIT_CARDS'] = self.extractCreditCard(text)
            content['SOCIAL_SECURITY_NUMBERS'] = self.extractSocialSecurity(text)

        return content 

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
            try:
                content = textract.process(file_path)
            except Exception as e:
                content = ""
                pass

        return content

    def createIndex(self, path):
        es = Elasticsearch(self.settings['elasticsearch'])

        if not es.ping():
            print(f'Unable to reach {self.settings["elasticsearch"]}')
            return None

        if self.settings['debug']:
            print(f'Processing files in {path}.')

        fcount = 0
        for root, _, files in os.walk(path):
            for file in files:
                fcount += 1
                file_path = os.path.join(root, file)
                content = self.summarizeFile(file_path)

                if self.settings['debug']:
                    print(f'Processing file {file_path}. count:{fcount}')

                doc_id = content['FILE_META_DATA']['SourceFile']
                index = self.settings['elasticsearch_index']

                if not es.indices.exists(index=index):
                    es.indices.create(index=index)

                try:
                    es.index(index=index, id=doc_id, document=json.dumps(content))
                except exceptions.RequestError as e:
                    print(f"RequestError: {e}")
                except exceptions.ConnectionError as e:
                    print(f"ConnectionError: {e}")
                except exceptions.TransportError as e:
                    print(f"TransportError: {e}")
                except Exception as e:
                    print("UnknownError: {e}")

                es.indices.refresh(index=index)

        return content

    def searchIndex(self):
        pass
