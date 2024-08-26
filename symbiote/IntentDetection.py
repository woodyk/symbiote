#!/usr/bin/env python3
#
# IntentDetection.py

import re
import os
import requests
import json
import sys
import logging
import warnings
import math
import numpy as np
from collections import defaultdict
from bs4 import BeautifulSoup
from transformers import pipeline, GPT2TokenizerFast
from transformers import AutoTokenizer
from huggingface_hub import login
from typing import List, Dict

# Suppress unwanted logging messages
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
warnings.simplefilter(action='ignore', category=FutureWarning)

# Authenticate with Hugging Face API
api_token = os.getenv("HUGGINGFACE_API_KEY")
login(token=api_token)
tokenizers_parallelism='false'
os.environ["TOKENIZERS_PARALLELISM"] = tokenizers_parallelism


# Constants for thresholds and penalties
NEUTRAL_DOMINANCE_THRESHOLD = 0.75
NEGATIVE_EMOTION_THRESHOLD = 0.05
HIGH_VARIABILITY_THRESHOLD = 0.15
LOW_AVERAGE_THRESHOLD = 0.05
SENTIMENT_THRESHOLD = 0.7
MIXED_SENTIMENT_PENALTY = 0.5
MASKING_PENALTY = 0.75
LOW_INTENSITY_VARIABILITY_PENALTY = 0.5

def get_dominant_emotion(emotion_scores: Dict[str, float]) -> str:
    sorted_emotions = sorted(emotion_scores.items(), key=lambda item: item[1], reverse=True)
    if sorted_emotions[0][0] == 'neutral' and len(sorted_emotions) > 1:
        return sorted_emotions[1][0]
    return sorted_emotions[0][0]

def calculate_entropy(emotion_scores: Dict[str, float]) -> float:
    total_score = sum(emotion_scores.values())
    if total_score == 0:
        return 0.0
    entropy = -sum((score / total_score) * math.log2(score / total_score) for score in emotion_scores.values() if score > 0)
    return entropy

def aggregate_emotion_scores(analysis_results: List[Dict[str, Dict[str, float]]]) -> Dict[str, Dict[str, float]]:
    emotion_data = defaultdict(list)
    for result in analysis_results:
        for emotion, score in result['emotion_scores'].items():
            emotion_data[emotion].append(score)
    aggregated_emotions = {}
    for emotion, scores in emotion_data.items():
        aggregated_emotions[emotion] = {
            "min": np.min(scores),
            "max": np.max(scores),
            "average": np.mean(scores),
            "std_dev": np.std(scores)
        }
    return aggregated_emotions

def calculate_aggregated_sentiment_stats(analysis_results: List[Dict[str, Dict[str, float]]]) -> Dict[str, Dict[str, float]]:
    sentiment_data = defaultdict(list)
    for result in analysis_results:
        sentiment = result['sentiment']
        sentiment_score = result['sentiment_score']
        sentiment_data[sentiment].append(sentiment_score)
    sentiment_stats = {}
    for sentiment, scores in sentiment_data.items():
        sentiment_stats[sentiment] = {
            "min": np.min(scores),
            "max": np.max(scores),
            "average": np.mean(scores),
            "std_dev": np.std(scores)
        }
    return sentiment_stats

def determine_dominant_sentiment(analysis_results: List[Dict[str, Dict[str, float]]]) -> str:
    sentiment_weights = defaultdict(float)
    for result in analysis_results:
        sentiment_weights[result['sentiment']] += result['sentiment_score']
    return max(sentiment_weights, key=sentiment_weights.get)

