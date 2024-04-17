#!/usr/bin/env python3
#
# tt.py

import re
import requests
from bs4 import BeautifulSoup
import urllib.parse as up

class GoogleTextFetcher:
    def __init__(self, num_results=5):
        """
        Initializes the GoogleTextFetcher with a specified number of search results.
        
        Args:
        num_results (int): Number of search results to fetch and extract text from.
        """
        self.num_results = num_results

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

    def fetch_links(self, keyword, num_results=10):
        encoded_string = up.quote_plus(keyword)
        base_url = f"https://www.google.com/search?q={encoded_string}&num={num_results}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        req = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(req.text, "html.parser")
        links = [a["href"] for a in soup.find_all("a")]
        cleaned_links = [self.cleanse_link(link) for link in links]
        return cleaned_links

    def fetch_text_from_url(self, url):
        """
        Fetches the textual content of a webpage given its URL.
        
        Args:
        url (str): URL of the webpage to fetch the text from.
        
        Returns:
        str: Textual content of the webpage.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extracts all text from paragraphs
            text = ' '.join([p.get_text() for p in soup.find_all('p')])
            return text
        except requests.RequestException as e:
            return f"Failed to retrieve content from {url}: {str(e)}"

    def perform_search_and_fetch_text(self, query):
        """
        Searches Google for the query and prints text from the top N links.
        
        Args:
        query (str): The search query to perform.
        """
        results = ""
        links = self.fetch_links(query)
        for i, url in enumerate(links, 1):
            print(f"Text from link {i}: {url}")
            text = self.fetch_text_from_url(url)
            results += text

        return results

# Example usage:
if __name__ == "__main__":
    gtf = GoogleTextFetcher(num_results=10)
    results = gtf.perform_search_and_fetch_text("Python programming tips")
    print(results)
    

