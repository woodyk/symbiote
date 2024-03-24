#!/usr/bin/env python3
import time
import sys
import json
import tiktoken
import re
import os
import requests
import uuid
from pygments.formatters import Terminal256Formatter
from transformers import GPT2Tokenizer, GPT2LMHeadModel, AdamW, get_linear_schedule_with_warmup


import symbiote.codeextract as codeextract
import symbiote.utils as utils

class symbiotes:
    def __init__(self, settings):
        # Available models
        self.models = {
            "someone": 1000000, 
            "dummy": 1024,
            "symbiote": 128000,
            "GSEGNN": 128000,
            "mistral-small-latest": 128000,
          }

        self.settings = settings
        self.remember = self.models[self.settings['model']]

        self.ce = codeextract.CodeBlockIdentifier()

        self.output = True
        
    def update_symbiote_settings(self, settings, *args, **kwargs):
        self.settings = settings 
        self.remember = self.models[self.settings['model']]

        if self.settings['debug']:
            print(self.settings)

        return

    def get_models(self):
        model_list = []
        for model in self.models:
            model_list.append(model)

        return model_list

    def process_mistral(self, message):
        request_body = {
            "model": "mistral-small-latest",
            "messages": [{"role": "user", "content": message}],
            "temperature": 0.7,
            "max_tokens": 100,
        }

        api_key = os.getenv("MISTRAL_AI_API_KEY")
        api_url = "https://api.mistral.ai/v1/chat/completions"

        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }


        try:
            response = requests.post(api_url, headers=headers, data=json.dumps(request_body))
        except Exception as e:
            print(e)
            return

        print(response["choices"][0]["message"]["content"].strip())

        return response_data["choices"][0]["message"]["content"].strip() 

    def process_someone(self, message, timeout=120):
        # Define the url of the API
        url = "http://192.168.1.40:5000/predict"

        print("---")
        # Define the data to be sent to the API
        data = {
            "input_text": message,
            "max_length": self.settings['max_tokens'],
            "temperature": self.settings['temperature'],
            "num_return_sequences": 1 
        }

        # Send a POST request to the API and get the response
        try:
            response = requests.post(url, json=data, timeout=timeout)
        except requests.exceptions.Timeout:
            pass
            return None
        except Exception as e:
            print(f'Request failed: {e}')
            return None

        if timeout < 1:
            return None

        if self.settings['debug']:
            for item in dir(response):
                value = getattr(response, item)
                print(item, value)

        # If the request was successful, return the generated text
        if response.status_code == 200:
            print("---")
            print(response.text)
            return response.text
        else:
            print(f"Request failed with status code {response.status_code}")
            print("---")
            return

    def split_user_input_into_chunks(self, user_input):
        chunks = []
        if self.settings['model'] == 'dummy':
            chunks.append(user_input)
            return chunks

        #encoding = tiktoken.encoding_for_model(self.settings['model'])
        #tokens = encoding.encode(user_input)
        #token_count = len(tokens)
        token_count, tokens, encoding  = self.tokenize(user_input)

        current_chunk = []
        current_token_count = 0

        for i, token in enumerate(tokens):
            current_chunk.append(token)
            current_token_count += 1

            if current_token_count >= self.settings['chunk_size'] or i == len(tokens) - 1:
                chunk_string = encoding.decode(current_chunk)
                chunks.append(chunk_string)
                current_chunk = []
                current_token_count = 0

        return chunks

    def append_prompt(self, *args, **kwargs):
        if "role" not in kwargs:
            kwargs['role'] = "user"

        conversation = kwargs['conversation']

        content = {
                "epoch": time.time(),
                "role": kwargs['role'],
                "content": kwargs['prompt'] 
                }

        conversation.append(content)

        return conversation

    def send_request(self, user_input, conversation, completion=False, suppress=False, role="user", flush=False, logging=True, timeout=30, output=True):
        self.conversation = conversation
        self.suppress = suppress
        total_trunc_tokens = 0
        total_user_tokens = 0
        total_assist_tokens = 0
        char_count = 0
        completion_content = []
        self.output = output

        original_user_input = user_input

        # Check if we are processing a string or other data type.
        if not isinstance(user_input, str):
            user_input = json.dumps(user_input)
            user_input = '\n```\n{}\n```\n'.format(user_input)

        user_input = re.sub('[ ]+', ' ', user_input)

        # Split user input into chunks
        query_tokens, _, _ = self.tokenize(user_input)
        user_input_chunks = self.split_user_input_into_chunks(user_input)

        for index, user_input_chunk in enumerate(user_input_chunks):
            # Update our conversation with the user input
            user_content = {
                "epoch": time.time(),
                "role": role,
                "content": user_input_chunk
            }

            self.conversation.append(user_content)
            completion_content.append(user_content)
            if logging:
                self.save_conversation(user_content, self.conversations_file)

        # Update our conversation with the user input
        user_content = {
            "epoch": time.time(),
            "role": role,
            "content": user_input
        }

        self.conversation.append(user_content)
        completion_content.append(user_content)
        if logging:
            self.save_conversation(user_content, self.conversations_file)

        # Handle suppressed messaging
        if self.suppress:
            if self.settings['debug']:
                print("suppression set returning")
            return self.conversation, 0, 0, 0, char_count, self.remember, original_user_input, None

        if completion:
            truncated_conversation, total_user_tokens, char_count = self.truncate_messages(completion_content, flush=flush)
        else:
            truncated_conversation, total_user_tokens, char_count = self.truncate_messages(self.conversation, flush=flush)

        # Push queries to model
        if self.settings['model'] == 'symbiote':
            response = self.interactWithModel(truncated_conversation)
        elif self.settings['model'].startswith("mistral"):
            response = self.process_mistral(truncated_conversation)
        elif self.settings['model'] == 'someone':
            try:
                response = self.process_someone(turncated_conversation, timeout=timeout)
            except Exception as e:
                return self.conversation, 0, 0, 0, char_count, self.remember, original_user_input, None
        elif self.settings['model'] == 'dummy':
            response = ""
        else:
            print("No AI model defined.\n");
            return self.conversation, 0, 0, 0, char_count, self.remember, original_user_input, None

        total_assist_tokens, _, _ = self.tokenize(response)
        total_assist_tokens = 0

        # update our conversation with the assistant response
        assistant_content = {
            "epoch": time.time(),
            "role": "assistant",
            "content": response
        }

        #conversation.append(assistant_content)
        truncated_conversation.append(assistant_content)
        if logging:
            self.save_conversation(assistant_content, self.conversations_file)
        #conversation = self.load_conversation(self.conversations_file)

        return truncated_conversation, (total_user_tokens + total_assist_tokens), total_user_tokens, total_assist_tokens, char_count, self.remember, original_user_input, response

    def load_conversation(self, conversations_file, flush=False):
        ''' Load conversation json file '''
        self.conversations_file = conversations_file
        data = []

        if os.path.exists(self.conversations_file):
            try:
                with open(conversations_file, 'r') as file:
                    for line in file:
                        data.append(json.loads(line))

            except Exception as e:
                pass
                print("Error: opening %s: %s" % (conversations_file, e))
                sys.exit(10)

        return data

    def save_conversation(self, conversation_data, conversations_file):
        ''' Save conversation output to loaded conversation file '''
        json_conv = {
                "conversation": self.settings['conversation'],
                "epoch": conversation_data['epoch'],
                "role": conversation_data['role'],
                "content": conversation_data['content']
                }

        jsonl_string = json.dumps(json_conv)

        with open(conversations_file, 'a+') as file:
            #json.dump(data, file, indent=2)
            file.write(jsonl_string + "\n")

    def tokenize(self, text):
        ''' Tokenize text '''
        if not isinstance(text, str):
            text = json.dumps(text)

        if self.settings['model'] == 'dummy':
            return 1000, 0, 0 
        elif self.settings['model'] == 'someone':
            return 1024, 0, 0
        else:
            tokenizer = tiktoken.encoding_for_model('gpt-4')
            encoded_tokens = tokenizer.encode(text, disallowed_special=())

        tokens = len(encoded_tokens)

        return tokens, encoded_tokens, tokenizer 

    def truncate_messages(self, conversation, flush=False):
        ''' Truncate data to stay within token thresholds '''
        max_length = int(self.remember * self.settings['conversation_percent'] - self.settings['max_tokens'])
        total_tokens = 0
        truncated_tokens = 0
        char_count = 0
        truncated_conversation = []
        single_message = True
        
        total_tokens, encoded_tokens, _ = self.tokenize(conversation)

        while truncated_tokens < max_length and len(conversation) > 0:
            last_message = conversation.pop()
            if 'epoch' in last_message:
                del last_message['epoch']
            if 'conversation' in last_message:
                del last_message['conversation']


            truncated_conversation.insert(0, last_message)
            t_tokens, _, _ = self.tokenize(last_message['content'])

            if last_message['content'] is None:
                char_count = 0
            else:
                char_count += len(last_message['content'])
            truncated_tokens += t_tokens
            single_message = False

        while truncated_tokens > max_length and len(truncated_conversation) > 0:
            removed_message = truncated_conversation.pop(0)
            t_tokens, _, _ = self.tokenize(removed_message['content'])
            char_count += len(last_message['content'])
            truncated_tokens -= t_tokens

        if total_tokens < self.settings['max_tokens'] and single_message:
            message = conversation.pop()
            if 'epoch' in message:
                del message['epoch']
            if 'conversation' in message:
                del message['conversation']

            truncated_conversation.insert(0, message)
            truncated_tokens, _, _ = self.tokenize(message['content'])
            char_count = len(message['content'])

        return truncated_conversation, truncated_tokens, char_count

    def list_conversations(self, conversations_dir):
        files = os.listdir(conversations_dir)

        if not files:
            print("No conversations availaable.")

        file_list = []
        for file in files:
            if re.search(r'\S+.jsonl$', file):
                file_list.append(file)

        return file_list

    def handle_control_c(self, signum, frame):
        print("\nControl-C detected.")
        sys.exit(0)

    def handle_control_x(self):
        print("\nControl-X detected. Sending 'stop::' command.")
        conversation = []
        return

    def change_max_tokens(self, max_tokens, update=False):
        if isinstance(max_tokens, int):
            self.settings['max_tokens'] = max_tokens 
        
            if update:
                self.settings['default_max_tokens'] = max_tokens 
        else:
            print("Tokens must be of type int.")

        return

    def interactWithModel(self, prompt):
        # Load the trained model and tokenizer
        model_dir = self.settings['symbiote_path'] + "/learning/gpt2_finetuned"
        model = GPT2LMHeadModel.from_pretrained(model_dir)
        tokenizer = GPT2Tokenizer.from_pretrained(model_dir)

        # Tokenize the prompt
        inputs = tokenizer.encode(prompt, return_tensors='pt')

        # Generate a response
        outputs = model.generate(inputs, max_length=150, num_return_sequences=1, no_repeat_ngram_size=2, temperature=0.7)

        # Decode the response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        return response 

    def export_conversation(self, input_file: str, history=False, lines=False):
        """
        Extracts data from a .jsonl file and saves it to a .txt file.

        Args:
        input_file (str): Path to the .jsonl file.
        """

        # Make sure the conversation exists in the conversations directory.
        if not os.path.exists(input_file):
            conversation_path = os.path.expanduser(self.settings['symbiote_path']) + "/conversations"
            check_file = os.path.join(conversation_path, input_file)
            if os.path.exists(check_file):
                input_file = check_file
            else:
                print(f"Failed to find conversation {input_file}")
                return None

        # Strip the .jsonl extension and append .txt
        output_filename = os.path.splitext(input_file)[0] + ".txt"

        with open(input_file, 'r') as infile:
            lines_to_read = infile.readlines()[-lines:] if lines else infile.readlines()

        full_history = str()
        with open(output_filename, 'w') as outfile:
            for line in lines_to_read:
                # Parse each line as a JSON object
                data = json.loads(line)

                # Extract the desired fields
                conversation = data.get("conversation", "N/A")
                epoch = data.get("epoch", "N/A")
                role = data.get("role", "N/A")
                content = data.get("content", "N/A")

                # Decode possible escape sequences in content
                try:
                    content = bytes(content, "utf-8").decode("unicode_escape")
                except Exception as e:
                    pass

                # Format the data
                formatted_data = f"Conversation: {conversation}\n"
                formatted_data += f"Epoch: {epoch}\n"
                formatted_data += f"Role: {role}\n"
                formatted_data += f"Content:\n{content}\n"
                formatted_data += '-'*50 + '\n' # separator

                full_history += formatted_data
                if history:
                    print(formatted_data)
                else:
                    # Write the formatted data to the output file
                    outfile.write(formatted_data)
                    print(f"Data saved to {output_filename}")

        return full_history
