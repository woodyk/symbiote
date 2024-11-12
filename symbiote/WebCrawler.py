#!/usr/bin/env python3
#
# webcrawler.py

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import hashlib
import re
from prompt_toolkit import print_formatted_text, ANSI
from prompt_toolkit.utils import get_cwidth
from rich.console import Console
console = Console()
print = console.print
log = console.log

class WebCrawler:
    def __init__(self, browser="firefox"):
        self.visited_urls = set()
        self.pages = {}  # Store page details in a dictionary
        self.match_count = 0  # Count of matched pages
        self.crawl_count = 0  # Count of crawled pages
        self.discarded_count = 0 # Count discarded pages
        self.browser = browser
        self.base_url = None 

        # Set up the WebDriver and make it run headlessly
        if self.browser.lower() == "chrome":
            options = webdriver.ChromeOptions()
            options.headless = True
            options.add_argument("--headless")
            self.driver = webdriver.Chrome(service=webdriver.chrome.service.Service(ChromeDriverManager().install()), options=options)
        elif self.browser.lower() == "firefox" or self.browser.lower() == "gecko":
            options = webdriver.FirefoxOptions()
            options.headless = True
            options.add_argument("--headless")
            self.driver = webdriver.Firefox(service=webdriver.firefox.service.Service(GeckoDriverManager().install(), log_path='/dev/null'), options=options)
        else:
            log(f"Unsupported browser: {self.browser}")
            return ""

    def pull_website_content(self, url, search_term=None, crawl=False, depth=None):
        if self.base_url is None:
            self.base_url = url

        self.search_term = search_term
        self.crawl = crawl

        try: 
            self.driver.get(url)
        except Exception as e:
            log(f"Error fetching the website content: {e}")
            return ""
        

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Close the WebDriver 
        #self.driver.quit()

        # Remove all script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get the text content
        text = soup.get_text()
        text = re.sub(r'\n+', r'\n', text)
        text = re.sub(r'\s+', r' ', text)

        # Compute the md5 sum of the page content
        md5_sum = hashlib.md5(text.encode()).hexdigest()

        # If the md5 sum already exists in the pages dictionary, discard the page
        if md5_sum in self.pages:
            self.discarded_count += 1
            return ""

        # Check if the search_term is in the page content
        matched = False
        if self.search_term:
            search_variations = [self.search_term.lower(), self.search_term.upper(), self.search_term.capitalize()]
            if any(re.search(variation, text) for variation in search_variations):
                matched = True
                self.match_count += 1

        # Store the page details in the pages dictionary
        self.pages[md5_sum] = {
            'url': url,
            'content_type': self.driver.execute_script("return document.contentType"),
            'content': text,
            'matched': matched,
            # Add any other details you want to store
        }

        '''
        # Encapsulate the extracted text and its md5 sum within triple backticks
        text = f"URL / Website: {url}.\n\nMD5 Sum: {md5_sum}\n\n```{text}```\n\n"
        text = str(text)
        '''

        # Display a progress update
        self.crawl_count += 1
        #progress = f"\x1b[2KCount: {self.crawl_count} Discarded: {self.discarded_count} Matches: {self.match_count} URL: {url}"
        #log(progress, end='\r')

        # If crawl option is set to True, find all links and recursively pull content
        if self.crawl and (depth is None or depth > 0):
            links = soup.find_all('a')
            for link in links:
                href = link.get('href')
                absolute_url = urljoin(url, href)
                if absolute_url.startswith(self.base_url) and absolute_url not in self.visited_urls:  # Stay url sticky
                    self.visited_urls.add(absolute_url)
                    self.pull_website_content(absolute_url, search_term=self.search_term, crawl=True, depth=None if depth is None else depth - 1)

        return self.pages

if __name__ == "__main__":
    # Usage
    # Initialize a WebCrawler object
    crawler = WebCrawler(browser='firefox')

    # Define the URL you want to crawl
    url = "https://books.toscrape.com"

    # Define the search term you're looking for
    search_term = "Python"

    # Pull website content
    pages = crawler.pull_website_content(url, search_term=None, crawl=False, depth=1)

    # Print the pages
    for md5, page in pages.items():
        print(f"URL: {page['url']}")
        print(f"Content Type: {page['content_type']}")
        print(f"Content: {page['content']}")
        print(f"Search Term Matched: {page['matched']}")
        print("\n")
