#!/usr/bin/env python3
import spacy
import ast
import re
import sys
import subprocess
import json
import pprint
from pygments.lexers import guess_lexer_for_filename, guess_lexer, get_all_lexers
from pygments.util import ClassNotFound

from pygments.style import Style
from collections import Counter
from transformers import pipeline

filename = sys.argv[1]

nlp = spacy.load("en_core_web_sm")
nlp.max_length = 5000000

# Initialize a named entity recognition pipeline
ner_pipe = pipeline('ner')

# Initialize a question answering pipeline
qa_pipe = pipeline('question-answering')

def is_json(filename):
    try:
        with open(filename, 'r') as f:
            json.load(f)
        return True
    except ValueError:
        return False
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return False

def lint_file(filename):
    # Read the file contents
    with open(filename, 'r') as file:
        code = file.read()

    # Guess the lexer based on the filename and the code
    try:
        lexer = guess_lexer_for_filename(filename, code)
    except ClassNotFound:
        print(f'Could not determine the language of the file: {filename}')
        return None

    # Choose the linter command based on the lexer name
    if 'python' in lexer.name.lower():
        command = ['pylint', filename]
    elif 'javascript' in lexer.name.lower():
        command = ['eslint', filename]
    elif 'java' in lexer.name.lower():
        command = ['checkstyle', filename]
    elif 'c++' in lexer.name.lower() or 'c' in lexer.name.lower():
        command = ['cppcheck', filename]
    elif 'shell' in lexer.name.lower():
        command = ['shellcheck', filename]
    elif 'php' in lexer.name.lower():
        command = ['php', '-l', filename]
    elif 'ruby' in lexer.name.lower():
        command = ['ruby', '-c', filename]
    else:
        print(f'Unsupported language: {lexer.name}')
        return None

    # Run the linter command
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Return the linter output
    return process.stdout.decode()


def get_contents(filename):
    # Read the file contents
    with open(filename, 'r') as file:
        file_contents = file.read()


    return file_contents

