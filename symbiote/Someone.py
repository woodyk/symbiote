#!/usr/bin/env python3
#
# symbiote/Someone.py

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class TextGenerator:
    def __init__(self):
        self.model_name = "gpt2"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.pad_token_id = self.tokenizer.pad_token_id

    def generate_text(self, prompt):
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
        attention_mask = (input_ids != self.tokenizer.pad_token_id).long()

        output = self.model.generate(
            input_ids,
            max_length=1024,
            do_sample=True,
            attention_mask=attention_mask,
            pad_token_id=self.pad_token_id,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            temperature=.5,
            repetition_penalty=3.0,
            top_p=1
        )

        generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        return generated_text
'''
if __name__ == "__main__":
    generator = TextGenerator()
    while True:
        prompt = input("> ")
        prompt = prompt.strip()
        print(generator.generate_text(prompt))
'''
