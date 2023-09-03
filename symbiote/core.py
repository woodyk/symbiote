#!/usr/bin/env python3

import time
import sys
import json
import openai
import tiktoken
import re
import os
import requests

class symbiotes:
    def __init__(self, settings):
        # Available models
        self.models = {
            "gpt-4": 8192,
            "gpt-3.5-turbo-16k": 16000,
            "gpt-4-32k": 32768,
            "gpt-3.5-turbo": 4096,
            "gpt-4-0613": 8192,
            "gpt-4-0314": 8192,
            "text-davinci-002": 4097,
            "text-davinci-003": 4097,
            "someone": 16384
          }

        self.settings = settings
        self.remember = self.models[self.settings['model']]

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

    def process_someone(self, message):
        # Define the url of the API
        url = "http://ai.sr:5000/predict"

        # Define the data to be sent to the API
        data = {
            "input_text": message,
            "max_length": self.settings['max_tokens'],
            "temperature": self.settings['temperature'],
            "num_return_sequences": self.settings['top_p'] 
        }

        # Send a POST request to the API and get the response
        response = requests.post(url, json=data)

        # If the request was successful, return the generated text
        if response.status_code == 200:
            return response.text
        else:
            return f"Request failed with status code {response.status_code}"

    def process_requestJ2(self, message):
        url = "https://api.ai21.com/studio/v1/j2-mid/complete"
        payload = {
            "numResults": 1,
            "maxTokens": self.settings['max_tokens'],
            "minTokens": 10,
            "temperature": self.settings['temperature'],
            "topP": self.settings['top_p'],
            "topKReturn": 0,
            "stopSequences": [self.settings['stop']],
            "frequencyPenalty": {
                "scale": self.settings['frequency_penalty'],
                "applyToWhitespaces": True,
                "applyToPunctuations": True,
                "applyToNumbers": True,
                "applyToStopwords": True,
                "applyToEmojis": True
            },
            "presencePenalty": {
                "scale": self.settings['presence_penalty'],
                "applyToWhitespaces": True,
                "applyToPunctuations": True,
                "applyToNumbers": True,
                "applyToStopwords": True,
                "applyToEmojis": True
            },
            "countPenalty": {
                "scale": 1,
                "applyToWhitespaces": True,
                "applyToPunctuations": True,
                "applyToNumbers": True,
                "applyToStopwords": True,
                "applyToEmojis": True
            }
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": "Bearer YOUR_API_KEY"
        }

        if self.settings['debug']:
            print(json.dumps(messages, indent=4))

        if not self.suppress:
            print("---")

        message = " "
        chunk_block = ""
        response = {} 

        response = requests.post(url, json=payload, headers=headers)
        message = response.choices[0].message.content

        if not self.suppress:
            print(message)
            print("---\n")

        return message.strip()

    def process_requestOpenAI(self, messages):
        ''' Send user_input to openai for processing '''
        if self.settings['debug']:
            print(json.dumps(messages, indent=4))

        if not self.suppress:
            print("---")

        message = " "
        chunk_block = ""
        response = {} 

        # Proper use of openai.ChatCompletion.create() function.
        try:
            # Process user_input
            response = openai.ChatCompletion.create(
                model = self.settings['model'],
                messages = messages,
                max_tokens = self.settings['max_tokens'],
                temperature = self.settings['temperature'],
                top_p = self.settings['top_p'],
                stream = self.settings['stream'],
                presence_penalty = self.settings['presence_penalty'],
                frequency_penalty = self.settings['frequency_penalty'],
                stop = self.settings['stop'] 
            )

        except openai.error.OpenAIError as e:
            # Handle openai error responses
            if e is not None:
                print()
                print(e.http_status)
                print(e.error)
                print()
            else:
                message = "Unknown Error"

        # Handle real time stream output from openai response
        chunk_size = 8 
        if self.settings['stream']:
            for chunk in response:
                try:
                    chunk_block += chunk.choices[0].delta.content
                    if len(chunk_block) >= chunk_size:
                        if not self.suppress:
                            print(chunk_block, end="")
                        chunk_block = ""
                except:
                    continue

                message += chunk.choices[0].delta.content

            if not self.suppress:
                print(chunk_block)
        else:
            message = response.choices[0].message.content
            if not self.suppress:
                print(message)

        if not self.suppress:
            print("---\n")

        if self.settings['max_tokens'] < self.settings['default_max_tokens']:
            message = "Data consumed."
       
        return message.strip()

    def split_user_input_into_chunks(self, user_input):
        encoding = tiktoken.encoding_for_model(self.settings['model'])
        #tokens = encoding.encode(user_input)
        #token_count = len(tokens)
        token_count, tokens = self.tokenize(user_input)

        chunks = []
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

    def send_request(self, user_input, conversation, completion=False, suppress=False, role="user"):
        self.suppress = suppress
        total_trunc_tokens = 0
        total_user_tokens = 0
        total_assist_tokens = 0
        char_count = 0
        completion_content = []

        # Check if we are processing a string or other data type.
        if not isinstance(user_input, str):
            user_input = json.dumps(user_input)
            user_input = '\n```\n{}\n```\n'.format(user_input)

        user_input = re.sub('[ ]+', ' ', user_input)

        # Split user input into chunks
        query_tokens, _ = self.tokenize(user_input)
        user_input_chunks = self.split_user_input_into_chunks(user_input)

        for index, user_input_chunk in enumerate(user_input_chunks):
            # Update our conversation with the user input
            user_content = {
                "epoch": time.time(),
                "role": role,
                "content": user_input_chunk
            }

            conversation.append(user_content)
            completion_content.append(user_content)
            self.save_conversation(user_content, self.conversations_file)

        # Handle suppressed messaging
        if suppress:
            return conversation, 0, 0, 0, char_count, self.remember

        if completion:
            truncated_conversation, total_user_tokens, char_count = self.truncate_messages(completion_content)
        else:
            truncated_conversation, total_user_tokens, char_count = self.truncate_messages(conversation)

        # Push queries to model
        if self.settings['model'] == 'symbiote':
            response = self.interactWithModel(truncated_conversation)
        elif self.settings['model'] == 'someone':
            response = self.process_someone(truncated_conversation)
        else:
            response = self.process_requestOpenAI(truncated_conversation)

        total_assist_tokens, _ = self.tokenize(response)

        # update our conversation with the assistant response
        assistant_content = {
            "epoch": time.time(),
            "role": "assistant",
            "content": response
        }

        conversation.append(assistant_content)
        self.save_conversation(assistant_content, self.conversations_file)
        conversation = self.load_conversation(self.conversations_file)

        return conversation, (total_user_tokens + total_assist_tokens), total_user_tokens, total_assist_tokens, char_count, self.remember

    def load_conversation(self, conversations_file):
        ''' Load openai conversation json file '''
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

        with open(conversations_file, 'a') as file:
            #json.dump(data, file, indent=2)
            file.write(jsonl_string + "\n")

    def tokenize(self, text):
        ''' Tokenize text '''
        if not isinstance(text, str):
            text = json.dumps(text)

        encoding = tiktoken.encoding_for_model(self.settings['model'])
        encoding.encode(text)
        encoded_tokens = encoding.encode(text)
        tokens = len(encoded_tokens)
        return tokens, encoded_tokens 

    def truncate_messages(self, conversation):
        ''' Truncate data to stay within token thresholds for openai '''
        max_length = int(self.remember * self.settings['conversation_percent'] - self.settings['max_tokens'])
        total_tokens = 0
        truncated_tokens = 0
        char_count = 0
        truncated_conversation = []
        
        total_tokens, encoded_tokens = self.tokenize(conversation)

        while truncated_tokens < max_length and len(conversation) > 0:
            last_message = conversation.pop()
            if 'epoch' in last_message:
                del last_message['epoch']
            if 'conversation' in last_message:
                del last_message['conversation']

            truncated_conversation.insert(0, last_message)
            t_tokens, _ = self.tokenize(last_message['content'])
            char_count += len(last_message['content'])
            truncated_tokens += t_tokens

        while truncated_tokens > max_length:
            removed_message = truncated_conversation.pop(0)
            t_tokens, _ = self.tokenize(removed_message['content'])
            char_count += len(last_message['content'])
            truncated_tokens -= t_tokens

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
        self.send_request("stop::", conversation)

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
        model_dir = self.settings['symbiote_path'] + "learning/index_model"
        model = GPT2LMHeadModel.from_pretrained(model_dir)
        tokenizer = GPT2Tokenizer.from_pretrained(model_dir)

        # Tokenize the prompt
        inputs = tokenizer.encode(prompt, return_tensors='pt')

        # Generate a response
        outputs = model.generate(inputs, max_length=150, num_return_sequences=1, no_repeat_ngram_size=2, temperature=0.7)

        # Decode the response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        return response 

    def export_conversation(self, input_file: str):
        """
        Extracts data from a .jsonl file and saves it to a .txt file.

        Args:
            input_file (str): Path to the .jsonl file.
        """
        # Strip the .jsonl extension and append .txt
        output_filename = os.path.splitext(input_file)[0] + ".txt"
        print(input_file, output_filename)

        with open(input_file, 'r') as infile, open(output_filename, 'w') as outfile:
            for line in infile:
                # Parse each line as a JSON object
                data = json.loads(line)

                # Extract the desired fields
                conversation = data.get("conversation", "N/A")
                epoch = data.get("epoch", "N/A")
                role = data.get("role", "N/A")
                content = data.get("content", "N/A")

                # Decode possible escape sequences in content
                content = bytes(content, "utf-8").decode("unicode_escape")

                # Format the data
                formatted_data = f"Conversation: {conversation}\n"
                formatted_data += f"Epoch: {epoch}\n"
                formatted_data += f"Role: {role}\n"
                formatted_data += f"Content:\n{content}\n"
                formatted_data += '-'*50 + '\n'  # separator

                # Write the formatted data to the output file
                outfile.write(formatted_data)

        print(f"Data saved to {output_filename}")
