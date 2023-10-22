#!/usr/bin/env python3
#
# tt.py

import os
import sys
import symbiote.chat as chat

symbiote = chat.symchat(working_directory=os.getcwd(), debug=False, output=False)
query = "setting::"
response = symbiote.process_input(user_input=query)
for i in response:
    print(i)

query = "convo:null:"
response = symbiote.process_input(user_input=query)
for i in response:
    print(i)

query = 'tokens::'
response = symbiote.process_input(user_input=query)
for i in response:
    print(i)

