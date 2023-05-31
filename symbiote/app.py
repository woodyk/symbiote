#!/usr/bin/env python3
#

import openai
import sys
import os
import re
import argparse
import time

# subprocess terminal
import symbiote.chat as chat
import symbiote.monitor as monitor

openai.api_key = os.getenv("OPENAI_API_KEY")
# Pull a list of available models to use.
# available_models = openai.Model.list()

def main():
    os.system('reset')
    current_path = os.getcwd()

    parser = argparse.ArgumentParser(description="Symbiote")

    parser.add_argument('-q', '--query',
                        type=str,
                        default="",
                        help='Query to populate Symbiote with.')

    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Query to populate Symbiote with.')

    parser.add_argument('-r', '--run',
                        action='store_true',
                        help='Execute query and exit.')

    parser.add_argument('-c', '--conversation',
                        type=str,
                        help='Conversation file to load.')

    parser.add_argument('-m', '--monitor',
                        action='store_true',
                        help='Execute Symbiote in monitor mode.')

    parser.add_argument('-f', '--filename',
                        type=str,
                        help='Load the given file into Symbiote.')

    parser.add_argument('-l', '--load',
                        type=str,
                        help='Load the given file into Symbiote.')

    args = parser.parse_args()

    schat = chat.symchat(working_directory=current_path, debug=args.debug)

    if args.monitor:
        #schat.chat(user_input="role:HELP_ROLE:", run=True)
        monmode = monitor.KeyLogger(schat, debug=args.debug)
        monmode.start()
        while True:
            time.sleep(1)
    else:
        schat.chat(user_input=args.query, run=args.run)

def entry_point() -> None:
    main()

if __name__ == "__main__":
    main()

os.system('reset')
