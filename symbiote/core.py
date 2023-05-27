#!/usr/bin/env python3
import sys
import json
import openai
import tiktoken
import re
import os

class symbiotes:
    def __init__(self, settings):
        # Available models
        self.models = {
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-3.5-turbo": 4096,
            "text-davinci-002": 4097,
            "text-davinci-003": 4097
          }

        self.settings = settings
        self.remember = self.models[self.settings['model']]

    def update_symbiote_settings(self, settings, *args, **kwargs):
        self.settings = settings 
        self.remember = self.models[self.settings['model']]

        return

    def get_models(self):
        model_list = []
        for model in self.models:
            model_list.append(model)

        return model_list

    def process_request(self, messages):
        ''' Send user_input to openai for processing '''
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
                "role": kwargs['role'],
                "content": kwargs['prompt'] 
                }

        conversation.append(content)

        return conversation

    def send_request(self, user_input, conversation, suppress=False, role="user"):
        self.suppress = suppress
        total_trunc_tokens = 0
        total_user_tokens = 0
        total_assist_tokens = 0

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
                "role": role,
                "content": user_input_chunk
            }

            conversation.append(user_content)
            self.save_conversation(user_content, self.conversations_file)

        # Handle suppressed messaging
        if suppress:
            return conversation, 0, 0, 0

        # Manage openai token balance
        truncated_conversation, total_user_tokens = self.truncate_messages(conversation)

        # Push queries to openai
        response = self.process_request(truncated_conversation)
        
        total_assist_tokens, _ = self.tokenize(response)

        # update our conversation with the assistant response
        assistant_content = {
            "role": "assistant",
            "content": response
        }

        conversation.append(assistant_content)
        self.save_conversation(assistant_content, self.conversations_file)

        return conversation, (total_user_tokens + total_assist_tokens), total_user_tokens, total_assist_tokens

    def load_conversation(self, conversations_file):
        ''' Load openai conversation json file '''
        self.conversations_file = conversations_file
        data = []

        try:
            with open(conversations_file, 'r') as file:
                data = json.load(file)
        except Exception as e:
            pass
            print("Error: opening %s: %s" % (conversations_file, e))
            sys.exit(10)

        return data

    def save_conversation(self, conversation_data, conversations_file):
        ''' Save conversation output to loaded conversation file '''
        self.conversations_file = conversations_file

        if os.path.exists(conversations_file):
            data = self.load_conversation(conversations_file)
            data.append(conversation_data)
        else:
            data = []

        with open(conversations_file, 'w') as file:
            json.dump(data, file, indent=2)

        return data

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
        #max_length = int(self.remember - self.settings['max_tokens'] * self.settings['conversation_percent'])
        max_length = int(self.remember * self.settings['conversation_percent'] - self.settings['max_tokens'])
        total_tokens = 0
        truncated_tokens = 0
        
        total_tokens, encoded_tokens = self.tokenize(conversation)

        if total_tokens <= max_length:
            return conversation, total_tokens
        
        truncated_conversation = []
        while truncated_tokens < max_length and len(conversation) > 1:
            last_message = conversation.pop()
            truncated_conversation.insert(0, last_message)
            t_tokens, _ = self.tokenize(last_message['content'])
            truncated_tokens += t_tokens

        while truncated_tokens > max_length:
            removed_message = truncated_conversation.pop(0)
            t_tokens, _ = self.tokenize(removed_message['content'])
            truncated_tokens -= t_tokens

        return truncated_conversation, truncated_tokens

    def list_conversations(self, conversations_dir):
        files = os.listdir(conversations_dir)

        if not files:
            print("No conversations availaable.")

        file_list = []
        for file in files:
            if re.search(r'\S+.json$', file):
                file_list.append(file)

        return file_list

    def handle_ctrl_c(self, signum, frame):
        print("\nControl-C detected. Sending 'stop::' command.")
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

