#!/usr/bin/env python3

import requests
import sys
from bs4 import BeautifulSoup
import re
import spacy
from transformers import pipeline
import nltk
from textblob import TextBlob
import random
import string
import torch
import networkx as nx
from urllib.parse import quote_plus
from transformers import T5Tokenizer, T5ForConditionalGeneration

class GoogleKnowledgeGraphChatbot:
    def __init__(self):
        self.G = nx.Graph()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = T5ForConditionalGeneration.from_pretrained('t5-base').to(self.device)
        self.tokenizer = T5Tokenizer.from_pretrained('t5-base')
        self.nlp = spacy.load("en_core_web_sm")
        self.pegasus_pipeline = pipeline("summarization", model="google/pegasus-large", tokenizer="google/pegasus-large")
        nltk.download("punkt")

    def summarize_text(self, text, max_length=512):
        #summary = self.pegasus_pipeline(text, max_length=max_length, truncation=True)[0]['summary_text']
        summary = self.pegasus_pipeline(text, truncation=True)[0]['summary_text']
        return summary

    def cleanse_link(self, dirty_link):
        cleaned_link = "https://www.google.com" + dirty_link.replace("/search?q=", "")
        match = re.search(r'q=(.*?)&', cleaned_link)
        if match:
            # Decode URL encoding
            extracted_url = re.sub(r'%3A', ':', match.group(1))
            extracted_url = re.sub(r'%2F', '/', extracted_url)
            return extracted_url
        else:
            return cleaned_link 

    def fetch_google_search_results(self, keyword):
        encoded_string = quote_plus(keyword)
        base_url = "https://www.google.com/search?q={}&num=35".format(encoded_string)
        req = requests.get(base_url)
        soup = BeautifulSoup(req.text, "html.parser")
        links = [a["href"] for a in soup.find_all("a")]
        cleaned_links = [self.cleanse_link(link) for link in links]
        return cleaned_links

    def visit_and_extract_text(self, urls):
        visited_urls = set()
        scraped_text = ""
        for url in urls:
            if url in visited_urls:
                continue
            visited_urls.add(url)
            try:
                # Send a GET request to the URL
                req = requests.get(url)
                # Initialize BeautifulSoup
                soup = BeautifulSoup(req.text, "html.parser")
                # Extract textual content from the parsed HTML
                text = soup.get_text()
                # Optionally, further clean the text
                # For example, remove excessive whitespaces
                text = re.sub(r'\s+', ' ', text).strip()
                print(text)
                scraped_text += text + "\n\n"  # Add a double newline for separation between URLs' text
            except Exception as e:
                print("Exception occurred:", e)
                continue
        return scraped_text

    def define_term(self, keyword):
        self.nlp.max_length = len(keyword) * 2
        doc = self.nlp(keyword)
        for ent in doc.ents:
            if ent.label_ == "PERSON" or ent.label_ == "ORG" or ent.label_ == "GPE":
                return f"{ent.text} is a {ent.label_}"
        return self.summarize_text(keyword)

    def analyze_and_provide_answer(self, merged_text, query):
        self.nlp.max_length = len(query) * 2
        doc = self.nlp(query)
        for ent in doc.ents:
            if ent.label_ == "PERSON" or ent.label_ == "ORG" or ent.label_ == "GPE":
                return self.define_term(ent.text)
        return self.summarize_text(merged_text)

    def summarize_with_t5(self, text, max_length=512, min_length=40):
        inputs = self.tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=max_length, truncation=True)
        inputs = inputs.to(self.device)
        summary_ids = self.model.generate(inputs, max_length=max_length, min_length=min_length, length_penalty=2.0, num_beams=4, early_stopping=True)
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary


if __name__ == "__main__":
    chatbot = GoogleKnowledgeGraphChatbot()
    print("Welcome to the Google Knowledge Graph Chatbot!")

    while True:
        user_input = input("Enter a question or statement (type 'exit' to quit): ")

        if user_input.lower() == 'exit':
            break

        search_results = chatbot.fetch_google_search_results(user_input)

        if not search_results:
            print("No search results found.")
            continue

        top_links = search_results[:35]

        for link in top_links:
            print(link)

        text_content = chatbot.visit_and_extract_text(top_links)

        if not text_content:
            print("No text content found among visited pages.")
            continue

        merged_text_content = text_content
        new_prompt = user_input + merged_text_content

        answer = chatbot.summarize_with_t5(new_prompt)
        print("\nT5 Response:")
        print(answer)

        """
        answer = chatbot.analyze_and_provide_answer(merged_text_content, user_input)
        print("\nChatbot's Response:")
        print(answer)
        """

        summary = chatbot.summarize_text(new_prompt)
        print("\nSummary:")
        print(summary)

        sentiment_score = TextBlob(new_prompt).sentiment.polarity
        print(f"Sentiment score: {sentiment_score}")

        if sentiment_score > 0:
            sentiment_response = "The request has a positive sentiment."
        elif sentiment_score < 0:
            sentiment_response = "The request has a negative sentiment."
        else:
            sentiment_response = "The request is neutral."

        print("\nSentiment Analysis:")
        print(sentiment_response)

