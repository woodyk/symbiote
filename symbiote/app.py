#!/usr/bin/env python3
#

import openai
import sys
import os
import re
import argparse
import time
import select
import subprocess
import platform

# subprocess terminal
import symbiote.chat as chat
import symbiote.core as core
import symbiote.monitor as monitor
import symbiote.speech as speech

openai.api_key = os.getenv("OPENAI_API_KEY")
# Pull a list of available models to use.
# available_models = openai.Model.list()

def main():
    check_libmagic()
    check_nl_packages()

    def is_data():
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

    piped_query = str()
    if is_data():
        for line in sys.stdin:
            piped_query += line

    current_path = os.getcwd()

    parser = argparse.ArgumentParser(description="Symbiote")

    parser.add_argument('-q', '--query',
                        type=str,
                        default="",
                        help='Query to populate Symbiote with.')

    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Turn on debugging')

    parser.add_argument('-r', '--run',
                        action='store_true',
                        help='Execute query and exit.')

    parser.add_argument('-e', '--enable',
                        action='store_true',
                        help='Execute query and and drop to Symbiote prompt.')

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
                        help='Load input into Symbiote.')

    args = parser.parse_args()

    schat = chat.symchat(working_directory=current_path, debug=args.debug)

    if len(piped_query) > 0:
        schat.chat(user_input="hello", suppress=True, run=True)
        os.system('reset')
        print("User data loaded. How can I help you?")
        schat.chat(user_input="", run=args.run)

    if args.load:
        schat.chat(user_input=args.load, suppress=True, run=True)
    elif args.monitor:
        #schat.chat(user_input="role:HELP_ROLE:", run=True)
        monmode = monitor.KeyLogger(schat, debug=args.debug)
        monmode.start()
        while True:
            time.sleep(1)
    elif args.query:
        schat.chat(user_input=args.query, run=args.run, enable=args.enable)
    else:
        os.system('reset')
        schat.chat(user_input="")

def check_libmagic():
    ret_code = 0

    try:
        subprocess.check_output(["file", "--version"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        ret_code = 1

    system = platform.system()

   # Check if libmagic is installed
    if ret_code != 0:
        # libmagic is not installed
        print('libmagic is not installed on this system.')

        # Check the OS and suggest a package manager to install libmagic
        if system == 'Linux':
            # Linux
            if os.path.isfile('/etc/lsb-release'):
                # Ubuntu
                print('Please run `sudo apt-get install libmagic-dev` to install libmagic on Ubuntu.')
            elif os.path.isfile('/etc/redhat-release'):
                # RedHat/CentOS
                print('Please run `sudo yum install libmagic-devel` to install libmagic on RedHat/CentOS.')
            elif os.path.isfile('/etc/os-release'):
                # Other Linux distros
                print('Please use your package manager to install libmagic-devel or libmagic-dev on this system.')

        elif system == 'Darwin':
            # macOS
            print('Please run `brew install libmagic` to install libmagic on macOS using Homebrew.')

        elif system == 'Windows':
            print('Please install libmagic-devel or libmagic-dev using your package manager.')

        else:
            print('Unable to determine OS. Please install libmagic-devel or libmagic-dev using your package manager.')

def check_nl_packages():
    try:
        subprocess.call(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    except:
        print("Error installing spacy en_core_web_sm")

    try:
        subprocess.call(['python', '-m', 'nltk.downloader', 'vader_lexicon'])
    except:
        print("Error installing nltk vader_lexicon")


def entry_point() -> None:
    main()

if __name__ == "__main__":
    main()