def measure_intent(analysis_results: List[Dict[str, Dict[str, float]]]) -> Dict[str, Dict[str, float]]:
    intent_score = 100 # Assume truth 
    previous_sentiment = None
    previous_emotion = None

    for i, result in enumerate(analysis_results):
        dominant_emotion = get_dominant_emotion(result['emotion_scores'])
        dominant_emotion_score = result['emotion_scores'][dominant_emotion]
        sentiment = result['sentiment']
        sentiment_score = result['sentiment_score']
        entropy = calculate_entropy(result['emotion_scores'])

        # Emotional and Sentiment Consistency Check
        if sentiment == 'positive' and dominant_emotion in ['anger', 'disgust', 'fear', 'sadness', 'disapproval', 'realization']:
            intent_score -= 2.5 * dominant_emotion_score
        elif sentiment == 'negative' and dominant_emotion in ['joy', 'surprise', 'admiration', 'amusement', 'approval']:
            intent_score -= 2.5 * dominant_emotion_score
        elif sentiment == 'neutral' and dominant_emotion in ['anger', 'disgust', 'fear', 'sadness', 'disapproval', 'realization']:
            intent_score -= 2 * dominant_emotion_score
        elif sentiment == 'neutral' and dominant_emotion in ['joy', 'surprise', 'admiration', 'amusement', 'approval']:
            intent_score += 2 * dominant_emotion_score
        elif sentiment == 'negative' and dominant_emotion in ['anger', 'disgust', 'fear', 'sadness', 'disapproval', 'realization']:
            intent_score += 2.5 * dominant_emotion_score
        elif sentiment == 'positive' and dominant_emotion in ['joy', 'surprise', 'admiration', 'amusement', 'approval']:
            intent_score += 2.5 * dominant_emotion_score


        # Adjust based on emotional distribution (entropy)
        if entropy > 1.5:
            intent_score -= 1
        elif entropy < 0.5:
            intent_score += 1


        # Adjust based on narrow gaps between dominant and secondary emotions
        second_highest_score = sorted(result['emotion_scores'].values(), reverse=True)[1]
        if dominant_emotion_score - second_highest_score < 0.1:
            intent_score -= 1


        # Adjust based on changes in sentiment between sentences
        if i > 0:
            if sentiment != previous_sentiment or dominant_emotion != previous_emotion:
                intent_score -= 1.0
            if sentiment == previous_sentiment and dominant_emotion == previous_emotion:
                intent_score += 0.5

        previous_sentiment = sentiment
        previous_emotion = dominant_emotion

    # Additional Penalties for Mixed Sentiments
    sentiment_stats = calculate_aggregated_sentiment_stats(analysis_results)
    if sentiment_stats['positive']['average'] > SENTIMENT_THRESHOLD and sentiment_stats['negative']['average'] > SENTIMENT_THRESHOLD:
        intent_score -= MIXED_SENTIMENT_PENALTY

    # Check for Emotional Masking
    aggregated_emotions = aggregate_emotion_scores(analysis_results)
    if aggregated_emotions['neutral']['average'] > NEUTRAL_DOMINANCE_THRESHOLD:
        if any(aggregated_emotions[emotion]['average'] > NEGATIVE_EMOTION_THRESHOLD for emotion in ['anger', 'disgust', 'sadness']):
            intent_score -= MASKING_PENALTY

    # Check for Low-Intensity, High-Variability Emotions
    for emotion in aggregated_emotions:
        if aggregated_emotions[emotion]['average'] < LOW_AVERAGE_THRESHOLD and aggregated_emotions[emotion]['std_dev'] > HIGH_VARIABILITY_THRESHOLD:
            intent_score -= LOW_INTENSITY_VARIABILITY_PENALTY

    # Clamp the intent score to a reasonable range to avoid extreme outputs
    intent_score = max(min(intent_score, 100), 0)

    # Normalize the intent score to a 0-1 range where 0 is deceptive and 1 is truthful
    inferred_intent_score = round(intent_score / 100, 4) 

    # Determine the dominant intent based on the normalized score
    dominant_intent = "truthful" if inferred_intent_score >= 0.5 else "deceptive"

    return {
        "inferred_intent_score": round(inferred_intent_score, 5),
        "dominant_intent": dominant_intent,
        "emotion_scores": aggregated_emotions,
        "sentiment": determine_dominant_sentiment(analysis_results),
        "sentiment_stats": sentiment_stats
    }

def split_text_into_sentences(text: str) -> List[str]:
    sentence_endings = re.compile(r'(?<=[.!?])(?=[A-Z]|\s|$)')
    sentences = sentence_endings.split(text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]

