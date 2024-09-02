#!/usr/bin/env python3
#
# IntentDetection.py

import os
import requests
import json
import logging
import math
import numpy as np
import re
from collections import defaultdict
from bs4 import BeautifulSoup
from transformers import pipeline, GPT2TokenizerFast, AutoTokenizer
from transformers import logging as hf_logging
from huggingface_hub import login
from typing import List, Dict
import warnings
import sys
import contextlib
from textstat import textstat

# Suppress all warnings and set logging to ERROR level
warnings.filterwarnings("ignore")
hf_logging.set_verbosity_error()
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# Suppress stdout entirely using context manager
@contextlib.contextmanager
def suppress_stdout():
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

class FakeNewsDetector:
    def __init__(self, api_key: str = None, tokenizers_parallelism: str = 'false'):
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        if self.api_key:
            self._authenticate()
        os.environ["TOKENIZERS_PARALLELISM"] = tokenizers_parallelism

        # Initialize models
        with suppress_stdout():
            self.emotion_model = pipeline(task="text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None)
            self.sentiment_model = pipeline(task="sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
            self.fake_news_model = pipeline("text-classification", model="hamzab/roberta-fake-news-classification")
            self.ai_detection_model = pipeline("text-classification", model="openai-community/roberta-base-openai-detector")
            self.tokenizer = AutoTokenizer.from_pretrained("SamLowe/roberta-base-go_emotions")
            self.max_length = self.tokenizer.model_max_length

    def _authenticate(self):
        with suppress_stdout():
            login(token=self.api_key, add_to_git_credential=False)

    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        Analyzes the text for fake news potential, AI-generated text potential, and emotions,
        and consolidates the results into a single deception score.
        """
        fake_news_score = self._process_text(text, self.fake_news_model, fake_label="FAKE")
        ai_detection_score = self._process_text(text, self.ai_detection_model, fake_label="AI-GENERATED")
        emotion_results = self.analyze_emotions(text)
        intent_results = self.measure_intent(emotion_results)
        complexity_score = self.analyze_text_complexity(text)

        # Combine the results into a single deception score
        deception_score, explanation = self._calculate_deception_score(
            fake_news_score, ai_detection_score, intent_results, complexity_score
        )

        return {
            "deception_score": deception_score,
            "fake_news_probability": fake_news_score,
            "ai_generated_probability": ai_detection_score,
            "intent_analysis": intent_results,
            "complexity_score": complexity_score,
            "explanation": explanation
        }

    def _process_text(self, text: str, model, fake_label: str) -> float:
        """
        Generic method to process text using a given model and calculate an average score.
        """
        chunks = self.split_text_into_chunks(text)
        scores = []
        for chunk in chunks:
            result = model(chunk)
            if result[0]['label'] == fake_label:
                scores.append(result[0]['score'])  # Use the score as is for the fake label
            else:
                scores.append(1 - result[0]['score'])  # Invert the score for non-fake labels
        return np.mean(scores)

    def analyze_emotions(self, text: str) -> List[Dict[str, Dict[str, float]]]:
        sentences = self.split_text_into_sentences(text)
        analysis_results = []
        for sentence in sentences:
            emotion_outputs = self.emotion_model(sentence[:self.max_length])[0]
            sentiment_output = self.sentiment_model(sentence[:self.max_length])[0]

            emotion_scores = {emotion['label']: emotion['score'] for emotion in emotion_outputs}
            analysis_results.append({
                "sentence": sentence,
                "emotion_scores": emotion_scores,
                "sentiment": sentiment_output['label'].lower(),
                "sentiment_score": sentiment_output['score']
            })
        return analysis_results

    def measure_intent(self, analysis_results: List[Dict[str, Dict[str, float]]]) -> Dict[str, Dict[str, float]]:
        intent_score = 100
        explanations = []
        previous_sentiment, previous_emotion = None, None

        for i, result in enumerate(analysis_results):
            dominant_emotion = self.get_dominant_emotion(result['emotion_scores'])
            entropy = self.calculate_entropy(result['emotion_scores'])

            intent_score, explanation = self.adjust_intent_score(
                intent_score, result['sentiment'], dominant_emotion, result['emotion_scores'][dominant_emotion],
                entropy, i, previous_sentiment, previous_emotion, result
            )
            explanations.extend(explanation)
            previous_sentiment, previous_emotion = result['sentiment'], dominant_emotion

        intent_score = self.apply_final_adjustments(intent_score, analysis_results)
        inferred_intent_score = round(intent_score / 100, 4)

        # Correcting the threshold for determining dominant intent
        dominant_intent = "deceptive" if inferred_intent_score > 0.5 else "truthful"

        return {
            "inferred_intent_score": inferred_intent_score,
            "dominant_intent": dominant_intent,
            "emotion_scores": self.aggregate_emotion_scores(analysis_results),
            "sentiment": self.determine_dominant_sentiment(analysis_results),
            "sentiment_stats": self.calculate_aggregated_sentiment_stats(analysis_results),
            "explanation": explanations
        }

    def _calculate_deception_score(self, fake_news_score: float, ai_detection_score: float, intent_results: Dict[str, float], complexity_score: float) -> float:
        """
        Combine all features, including new ones, to calculate a final deception score.
        """
        intent_score = intent_results["inferred_intent_score"]

        # Detailed explanation of the score calculation
        explanation = []

        # Fake News Analysis
        explanation.append(f"Fake News Analysis: The text was analyzed for potential fake news. The resulting score was {fake_news_score:.4f}, where 1 indicates a high likelihood of being fake and 0 indicates a high likelihood of being truthful.")

        # AI Writing Detection
        explanation.append(f"AI Writing Detection: The text was checked to see if it was generated by AI. The resulting score was {ai_detection_score:.4f}, where 1 indicates a high likelihood of being AI-generated and 0 indicates a high likelihood of being human-written.")

        # Intent Analysis
        explanation.append(f"Intent Analysis: The text's sentiment and emotion were analyzed to infer intent. The inferred intent score was {intent_score:.4f}, where 0 indicates truthful intent and 1 indicates deceptive intent.")

        # Text Complexity Analysis
        explanation.append(f"Text Complexity Analysis: The text was evaluated for complexity using readability metrics and sentence/word length. The complexity score was {complexity_score:.4f}, where higher values indicate higher complexity.")

        # Example of a more complex weighting scheme
        combined_score = (0.4 * fake_news_score +
                          0.3 * ai_detection_score +
                          0.2 * intent_score +  # Adjusted: intent score as is
                          0.1 * complexity_score)

        explanation.append(f"The final deception score is calculated by weighting the scores from each analysis: "
                           f"40% Fake News Analysis, 30% AI Writing Detection, 20% Intent Analysis, and 10% Text Complexity. "
                           f"The final deception score is {combined_score:.4f}, where 1 indicates high likelihood of deception and 0 indicates high likelihood of truthfulness.")

        return round(combined_score, 4), explanation

    def adjust_intent_score(self, intent_score, sentiment, dominant_emotion, dominant_emotion_score, entropy, i, previous_sentiment, previous_emotion, result):
        explanation = []
        if sentiment == 'positive' and dominant_emotion in ['anger', 'disgust', 'fear', 'sadness', 'disapproval', 'realization']:
            intent_score -= 2.5 * dominant_emotion_score
            explanation.append(f"Adjusted down due to inconsistent sentiment ({sentiment}) and emotion ({dominant_emotion}).")
        elif sentiment == 'negative' and dominant_emotion in ['joy', 'surprise', 'admiration', 'amusement', 'approval']:
            intent_score -= 2.5 * dominant_emotion_score
            explanation.append(f"Adjusted down due to inconsistent sentiment ({sentiment}) and emotion ({dominant_emotion}).")
        elif sentiment == 'neutral' and dominant_emotion in ['anger', 'disgust', 'fear', 'sadness', 'disapproval', 'realization']:
            intent_score -= 2 * dominant_emotion_score
            explanation.append(f"Adjusted down due to neutral sentiment with negative emotion ({dominant_emotion}).")
        elif sentiment == 'neutral' and dominant_emotion in ['joy', 'surprise', 'admiration', 'amusement', 'approval']:
            intent_score += 2 * dominant_emotion_score
            explanation.append(f"Adjusted up due to neutral sentiment with positive emotion ({dominant_emotion}).")
        elif sentiment == 'negative' and dominant_emotion in ['anger', 'disgust', 'fear', 'sadness', 'disapproval', 'realization']:
            intent_score += 2.5 * dominant_emotion_score
            explanation.append(f"Adjusted up due to consistent negative sentiment and emotion ({dominant_emotion}).")
        elif sentiment == 'positive' and dominant_emotion in ['joy', 'surprise', 'admiration', 'amusement', 'approval']:
            intent_score += 2.5 * dominant_emotion_score
            explanation.append(f"Adjusted up due to consistent positive sentiment and emotion ({dominant_emotion}).")

        # Adjust based on emotional distribution (entropy)
        if entropy > 1.5:
            intent_score -= 1
            explanation.append("Adjusted down due to high entropy (emotional variability).")
        elif entropy < 0.5:
            intent_score += 1
            explanation.append("Adjusted up due to low entropy (emotional consistency).")

        # Adjust based on narrow gaps between dominant and secondary emotions
        emotion_scores = sorted(result['emotion_scores'].values(), reverse=True)
        if len(emotion_scores) > 1:
            second_highest_score = emotion_scores[1]
            if dominant_emotion_score - second_highest_score < 0.1:
                intent_score -= 1
                explanation.append("Adjusted down due to narrow gap between dominant and secondary emotions.")

        # Adjust based on changes in sentiment between sentences
        if i > 0:
            if sentiment != previous_sentiment or dominant_emotion != previous_emotion:
                intent_score -= 1.0
                explanation.append("Adjusted down due to changes in sentiment/emotion consistency.")
            if sentiment == previous_sentiment and dominant_emotion == previous_emotion:
                intent_score += 0.5
                explanation.append("Adjusted up due to consistent sentiment/emotion across sentences.")

        return intent_score, explanation

    def apply_final_adjustments(self, intent_score, analysis_results):
        sentiment_stats = self.calculate_aggregated_sentiment_stats(analysis_results)
        if sentiment_stats['positive']['average'] > 0.7 and sentiment_stats['negative']['average'] > 0.7:
            intent_score -= 0.5

        aggregated_emotions = self.aggregate_emotion_scores(analysis_results)
        if aggregated_emotions['neutral']['average'] > 0.75:
            if any(aggregated_emotions[emotion]['average'] > 0.05 for emotion in ['anger', 'disgust', 'sadness']):
                intent_score -= 0.75

        for emotion in aggregated_emotions:
            if aggregated_emotions[emotion]['average'] < 0.05 and aggregated_emotions[emotion]['std_dev'] > 0.15:
                intent_score -= 0.5

        return max(min(intent_score, 100), 0)

    def get_dominant_emotion(self, emotion_scores: Dict[str, float]) -> str:
        sorted_emotions = sorted(emotion_scores.items(), key=lambda item: item[1], reverse=True)
        if sorted_emotions[0][0] == 'neutral' and len(sorted_emotions) > 1:
            return sorted_emotions[1][0]
        return sorted_emotions[0][0]

    def calculate_entropy(self, emotion_scores: Dict[str, float]) -> float:
        total_score = sum(emotion_scores.values())
        if total_score == 0:
            return 0.0

        entropy = 0.0
        for score in emotion_scores.values():
            if score > 0:
                probability = score / total_score
                entropy_contribution = probability * math.log2(probability)
                entropy -= entropy_contribution

        return entropy

    def aggregate_emotion_scores(self, analysis_results: List[Dict[str, Dict[str, float]]]) -> Dict[str, Dict[str, float]]:
        emotion_data = defaultdict(list)
        for result in analysis_results:
            for emotion, score in result['emotion_scores'].items():
                emotion_data[emotion].append(score)
        return {emotion: {"min": np.min(scores), "max": np.max(scores), "average": np.mean(scores), "std_dev": np.std(scores)} for emotion, scores in emotion_data.items()}

    def calculate_aggregated_sentiment_stats(self, analysis_results: List[Dict[str, Dict[str, float]]]) -> Dict[str, Dict[str, float]]:
        sentiment_data = defaultdict(list)
        for result in analysis_results:
            sentiment_data[result['sentiment']].append(result['sentiment_score'])
        return {sentiment: {"min": np.min(scores), "max": np.max(scores), "average": np.mean(scores), "std_dev": np.std(scores)} for sentiment, scores in sentiment_data.items()}

    def determine_dominant_sentiment(self, analysis_results: List[Dict[str, Dict[str, float]]]) -> str:
        sentiment_weights = defaultdict(float)
        for result in analysis_results:
            sentiment_weights[result['sentiment']] += result['sentiment_score']
        return max(sentiment_weights, key=sentiment_weights.get)

    def analyze_text_complexity(self, text: str) -> float:
        """
        Analyzes the complexity of the text using readability metrics and average sentence/word length.
        """
        # Flesch-Kincaid readability score (lower values indicate higher complexity)
        fk_score = textstat.flesch_kincaid_grade(text)

        # Average sentence length (higher values indicate higher complexity)
        sentences = self.split_text_into_sentences(text)
        avg_sentence_length = sum(len(sentence.split()) for sentence in sentences) / len(sentences)

        # Average word length (higher values indicate higher complexity)
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Normalize the scores (example: using a 0-1 range)
        fk_score_normalized = np.clip((fk_score - 1) / 12, 0, 1)
        avg_sentence_length_normalized = np.clip(avg_sentence_length / 20, 0, 1)
        avg_word_length_normalized = np.clip(avg_word_length / 10, 0, 1)

        # Weighted average complexity score
        complexity_score = (0.4 * fk_score_normalized +
                            0.3 * avg_sentence_length_normalized +
                            0.3 * avg_word_length_normalized)

        return round(complexity_score, 4)

    def split_text_into_sentences(self, text: str) -> List[str]:
        sentence_endings = re.compile(r'(?<=[.!?])(?=[A-Z]|\s|$)')
        return [sentence.strip() for sentence in sentence_endings.split(text) if sentence.strip()]

    def split_text_into_chunks(self, text: str, max_tokens: int = 500) -> List[str]:
        tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
        tokens = tokenizer.encode(text)
        return [tokenizer.decode(tokens[i:i + max_tokens]) for i in range(0, len(tokens), max_tokens)]

    def download_text_from_url(self, url: str) -> str:
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            return "\n".join([para.get_text() for para in paragraphs])
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while trying to download the text: {e}")
            return ""

# Example usage
if __name__ == "__main__":
    # Use environment variable if no API key is provided explicitly
    detector = FakeNewsDetector()

    url = "https://theonion.com/dozens-of-pregnant-women-caught-in-hanging-snare-nets-above-texas-hospital-entrance/"
    url = "https://www.cnn.com/2024/08/31/politics/harris-slams-trump-arlington-national-cemetery/index.html"
    url = "https://www.cnn.com/2024/08/31/politics/fact-check-trump-ad-harris-immigration/index.html"
    text = detector.download_text_from_url(url)

    if text:
        with suppress_stdout():
            result = detector.analyze_text(text)
        print(json.dumps(result, indent=4))
        print(result['deception_score'])
    else:
        print("Failed to download or process the text.")

