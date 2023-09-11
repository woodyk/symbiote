#!/usr/bin/env python3
#
# webcrawler.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from bs4 import BeautifulSoup
import hashlib
import re
from prompt_toolkit import print_formatted_text, ANSI
from prompt_toolkit.utils import get_cwidth

class WebCrawler:
    def __init__(self):
        self.visited_urls = set()
        self.pages = {}  # Store page details in a dictionary
        self.match_count = 0  # Count of matched pages
        self.crawl_count = 0  # Count of crawled pages

    def pull_website_content(self, url, search_term=None, browser="firefox", crawl=False):
        # Set up the WebDriver and make it run headlessly
        if browser.lower() == "chrome":
            options = ChromeOptions()
            options.headless = True
            driver = webdriver.Chrome(options=options)
        elif browser.lower() == "firefox":
            options = FirefoxOptions()
            options.headless = True
            driver = webdriver.Firefox(options=options)
        else:
            print(f"Unsupported browser: {browser}")
            return ""

        try: 
            driver.get(url)
        except Exception as e:
            print(f"Error fetching the website content: {e}")
            return ""

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # If crawl option is set to True, find all links and recursively pull content
        if crawl:
            links = soup.find_all('a')
            for link in links:
                href = link.get('href')
                if href and href.startswith(url):  # Stay url sticky
                    # Deduplication: Only visit the url if it's not already visited
                    if href not in self.visited_urls:
                        self.visited_urls.add(href)
                        self.pull_website_content(href, search_term=search_term, browser=browser, crawl=crawl)

        # Close the WebDriver 
        driver.quit()

        # Remove all script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get the text content
        text = soup.get_text()

        # Remove extra whitespace and newlines
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        # Compute the md5 sum of the page content
        md5_sum = hashlib.md5(text.encode()).hexdigest()

        # If the md5 sum already exists in the pages dictionary, discard the page
        if md5_sum in self.pages:
            print(f"Discarding page {url} due to matched md5sum.")
            return ""

        # Check if the search_term is in the page content
        matched = False
        if search_term:
            search_variations = [search_term.lower(), search_term.upper(), search_term.capitalize()]
            if any(re.search(variation, text) for variation in search_variations):
                matched = True
                self.match_count += 1

        # Store the page details in the pages dictionary
        self.pages[md5_sum] = {
            'url': url,
            'content_type': driver.execute_script("return document.contentType"),
            'content': text,
            'matched': matched,
            # Add any other details you want to store
        }

        # Encapsulate the extracted text and its md5 sum within triple backticks
        text = f"URL / Website: {url}.\n\nMD5 Sum: {md5_sum}\n\n```{text}```\n\n"
        text = str(text)

        # Display a progress update
        self.crawl_count += 1
        progress = f"Crawled: {self.crawl_count} Search matches: {self.match_count}\n{url}"
        print_formatted_text(ANSI(f'\x1b[2K\r{progress}'), end='')

        return self.pages

# Initialize a WebCrawler object
crawler = WebCrawler()

# Define the URL you want to crawl
url = "https://books.toscrape.com"

# Define the search term you're looking for
search_term = "Python"

# Pull website content
pages = crawler.pull_website_content(url, search_term, browser="firefox", crawl=True)

# Print the pages
for md5, page in pages.items():
    print(f"URL: {page['url']}")
    print(f"Content Type: {page['content_type']}")
    print(f"Content: {page['content']}")
    print(f"Search Term Matched: {page['matched']}")
    print("\n")

