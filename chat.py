#!/usr/bin/env python3
#
# chat.py
import os
from transformers import GPT2LMHeadModel, GPT2Tokenizer

def chat():
    # Load the fine-tuned model and tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained('~/.symbiote/learning/gpt2_finetuned')
    model = GPT2LMHeadModel.from_pretrained('~/.symbiote/learning/gpt2_finetuned')

    # Start the chat loop
    while True:
        # Get the user's input
        user_input = input("User: ")

        # Quit the chat if the user types 'quit'
        if user_input.lower() == 'quit':
            break

        # Encode the user's input and add the end-of-string token
        input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors='pt')

        # Generate a response
        output = model.generate(input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id)

        # Decode the response
        response = tokenizer.decode(output[:, input_ids.shape[-1]:][0], skip_special_tokens=True)

        print("Bot: " + response)

if __name__ == '__main__':
    chat()

