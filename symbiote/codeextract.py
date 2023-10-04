#!/usr/bin/env python3
#
# codeextract.py

import re
import os
import uuid
from collections import Counter
from pygments.lexers import get_lexer_by_name, guess_lexer, get_all_lexers
from bs4 import BeautifulSoup

class CodeBlockIdentifier:
    def __init__(self, text):
        self.text = text
        self.block_match = r'`{3}(\w+\n)(.*)`{3}|\'{3}(\w+\n)(.*)\'{3}'

    def extract_html_code_blocks(self):
        code_blocks = re.findall(self.block_match, self.text, re.DOTALL)
        soup = BeautifulSoup(self.text, 'html.parser')
        for tag in soup.find_all(['code', 'pre', 'script']):
            code_blocks.append(tag.get_text())
        return code_blocks

    def extract_markdown_code_blocks(self):
        code_blocks = re.findall(self.block_match, self.text, re.DOTALL)
        new_blocks = []
        for code in code_blocks:
            code = list(code)
            mdlang = None
            if len(code[1]) > 0:
                mdlang = code[0].rstrip("\n")
                code[0] = mdlang

            filtered = [item for item in code if item]
            new_blocks.append(filtered)

        return new_blocks

    def write_tmp_code(self, code_block, file_extension, file_name='/tmp/testcode'):
        unique_filename = f"{file_name}_{str(uuid.uuid4())}.{file_extension}"
        with open(unique_filename, 'w') as file:
            file.write(code_block)
        os.chmod(unique_filename, 0o755)
        return unique_filename

    def score_code_block(self, block):
        keywords = [item[2] for item in get_all_lexers() if item[1]]
        keywords = [item for sublist in keywords for item in sublist]
        tokens = re.findall(r'\b\w+\b', block)
        token_counts = Counter(tokens)
        score = sum(count for token, count in token_counts.items() if token in keywords)
        return score

    def identify_language(self, block, lang=None):
        print(lang)
        try:
            if lang is not None:
                # If 'lang' is provided, use it to get the lexer
                lexer = get_lexer_by_name(lang, stripall=True)
            else:
                # Try to guess the lexer
                lexer = guess_lexer(block)
            language = lexer.name
            # Extract the file extension from the lexer's filenames attribute
            file_extension = lexer.filenames[0].split('.')[-1]
            return language, file_extension
        except Exception as e:
            # Handle other exceptions gracefully, e.g., print an error message
            return None, None

    def process_text(self):
        code_blocks = self.extract_markdown_code_blocks()
        code_files = []
        for code_block in code_blocks:
            if len(code_block) > 1:
                language, extension = self.identify_language(code_block[1], lang=code_block[0])
                code = code_block[1]
            else:
                language, extension = self.identify_language(code_block[0])
                code = code_block[0]

            file_path = self.write_tmp_code(code, extension)
            code_files.append(file_path)

        return code_files
'''
Usage:
identifier = CodeBlockIdentifier(text)
file_list = identifier.process_text()
'''