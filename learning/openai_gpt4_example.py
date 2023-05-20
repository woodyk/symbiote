#!/usr/bin/env python3
#
# openai_gpt4_example.py

import openai

''' Configurable variables for use with gpt-4. '''
model = "gpt-4"
max_tokens = 1024
temperature = 0.6
top_p = 1
stream = True

''' Configure output autoflush for real time chat output '''
sys.stdout = io.TextIOWrapper(
    open(sys.stdout.fileno(), 'wb', 0),
    write_through=True
)

''' Proper function for interacting with gpt-4 '''
def process_request(messages):
    try:
        ''' Proper Openai gpt-4 api call '''
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=stream
        )
    except openai.error.OpenAIError as e:
        ''' Proper error handling in the event of failure with the api '''
        print(e.http_status)
        print(e.error)
        sys.exit(1)

    ''' Stream handler for real time output from openai gpt-4 '''
    if stream:
        for chunk in response:
            try:
                chunk.choices[0].delta.content
            except:
                continue

            print(chunk.choices[0].delta.content, end="")
            message += chunk.choices[0].delta.content

    else:
        message = response.choices[0].text

    return message.strip()

''' Main function for interacting with process_request() directly '''
def main():
    user_input = input("User: ").strip()

    response = process_request(user_input)

''' Call main upon execution '''
if __name__ == "__main__":
    main()
