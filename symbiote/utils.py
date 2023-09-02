#!/usr/bin/env python3
#
# symbiote/utils.py

import json
import spacy
#import scispacy
import sys
import re
import os
import time
import subprocess
import magic
import textract
import hashlib
import requests 
import pathspec

from mss import mss
from PIL import Image
import numpy as np
import pandas as pd
import speech_recognition as sr
from pydub import AudioSegment
from thefuzz import fuzz
from thefuzz import process

from nltk.sentiment import SentimentIntensityAnalyzer
from spacy.lang.en.stop_words import STOP_WORDS
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from postal.parser import parse_address
from dateutil.parser import parse
from collections import defaultdict
from elasticsearch import Elasticsearch, exceptions
from elasticsearch import Elasticsearch
from transformers import GPT2Tokenizer, GPT2LMHeadModel, TextDataset, DataCollatorForLanguageModeling, Trainer, TrainingArguments
import torch

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sumy")

class utilities():
    def __init__(self, settings):
        self.settings = settings
        return

    def getScreenShot(self):
        ''' Take screenshot and return text object for all text found in the image '''
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
        ''' Take in a file path and return SHA256 value for the file '''
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
        ''' Check if an object fits the pattern of a potential date '''
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
        ''' Check text for the pattern of an e-mail address '''
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

    def exctractMedical(self, text):
        self.nlpm = spacy.load("en_core_sci_sm")

        doc = self.nlpm(text)

        for ent in doc.ents:
            print(ent.label_, ent.text)

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

    def extractDirText(self, dir_path):
        dir_path = os.path.expanduser(dir_path)
        dir_path = os.path.abspath(dir_path)

        if not os.path.isdir(dir_path):
            return None


        '''
        if os.path.isfile(".gitignore"):
            with open(os.path.join(dir_path, '.gitignore'), 'r') as f:
                gitignore = f.read()

            spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, gitignore.splitlines())
        '''

        header = str()
        content = str()
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                absolute_path = os.path.abspath(file_path)
                #if spec.match_file(file_path):
                #    continue
                file_contents = self.extractText(absolute_path)
                content += f"File name: {absolute_path}\n"
                content += '\n```\n{}\n```\n'.format(file_contents)

        return content

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
        elif re.search(r'^image\/', mime_type):
            content = textract.process(file_path)
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

    def learnFiles(self, path):
        ''' Model builder off personal data '''
        learning_dir = self.settings['symbiote_path'] + "/learning"
        if not os.path.exists(learning_dir):
            os.mkdir(learning_dir)

        # Download the tokenizer files
        tokenizer_files = {
            "vocab.json": "https://huggingface.co/gpt2/resolve/main/vocab.json",
            "merges.txt": "https://huggingface.co/gpt2/resolve/main/merges.txt",
            "tokenizer_config.json": "https://huggingface.co/gpt2/resolve/main/tokenizer_config.json",
        }

        for filename, url in tokenizer_files.items():
            response = requests.get(url)
            with open(os.path.join(learning_dir, filename), "wb") as f:
                f.write(response.content)

        # Load the tokenizer files and create a GPT2Tokenizer instance
        vocab_file = os.path.join(learning_dir, "vocab.json")
        merges_file = os.path.join(learning_dir, "merges.txt")

        model = GPT2LMHeadModel.from_pretrained('gpt2')
        tokenizer = GPT2Tokenizer(vocab_file=vocab_file, merges_file=merges_file)
        model.save_pretrained(learning_dir + "/gpt2_finetuned")

        file_list = []
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    full_path = os.path.join(root, file)
                    if not os.path.isdir(full_path):
                        file_list.append(full_path)
        elif os.path.isfile(path):
            file_list.append(path)

        with open(learning_dir + "gpt2_finetuned/tokenizer_config.json", "w") as f:
            data = {
                "model_max_length": 1024,
                "model_type": "gpt2",
                "padding_side": "right"
            }

            f.write(json.dumps(data))

        train_data = '/tmp/train_data.txt'

        train_data_size = 0
        with open(train_data, "w") as f:
            for file in file_list:
                content = self.extractText(file)
                f.write(content + '\n')
                f.flush()
                train_data_size = os.path.getsize(train_data) / (1024 * 1024)
                if train_data_size >= 128:
                    dataset = TextDataset(
                        tokenizer=tokenizer,
                        file_path=train_data,
                        block_size=128,
                    )

                    data_collator = DataCollatorForLanguageModeling(
                        tokenizer=tokenizer, mlm=False,
                    )

                    training_args = TrainingArguments(
                        output_dir="./gpt2_finetuned",
                        overwrite_output_dir=True,
                        num_train_epochs=1,
                        per_device_train_batch_size=4,
                        save_steps=10_000,
                        save_total_limit=2,
                        learning_rate=5e-5,
                        weight_decay=0.01,
                        gradient_accumulation_steps=4,
                        max_grad_norm=1.0,
                        report_to=[]
                    )

                    trainer = Trainer(
                        model=model,
                        args=training_args,
                        data_collator=data_collator,
                        train_dataset=dataset,
                    )

                    trainer.train()
                    f.truncate(0)
                    f.seek()

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
        output = None

        display_fields = ["METADATA.SourceFile"]

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
        except:
            print("No results found.")
        #print(df[['METADATA.SourceFile']])

        return output 

    def grepFiles(self, es_results, search_term):
        file_list = []
        fuzzy = re.sub(r'~\d\b|\bAND\b|\bOR\b', ' ', search_term)

        regex_search = self.lucene_like_to_regex(search_term)
        if regex_search is False:
            return None

        for hit in es_results['hits']['hits']:
            source_file = hit["fields"]['METADATA.SourceFile'][0]
            if source_file is not None:
                file_list.append(source_file)

        text = ""
        for file_path in file_list:
            if self.settings['debug']:
                print(f"Scanning {file_path}")
            with open(file_path, 'r') as file:
                for line_no, line in enumerate(file.readlines(), start=1):
                    if re.search(regex_search, line, re.I):
                        text += line
                        continue
                    
                    chunks = self.break_text(line, 1) 

                    for chunk in chunks:
                        ratio = fuzz.ratio(fuzzy.lower(), chunk.lower())
                        if ratio > 50:
                            if self.settings['debug']:
                                print(ratio, chunk, "\n", line)
                            text += line
                            break

        return text

    def break_text(self, text, num_words):
        words = text.split()
        chunks = [' '.join(words[i:i + num_words]) for i in range(0, len(words), num_words)]
        return chunks

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
        except Exception as e:
            print(f"Unknown exception: {e}")

        return text

    def lucene_like_to_regex(self, query):
        # Replace field:term to term
        single_term_regex = re.sub(r'\S+:(\S+)', r'\1', query)

        # Escape special regex characters, but leave our syntax elements
        escaped = re.sub(r'([\\.+^$[\]{}=!<>|:,\-])', r'\\\1', single_term_regex)

        # Restore escaped spaces (i.e., '\ ' to ' ')
        escaped = re.sub(r'\\ ', ' ', escaped)

        # Process grouping parentheses and quoted strings
        groups_and_quotes = re.sub(r'([()])', r'\\\1', escaped)
        groups_and_quotes = re.sub(r'"(.*?)"', r'\1', groups_and_quotes)

        # Convert wildcard queries to regex
        wildcard_regex = groups_and_quotes.replace('?', '.').replace('*', '.*')

        # Convert TO (range) queries to regex
        range_regex = re.sub(r'\[(\d+)\sTO\s(\d+)\]', lambda m: f"[{m.group(1)}-{m.group(2)}]", wildcard_regex)

        # Convert AND, OR and NOT queries to regex
        # AND operator is a bit tricky. We use positive lookaheads to emulate AND behavior in regex
        and_operator_regex = re.sub(r'(\S+)\sAND\s(\S+)', r'(?=.*\1)(?=.*\2)', range_regex)
        or_operator_regex = and_operator_regex.replace(' OR ', '|')
        not_operator_regex = or_operator_regex.replace(' NOT ', '^(?!.*')

        # Closing parentheses for each NOT operator
        final_regex = not_operator_regex.replace(' ', ').*')

        try:
            re.compile(final_regex)
            return final_regex
        except re.error:
            print(f"Invalid search term: {query}")
            return False


