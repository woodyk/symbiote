#!/usr/bin/env python3
#
# ollama.py

import requests
import json

class Llama3API:
    def __init__(self, base_url):
        self.base_url = base_url
        self.conversation_history = []

    def chat_completion(self, prompt, model="llama3", stream=True):
        endpoint = "/api/chat"
        url = f"{self.base_url}{endpoint}"

        self.conversation_history.append({"role": "user", "content": prompt})

        payload = {
            'model': model,
            'messages': self.conversation_history,
            'stream': True,
            'opetions': {
                'num_ctx': 16000 
                }
        }
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload), stream=True)

        full_response = ""
        for line in response.iter_lines():
            if line:
                json_response = json.loads(line.decode('utf-8'))
                if json_response.get('done', False):
                    break
                part = json_response.get('message', {}).get('content', '')
                print(part, end='', flush=True)
                full_response += part

        self.conversation_history.append({"role": "assistant", "content": full_response})
        print()

        return full_response

    def reset_conversation_history(self):
        self.conversation_history = []

# Example usage:
if __name__ == "__main__":
    api = Llama3API(base_url="http://localhost:11434")

    # Generate chat completions with remembered history
    chat_response_1 = api.chat_completion(
        model="llama3",
        prompt="Why is the sky blue?",
        stream=True
    )
    print("response:", chat_response_1)

    # Reset the conversation history
    api.reset_conversation_history()

