#!/usr/bin/env python3
#
# symbiote/learn.py

import os
import requests
from bs4 import BeautifulSoup
import argparse
from urllib.parse import urljoin, urlparse

class WebCrawler:
    def __init__(self, url):
        self.url = url
        self.visited = set()

    def is_valid(self, url):
        """
        Checks whether `url` is a valid URL.
        """
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def get_all_website_links(self, url):
        """
        Returns all URLs that is found on `url` in which it belongs to the same website
        """
        # domain name of the URL without the protocol
        domain_name = urlparse(url).netloc
        soup = BeautifulSoup(requests.get(url).content, "html.parser")

        for a_tag in soup.findAll("a"):
            href = a_tag.attrs.get("href")
            if href == "" or href is None:
                # href empty tag
                continue
            # join the URL if it's relative (not absolute link)
            href = urljoin(url, href)
            parsed_href = urlparse(href)
            # remove URL GET parameters, URL fragments, etc.
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            if not self.is_valid(href):
                # not a valid URL
                continue
            if href in self.visited:
                # already in the set
                continue
            if domain_name not in href:
                # external link
                continue
            self.visited.add(href)
            if ".pdf" in href:
                self.download_pdf(href)

    def download_pdf(self, pdf_url):
        # Send a GET request to the PDF URL
        response = requests.get(pdf_url)

        # Get the PDF's name from its URL
        pdf_name = os.path.basename(pdf_url)

        # Write the PDF to a file
        with open(pdf_name, 'wb') as f:
            f.write(response.content)

        print(f'Downloaded: {pdf_name}')

    def crawl(self):
        # Crawl all webpages of the website
        self.get_all_website_links(self.url)
        for link in self.visited:
            self.get_all_website_links(link)

# USAGE
'''
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Crawler")
    parser.add_argument('url', type=str, help='The website to crawl')
    args = parser.parse_args()
    crawler = WebCrawler(args.url)
    crawler.crawl()
'''
