#!/usr/bin/env python3
#
# symbiote/utils.py

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

from mss import mss
from PIL import Image
import numpy as np
import pandas as pd
import speech_recognition as sr
from pydub import AudioSegment

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

    def getScreenShot(self):
        # Screenshot storage path
        path = r'/tmp/symScreenShot.png'

        with mss() as sct:
            monitor = {"top": 0, "left": 0, "width": 0, "height": 0}
            
            for mon in sct.monitors:
                # get furthest left point
                monitor["left"] = min(mon["left"], monitor["left"])
                # get highest point
                monitor["top"] = min(mon["top"], monitor["top"])
                # get furthest right point
                monitor["width"] = max(mon["width"]+mon["left"]-monitor["left"], monitor["width"])
                # get lowest point
                monitor["height"] = max(mon["height"]+mon["top"]-monitor["top"], monitor["height"])
            
            screenshot = sct.grab(monitor)

        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        img_gray = img.convert("L")
        img_gray.save(path)

        return path

    def getSHA256(self, file_path):
        file_path = os.path.expanduser(file_path)
        file_path = os.path.abspath(file_path)

        with open(file_path, "rb") as f:
            digest = hashlib.file_digest(f, "sha256")
    
        return digest.hexdigest()

    def extractMetadata(self, file_path):
        """Extracts metadata from a file using exiftool"""
        file_path = os.path.expanduser(file_path)
        file_path = os.path.abspath(file_path)

        sha256 = self.getSHA256(file_path)

        try:
            result = subprocess.run(['exiftool', '-j', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(f'exiftool failed: {e}')

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
        
        clean = self.cleanMatches(matches)

        return clean

    def cleanMatches(self, matches):
        clean = []
        for match in matches:
            if type(match) == tuple or type(match) == list:
                for entry in match:
                    if entry is not None and not "" and entry not in clean:
                        clean.append(entry)
            elif type(match) == str:
                clean.append(match)
            else:
                pass

        return clean

    def removeSpecial(self, values):

        if type(values) == str:
            values = re.sub('[^\-\.,\#A-Za-z0-9 ]+', '', values)
        elif type(values) == (str or list or tuple):
            for value in values:
                values[index(value)] = re.sub('[^\-\.,\#A-Za-z0-9 ]+', '', value)

        return values 

    def extractURL(self, text):
        #url_pattern = r"(?:http[s]?:\/\/)?(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        #url_pattern = r'(?:http[s]?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&\'\(\)\*\+,;=.]+'
        url_pattern = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        matches = re.findall(url_pattern, text)

        clean = self.cleanMatches(matches)

        return clean 

    def extractPhone(self, text):
        phone_number_pattern = r"\b\d{10,11}\b|\b(\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})\b"
        matches = re.findall(phone_number_pattern, text)

        clean = self.cleanMatches(matches)
        clean = self.removeSpecial(clean)

        return clean

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
                address[component[1]] = self.removeSpecial(component[0])

        return addresses

    def extractCreditCard(self, text):
        card_pattern = r'\b(?:\d[ -]*?){13,16}\b'
        matches = re.findall(card_pattern, text)

        clean = self.cleanMatches(matches)
        clean = self.removeSpecial(clean)

        return clean

    def extractSocialSecurity(self, text):
        ss_pattern = r'\b\d{3}-?\d{2}-?\d{4}\b'
        matches = re.findall(ss_pattern, text)

        clean = self.cleanMatches(matches)
        clean = self.removeSpecial(clean)

        return clean

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
                elif ent.text not in content[label_map[ent.label_]] and ent.text is not (None or ""):
                    clean_text = self.removeSpecial(ent.text)
                    content[label_map[ent.label_]].append(clean_text)

        sentiment = self.sia.polarity_scores(text)

        parser = PlaintextParser.from_string(text, self.tokenizer)
        stop_words = list(STOP_WORDS)
        summarizer = LsaSummarizer()
        summarizer.stop_words = stop_words
        summary = summarizer(parser.document, 10)
        main_idea = " ".join(str(sentence) for sentence in summary)

        content['EPOCH'] = time.time()
        content['ADDRESSES'] = self.extractAddress(text)
        #content.update(meta)
        content['METADATA'] = meta
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
                try:
                    content = f.read()
                except UnicodeDecodeError as e:
                    content = ""
        elif re.search(r'^audio\/', mime_type):
            #content = self.transcribe_audio_file(file_path)
            content = ""
        else:
            try:
                content = textract.process(file_path, method='tesseract', language='eng')
            except Exception as e:
                content = ""

        try:
            content = content.decode('utf-8')
        except:
            pass

        if self.settings['debug']:
            print(content)

        return content

    def esConnect(self):
        es = Elasticsearch(self.settings['elasticsearch'])

        if not es.ping():
            print(f'Unable to reach {self.settings["elasticsearch"]}')
            return None

        return es

    def createIndex(self, path, reindex=False):
        es = self.esConnect()
        
        file_list = []
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    full_path = os.path.join(root, file)
                    if not os.path.isdir(full_path):
                        file_list.append(full_path)
        elif os.path.isfile(path):
            file_list.append(path)

        index = self.settings['elasticsearch_index']

        if not es.indices.exists(index=index):
            es.indices.create(index=index)

        fcount = 0
        for file in file_list:
            fcount += 1
            if self.settings['debug']:
                print(f'Processing file {file}. count:{fcount}')

            doc_id = self.getSHA256(file)

            if not reindex:
                if es.exists(index=index, id=doc_id):
                    if self.settings['debug']:
                        print(f"Document {doc_id} found. skipping...")
                    continue

            content = self.summarizeFile(file)

            try:
                es.index(index=index, id=doc_id, document=json.dumps(content))
            except exceptions.NotFoundError as e:
                if self.settings['debug']:
                    print(f"Document not found: {e}")
            except exceptions.RequestError as e:
                if self.settings['debug']:
                    print(f"Problem with the request: {e}")
            except exceptions.ConnectionError as e:
                if self.settings['debug']:
                    print(f"Problem with the connection: {e}")
            except exceptions.ConflictError as e:
                if self.settings['debug']:
                    print(f"Conflict occurred. Probably the document with this id already exists.")
            except exceptions.TransportError as e:
                if self.settings['debug']:
                    print(f"General transport error: {e}")
            except Exception as e:
                if self.settings['debug']:
                    print(f"Error: {e}")

            es.indices.refresh(index=index)

        return True

    def searchIndex(self, query):
        es = self.esConnect()

        ret = ""

        try:
            res = es.search(index=self.settings['elasticsearch_index'],
                               body={
                                  "track_total_hits": True,
                                  "sort": [
                                    {
                                      "_score": {
                                        "order": "desc"
                                      }
                                    }
                                  ],
                                  "fields": [
                                    {
                                      "field": "*",
                                      "include_unmapped": "true"
                                    }
                                  ],
                                  "size": 10000,
                                  "version": True,
                                  "script_fields": {},
                                  "stored_fields": [
                                    "*"
                                  ],
                                  "runtime_mappings": {},
                                  "_source": False,
                                  "query": {
                                    "bool": {
                                      "must": [
                                        {
                                          "query_string": {
                                            "query": query,
                                            "analyze_wildcard": True,
                                            "time_zone": "America/New_York"
                                          }
                                        }
                                      ],
                                      "filter": [],
                                      "should": [],
                                      "must_not": []
                                    }
                                  }
                                }
                            )

            ret = res.copy()
        except:
            print(f'Error running query: {query}')

        return ret 

    def displayDocuments(self, json_data):
        # Load the JSON data
        data = json.loads(json_data)

        display_fields = ["METADATA.SourceFile", "METADATA.MIMEType"]

        # Extract the 'hits' data
        hits = data["hits"]["hits"]

        # Create a list to store the documents
        documents = []

        # Iterate through the hits and extract the fields data
        for hit in hits:
            fields = hit["fields"]

            fields = {k: v for k, v in fields.items() if not k.endswith('.keyword')}

            documents.append(fields)

        # Create a Pandas DataFrame from the documents
        df = pd.DataFrame(documents)

        # Print the DataFrame as a table
        try:
            output = df[display_fields]
            print(output)
        except:
            print("No results found.")
        #print(df[['METADATA.SourceFile']])

        return 

    def grepFiles(self, es_results, search_term):
        source_files = []
        for hit in es_results['hits']['hits']:
            source_file = hit["_source"].get("METADATA", {}).get("SourceFile")
            if file_list:
                file_list.append(source_file)

        text = ""
        for file_path in file_list:
            with open(file_path, 'r') as file:
                for line_no, line in enumerate(file.readlines(), start=1):
                    if re.search(search_term, line):
                        text += line
        return text

    def convert_audio_to_wav(self, file_path):
        # Extract the file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lstrip('.')

        # Use pydub to convert to WAV
        audio = AudioSegment.from_file(file_path, format=ext)
        wav_file_path = file_path.replace(ext, 'wav')
        audio.export(wav_file_path, format='wav')

        return wav_file_path

    def transcribe_audio_file(self, audio_file):
        recognizer = sr.Recognizer()
        text = ""

        # Convert the file to WAV if necessary
        _, ext = os.path.splitext(audio_file)
        if ext.lower() not in ['.wav', '.wave']:
            audio_file = self.convert_audio_to_wav(audio_file)

        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            print("Google Speech Recognition thinks you said: " + text)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

        return text
