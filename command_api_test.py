#!/usr/bin/env python3
#
# tt.py

import os
import sys
import time
import symbiote.chat as sym 

symbiote = sym.symchat(working_directory=os.getcwd(), debug=False, output=False)

query = "help::"
response = symbiote.process_input(user_input=query)

print(response[0]) # truncated_conversation
print(response[1]) # total_user_tokens + total_assist_tokens
print(response[2]) # total_user_tokens used on request
print(response[3]) # total_assit_tokens used on request
print(response[4]) # char_count
print(response[5]) # remember settings
print(response[6]) # user_input
print(response[7]) # response