def analyze_emotions(text: str) -> List[Dict[str, Dict[str, float]]]:
    """
    Processes each sentence in the text to extract the full distribution of emotions.

    :param text: The input text.
    :return: A list of dictionaries, each containing the sentence and a dictionary of emotion scores.
    """
    classifier = pipeline(task="text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None)
    sentiment_analyzer = pipeline(task="sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

    tokenizer = AutoTokenizer.from_pretrained("SamLowe/roberta-base-go_emotions")
    max_length = tokenizer.model_max_length

    sentences = split_text_into_sentences(text)

    analysis_results = []
    for sentence in sentences:
        # Tokenize the sentence
        encoded_input = tokenizer(sentence, truncation=True, max_length=max_length, return_tensors="pt")

        # Check if the tokenized sentence length exceeds max_length
        if encoded_input["input_ids"].shape[1] > max_length:
            print(f"Truncated sentence: {sentence}")

        # Get emotion outputs and sentiment outputs
        emotion_outputs = classifier([sentence[:max_length]])[0]
        sentiment_output = sentiment_analyzer(sentence[:max_length])[0]

        # Convert emotion outputs to a dictionary with emotion labels as keys and scores as values
        emotion_scores = {emotion['label']: emotion['score'] for emotion in emotion_outputs}

        analysis_results.append({
            "sentence": sentence,
            "emotion_scores": emotion_scores,
            "sentiment": sentiment_output['label'].lower(),
            "sentiment_score": sentiment_output['score']
        })

    return analysis_results
"""
def analyze_emotions(text: str) -> List[Dict[str, Dict[str, float]]]:
    classifier = pipeline(task="text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None)
    sentiment_analyzer = pipeline(task="sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

    sentences = split_text_into_sentences(text)

    analysis_results = []
    for sentence in sentences:
        emotion_outputs = classifier([sentence])[0]
        sentiment_output = sentiment_analyzer(sentence)[0]

        # Convert emotion outputs to a dictionary with emotion labels as keys and scores as values
        emotion_scores = {emotion['label']: emotion['score'] for emotion in emotion_outputs}

        analysis_results.append({
            "sentence": sentence,
            "emotion_scores": emotion_scores,  # Full distribution of emotion scores
            "sentiment": sentiment_output['label'].lower(),
            "sentiment_score": sentiment_output['score']
        })

    return analysis_results
"""
def split_text_into_chunks(text: str, max_tokens: int = 500) -> List[str]:
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    tokens = tokenizer.encode(text)
    chunks = [tokens[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]
    text_chunks = [tokenizer.decode(chunk) for chunk in chunks]
    return text_chunks

def download_text_from_url(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = "\n".join([para.get_text() for para in paragraphs])
        return text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while trying to download the text: {e}")
        return ""

def process_article(text: str, model_name: str = "hamzab/roberta-fake-news-classification") -> List[dict]:
    clf = pipeline("text-classification", model=model_name, tokenizer=model_name)
    chunks = split_text_into_chunks(text)
    results = []
    for chunk in chunks:
        result = clf(chunk)
        results.append(result)
    return results

if __name__ == "__main__":
    url = sys.argv[1]

    text = download_text_from_url(url)

    MODEL = "jy46604790/Fake-News-Bert-Detect"
    MODEL = "yanzcc/FakeNewsClassifier_Longformer"
    MODEL = "vishalk4u/liar_binaryclassifier_bert_cased"
    MODEL = "Zain6699/intent-classifier-establish_credibility"
    MODEL = "armansakif/bengali-fake-news"
    MODEL = "eligapris/lie-detection-sentiment-analysis" # login needed
    MODEL = "dlentr/lie_detection_distilbert"
    MODEL = "Giyaseddin/distilbert-base-cased-finetuned-fake-and-real-news-dataset"
    MODEL = "hamzab/roberta-fake-news-classification"

    if text:
        news_classification = process_article(text, model_name=MODEL)
        print(json.dumps(news_classification, indent=4))

        MODEL = "openai-community/roberta-base-openai-detector" # detect if written by AI
        ai_detection = process_article(text, model_name=MODEL)
        print(json.dumps(ai_detection, indent=4))

        analysis_results = analyze_emotions(text)
        intent = measure_intent(analysis_results)
        #print(json.dumps(analysis_results, indent=4))
        print(json.dumps(intent, indent=4))
    else:
        print("Failed to download or process the text.")

