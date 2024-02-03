#!/usr/bin/env python3
#
# chat.py
import os
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from transformers import GPT2Tokenizer, GPT2Model

def chat():
    # Load the fine-tuned model and tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2', cache_dir='/Users/kato/.symbiote/learning')
    model = GPT2LMHeadModel.from_pretrained('gpt2')

    # Start the chat loop
    while True:
        # Get the user's input
        user_input = input("User: ")

        # Quit the chat if the user types 'quit'
        if user_input.lower() == 'quit':
            break

        # Encode the user's input and add the end-of-string token
        input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors='pt')
        attention_mask = (input_ids != tokenizer.pad_token_id)

        # Generate a response
        output = model.generate(input_ids,
                                attention_mask=attention_mask,
                                max_length=1024,
                                pad_token_id=tokenizer.eos_token_id,
                                temperature=.5,
                                num_return_sequences=1,
                                no_repeat_ngram_size=2,
                                repetition_penalty=3.0,
                                top_p=1
                            )

        # Decode the response
        response = tokenizer.decode(output[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
        print("Bot: " + response)

if __name__ == '__main__':
    chat()
