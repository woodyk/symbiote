#!/usr/bin/env python3
#
# huggingface.py

from transformers import (
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    AutoConfig
)
from transformers import AutoModel, AutoTokenizer
from datasets import load_dataset, list_datasets

class HuggingFaceManager:
    def __init__(self):
        self.available_datasets = list_datasets()

    def download_model(self, model_name):
        """
        Downloads the specified model and tokenizer from Hugging Face.
        """
        try:
            model = AutoModel.from_pretrained(model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            print(f"Downloaded model and tokenizer for {model_name}.")
            return model, tokenizer
        except Exception as e:
            print(f"An error occurred: {e}")

    def download_dataset(self, dataset_name, **kwargs):
        """
        Downloads the specified dataset from Hugging Face.
        """
        if dataset_name in self.available_datasets:
            try:
                dataset = load_dataset(dataset_name, **kwargs)
                print(f"Downloaded dataset: {dataset_name}.")
                return dataset
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print(f"Dataset {dataset_name} not found in available datasets.")

    def list_available_datasets(self):
        """
        Lists all available datasets in Hugging Face.
        """
        return self.available_datasets

    def create_model(self, model_name, num_labels, task='sequence_classification'):
        """
        Initializes a new model for a specific task.
        """
        config = AutoConfig.from_pretrained(model_name, num_labels=num_labels)
        if task == 'sequence_classification':
            model = AutoModelForSequenceClassification.from_config(config)
        else:
            raise ValueError("Task not supported")
        return model

    def train_model(self, model, tokenizer, train_dataset, eval_dataset, output_dir='./results', epochs=3):
        """
        Fine-tunes and trains the model with the given datasets.
        """
        # Tokenization of datasets
        def tokenize_function(examples):
            return tokenizer(examples['text'], padding='max_length', truncation=True)

        tokenized_train = train_dataset.map(tokenize_function, batched=True)
        tokenized_eval = eval_dataset.map(tokenize_function, batched=True)

        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir='./logs',
        )

        # Initialize Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_train,
            eval_dataset=tokenized_eval,
        )

        # Train the model
        trainer.train()

        return model

# Assuming the dataset has 'train' and 'validation' splits
train_dataset = dataset['train']
eval_dataset = dataset['validation']
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

# Train the model
trained_model = manager.train_model(model, tokenizer, train_dataset, eval_dataset)

# Example usage
manager = HuggingFaceManager()
model, tokenizer = manager.download_model("bert-base-uncased")
dataset = manager.download_dataset("glue", name="mrpc")

