#!/usr/bin/env python3
#
# extract_code.py

import re
from collections import Counter
from pygments.lexers import guess_lexer, get_all_lexers
from bs4 import BeautifulSoup

class CodeBlockIdentifier:
    def __init__(self, text):
        self.text = text

    def extract_code_blocks(self):
        code_blocks = re.findall(r'```(.*?)```', self.text, re.DOTALL)
        soup = BeautifulSoup(self.text, 'html.parser')
        for tag in soup.find_all(['code', 'pre', 'script']):
            code_blocks.append(tag.get_text())
        return code_blocks

    def score_code_block(self, block):
        keywords = [item[2] for item in get_all_lexers() if item[1]]
        keywords = [item for sublist in keywords for item in sublist]
        tokens = re.findall(r'\b\w+\b', block)
        token_counts = Counter(tokens)
        score = sum(count for token, count in token_counts.items() if token in keywords)
        return score

    def identify_language(self, block):
        try:
            lexer = guess_lexer(block)
            return lexer.name
        except Exception:
            return "Unknown"

    def process_text(self):
        code_blocks = self.extract_code_blocks()
        for block in code_blocks:
            score = self.score_code_block(block)
            language = self.identify_language(block)
            print(f"Code block:\n{block}\nScore: {score}\nLanguage: {language}\n")

'''
Usage:
Create an instance of the class with the text to be processed.

identifier = CodeBlockIdentifier(text)
identifier.process_text()
'''
