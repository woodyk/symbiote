#!/usr/bin/env python3
#
# tt.py

import requests
from bs4 import BeautifulSoup
from googlesearch import search

class GoogleTextFetcher:
    def __init__(self, num_results=5):
        """
        Initializes the GoogleTextFetcher with a specified number of search results.
        
        Args:
        num_results (int): Number of search results to fetch and extract text from.
        """
        self.num_results = num_results

    def fetch_links(self, query):
        """
        Performs a Google search and fetches the top N links based on the query.
        
        Args:
        query (str): The search term to query.
        
        Returns:
        list: A list of URLs.
        """
        # Perform the search using googlesearch-python library
        return list(search(query, num_results=self.num_results))

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
    

