#!/usr/bin/env python3
from transformers import pipeline

# Initialize a named entity recognition pipeline
ner_pipe = pipeline('ner')

# Initialize a question answering pipeline
qa_pipe = pipeline('question-answering')

def generate_qa(data_description, data):
    # Understand the data
    entities = ner_pipe(data_description)

    # Generate questions based on entities
    questions = [f"What is the {entity['entity']}?" for entity in entities]

    # Find answers in the data
    qa_pairs = []
    for question in questions:
        answer = qa_pipe(question=question, context=data)
        qa_pairs.append((question, answer))

    return qa_pairs

