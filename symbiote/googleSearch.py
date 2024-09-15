#!/usr/bin/env python3
#
# tt.py
import os
import requests
import urllib
from bs4 import BeautifulSoup

class googleSearch:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY") 
        self.cse_id = os.getenv("GOOGLE_API_CX")

    def fetch_links(self, query, num_results=10):
        query = urllib.parse.quote(query)
        search_url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.cse_id}&q={query}&num={num_results}"
        try:
            response = requests.get(search_url)
            response.raise_for_status()
            search_results = response.json()
            links = [item['link'] for item in search_results.get('items', [])]
            return links
        except requests.RequestException as e:
            print(f"Failed to fetch search results: {e}")
            return []

    def fetch_text_from_urls(self, urls):
        all_text = ""
        for url in urls:
            try:
                response = requests.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                text = ' '.join(p.text for p in soup.find_all('p'))
                all_text += text + " "  # Append text and add a space to separate content from different URLs
            except requests.RequestException as e:
                print(f"Failed to fetch page content from {url}: {e}")
                continue
        return all_text.strip()  # Remove any trailing whitespace

if __name__ == "__main__":
    # Usage example
    search_engine = googleSearch()
    links = search_engine.fetch_links("site:w3schools.com python")
    all_text = search_engine.fetch_text_from_urls(links)
    print(all_text)
