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
    parser = argparse.ArgumentParser(description="Symbiote")

    parser.add_argument('-q', '--query',
                        type=str,
                        default="",
                        help='Query to populate Symbiote with.')

    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Query to populate Symbiote with.')

    parser.add_argument('-c', '--conversation',
                        type=str,
                        help='Conversation file to load.')

    parser.add_argument('-m', '--monitor',
                        action='store_true',
                        help='Execute Symbiote in monitor mode.')

    parser.add_argument('-f', '--filename',
                        type=str,
                        help='Load the given file into Symbiote.')

    args = parser.parse_args()

    if args.monitor:
        monmode = monitor.KeyLogger(debug=args.debug)
        monmode.start()
        while True:
            time.sleep(1)
    else:
        os.system('reset')
        current_path = os.getcwd()
        schat = chat.symchat(working_directory=current_path)
        schat.chat(user_input=args.query,debug=args.debug)

def entry_point() -> None:
    main()

if __name__ == "__main__":
    main()

os.system('reset')
