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


openai.api_key = os.getenv("OPENAI_API_KEY")
# Pull a list of available models to use.
# available_models = openai.Model.list()

def main():
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

    parser.add_argument('-i', '--install',
                        action='store_true',
                        help='Install required packages.')

    args = parser.parse_args()

    if args.install:
        os.chdir('/tmp')
        check_libmagic()
        check_nl_packages()
        check_libpostal()
        return

    # subprocess terminal
    import symbiote.chat as chat
    import symbiote.core as core
    import symbiote.monitor as monitor
    import symbiote.speech as speech

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

def check_libpostal():
    install = False
    try:
        import postal
    except:
        install = True

    system = platform.system()

    if system not in ['Linux', 'Darwin']:
        print("This function only supports MacOS and Linux")
        return

    if install:
        # Install prerequisites
        if system == 'Linux':
            subprocess.run(["sudo", "apt-get", "install", "curl", "autoconf", "automake", "libtool", "pkg-config"])
        elif system == 'Darwin':
            subprocess.run(["brew", "install", "curl", "autoconf", "automake", "libtool", "pkg-config"])

        # Clone libpostal repository
        subprocess.run(["git", "clone", "https://github.com/openvenues/libpostal"])

        # Install libpostal
        os.chdir("libpostal")
        home = os.path.expanduser("~")
        subprocess.run(["./bootstrap.sh"])
        subprocess.run(["./configure", f'--prefix="{home}/.local/share"', f'--datadir="{home}/.cache/libpostal"'])
        subprocess.run(["make", "-j4"])
        subprocess.run(["make", "install"])

        print("############################################")
        print("Run the following before executing symbiote.")
        print('echo \'export LD_LIBRARY_PATH="$HOME/.local/share/include:$LD_LIBRARY_PATH"\' >> ~/.bashrc')
        print('echo \'export CPATH="$HOME/.local/share/include:$CPATH"\' >> ~/.bashrc')
        print('echo \'export LDFLAGS="-L$HOME/.local/share/lib"\' >> ~/.bashrc')
        print('source ~/.bashrc')

        response = input("Hit any key to continue.")

        subprocess.run(["pip3", "install", "postal"])

        # Run ldconfig on Linux
        if system == 'Linux':
            subprocess.run(["sudo", "ldconfig"])

        print("libpostal installation completed")

def entry_point() -> None:
    main()

if __name__ == "__main__":
    main()