def get_exif_data(filename):
    try:
        result = subprocess.run(['exiftool', '-j', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        exif_data = json.loads(result.stdout.decode())[0]  # exiftool outputs JSON data, so we parse it
        return exif_data

    except Exception as e:
        print(f'error: {e}')
        return None

def read_file(filename):
    with open(filename, 'r') as file:
        text = file.read()

    return text

def is_software(text, filename):
    # Define weights for each scoring component
    weights = {
        'keyword_score': 0.2,
        'pattern_score': 0.2,
        'comment_score': 0.2,
        'code_percentage_score': 0.2,
        'filename_score': 0.1,
        'lexer_score': 0.1
    }

    # Initialize scores
    scores = {
        'keyword_score': 0,
        'pattern_score': 0,
        'comment_score': 0,
        'code_percentage_score': 0,
        'filename_score': 0,
        'lexer_score': 0
    }

    # Get all keywords from all lexers
    keywords = [item[2] for item in get_all_lexers() if item[1]]
    keywords = [item for sublist in keywords for item in sublist]

    # Find all tokens in the block
    tokens = re.findall(r'\b\w+\b', text)
    token_counts = Counter(tokens)

    # Calculate the score based on the presence of keywords
    scores['keyword_score'] = sum(count for token, count in token_counts.items() if token in keywords) / len(tokens)

    # Calculate the score based on the presence of import statements, function or class definitions, and common programming keywords
    patterns = [r'\bimport\b', r'\bdef\b', r'\bclass\b', r'\bif\b', r'\belse\b', r'\bfor\b', r'\bwhile\b', r'\breturn\b', r'\bin\b', r'\btry\b', r'\bexcept\b']
    scores['pattern_score'] = sum(1 for pattern in patterns if re.search(pattern, text)) / len(tokens)

    # Calculate the score based on the presence of comment lines
    comment_patterns = [r'//', r'#', r'"""', r'/*', r"'''"]
    scores['comment_score'] = sum(1 for pattern in comment_patterns if re.search(pattern, text)) / len(tokens)

    # Calculate the percentage of code vs other text
    code_percentage = len(re.findall(r'\b\w+\b', text)) / len(text.split())
    scores['code_percentage_score'] = code_percentage

    # Use Pygments to guess the language
    try:
        guess_lexer(text)
        scores['lexer_score'] = 1
    except:
        pass

    # Use Pygments to get a lexer for the filename
    try:
        get_lexer_for_filename(filename)
        scores['filename_score'] = 1
    except:
        pass

    # Calculate the final score as the weighted sum of the scores
    final_score = sum(scores[key] * weights[key] for key in scores)

    return final_score

def generate_code_qa(code, filename):
    tree = ast.parse(code)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]

    qa_pairs = []
    qa_pairs.append((f"How many functions are in {filename}?", len(functions)))
    qa_pairs.append((f"How many libraries are imported in {filename}?", len(imports)))

    for function in functions:
        qa_pairs.append((f"What does the function '{function.name}' do in {filename}?", "The function's behavior depends on its implementation in the code."))
        qa_pairs.append((f"How many arguments does the function '{function.name}' in {filename} take?", len(function.args.args)))
        qa_pairs.append((f"What are the arguments of the function '{function.name}' in {filename}?", ', '.join(arg.arg for arg in function.args.args)))

    for class_ in classes:
        qa_pairs.append((f"What is the purpose of the class '{class_.name}' in {filename}?", "The class's purpose depends on its implementation in the code."))

    for import_ in imports:
        if isinstance(import_, ast.Import):
            qa_pairs.append((f"What modules are imported in {filename}?", ', '.join(alias.name for alias in import_.names)))
        elif isinstance(import_, ast.ImportFrom):
            qa_pairs.append((f"What is imported from the module '{import_.module}' in {filename}?", ', '.join(alias.name for alias in import_.names)))

    # Specific questions about certain libraries and functions
    if any('pygments' in alias.name for import_ in imports for alias in import_.names):
        qa_pairs.append(("What does the library 'pygments' do?", "The library 'pygments' is responsible for syntax highlighting and code recognition."))

    if any(function.name == 'extract_html_code_blocks' for function in functions):
        qa_pairs.append(("What function pulls out the content of text in {filename}?", "The function 'extract_html_code_blocks' is responsible for that."))

    return qa_pairs

def generate_qa(data, filename):
    '''
    # Understand the data
    entities = ner_pipe(data_description)
    
    questions = []
    for entity in entities:
        # Generate questions based on entities
        questions = [f"What is the {entity['entity']}?" for entity in entities]

    # Find answers in the data
    qa_pairs = []
    if questions:
        for question in questions:
            answer = qa_pipe(question=question, context=data)
            qa_pairs.append((question, answer))
            print(question, answer)
    '''

    doc = nlp(data)
    qa_pairs = []
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            qa_pairs.append((f"Who is {ent.text}?", ent.text))
        elif ent.label_ == "GPE":
            qa_pairs.append((f"Where is {ent.text}?", ent.text))
        elif ent.label_ == "DATE":
            qa_pairs.append((f"When is {ent.text}?", ent.text))
        elif ent.label_ == "ORG":
            qa_pairs.append((f"What is {ent.text}?", ent.text))
        elif ent.label_ == "NORP":
            qa_pairs.append((f"What nationality is {ent.text}?", ent.text))
        elif ent.label_ == "EVENT":
            qa_pairs.append((f"What is the event {ent.text}?", ent.text))
        elif ent.label_ == "WORK_OF_ART":
            qa_pairs.append((f"What is the work of art {ent.text}?", ent.text))
        elif ent.label_ == "LAW":
            qa_pairs.append((f"What is the law {ent.text}?", ent.text))
        elif ent.label_ == "PRODUCT":
            qa_pairs.append((f"What is the product {ent.text}?", ent.text))
        elif ent.label_ == "LANGUAGE":
            qa_pairs.append((f"What is the language {ent.text}?", ent.text))
        elif ent.label_ == "FAC":
            qa_pairs.append((f"What is the facility {ent.text}?", ent.text))
        elif ent.label_ == "LOC":
            qa_pairs.append((f"What is the location {ent.text}?", ent.text))
        elif ent.label_ == "QUANTITY":
            qa_pairs.append((f"What is the quantity of {ent.text}?", ent.text))
        elif ent.label_ == "PERCENT":
            qa_pairs.append((f"What is the percentage of {ent.text}?", ent.text))
        elif ent.label_ == "MONEY":
            qa_pairs.append((f"What is the amount of money {ent.text}?", ent.text))
        elif ent.label_ == "TIME":
            qa_pairs.append((f"What is the time {ent.text}?", ent.text))


    '''
    qa_pairs = []
    qa_pairs.append(("What is the name of the file?", file_data['FileName']))
    qa_pairs.append(("What is the size of the file?", file_data['FileSize']))
    qa_pairs.append(("What is the file type of the file?", file_data['FileType']))
    qa_pairs.append(("What is the MIME type of the file?", file_data['MIMEType']))
    qa_pairs.append(("What are the file permissions of the file?", file_data['FilePermissions']))
    qa_pairs.append(("When was the file last modified?", file_data['FileModifyDate']))
    qa_pairs.append(("When was the file last accessed?", file_data['FileAccessDate']))
    qa_pairs.append(("When was the inode of the file last changed?", file_data['FileInodeChangeDate']))
    qa_pairs.append(("What is the directory of the file?", file_data['Directory']))
    qa_pairs.append(("What is the ExifTool Version Number used for the file?", file_data['ExifToolVersion']))
    '''
    return qa_pairs

lints = lint_file(filename)
print(lints)

exif = get_exif_data(filename)
print(exif)
content = get_contents(filename)
print(content)

# Convert the EXIF data to a string
exif_string = pprint.pformat(exif)
# Prepend the EXIF data to the file contents
c_content = f"exif {filename}\n---\n{exif}\n---\n\ncontents {filename}\n---\n{content}\n---\n"

json_check = False
score = 0
json_check = is_json(filename)

if json_check:
    score = is_software(content, filename)
    print(score)

if score >= 4:
    qa_pairs = generate_code_qa(content, filename) 
    for i in qa_pairs:
        print(i)

qa_pairs = generate_qa(c_content, filename)
for i in qa_pairs:
    print(i)
