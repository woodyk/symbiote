#!/usr/bin/env python3
#
# chat.py

import time
import sys
import os
import io
import re
import signal
import requests
import threading
import textract
import magic
import subprocess
import platform
import json

from bs4 import BeautifulSoup

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import PathValidator

from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

import symbiote.core as core
import symbiote.shell as shell
import symbiote.roles as roles
import symbiote.utils as utils

command_list = {
        "help::": "This help output.",
        "convo::": "Load, create conversation.",
        "role::": "Load built in system roles.",
        "clear::": "Clear the screen.",
        "tokens::": "Token usage summary.",
        "save::": "Save setting:: changes.",
        "exit::": "Exit symbiote.",
        "setting::": "View, update symbiote settings.",
        "maxtoken::": "Change maxtoken setting.",
        "model::": "Change AI model.",
        "cd::": "Change working directory.",
        "pwd::": "Show current working directory.",
        "file::": "Load a file for submission.",
        "get::": "Load a webpage for submission.",
        "tree::": "Load a directory tree for submission.",
        "shell::": "Load the symbiote bash shell.",
        "ls::": "Load ls output for submission."
        }

# Configure prompt settings.
prompt_style = Style.from_dict({
        '': '#f95393',  # Matrix green text color
        'prompt': '#06AC6C',  # text color for the prompt
        'bottom-toolbar': 'bg:#e5e5e5 #4B4B4B',  # Bottom toolbar style
        'bottom-toolbar.off': 'bg:#e5e5e5 #9A9A9A',  # Bottom toolbar off style
    })

pricing = {"gpt-4": { "prompt": .03, "completion": .06 },
           "gpt-4-32k": { "prompt": .06, "completion": .12},
           "gpt-3.5-turbo": { "prompt": .002, "completion": .002}
           }

# Default settings for openai and symbiot module.
symbiote_settings = {
        "model": "gpt-3.5-turbo",
        "max_tokens": 512,
        "temperature": 0.6,
        "top_p": 1,
        "n": 0,
        "stream": True,
        "stop": "stop::",
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "logit_bias": 0,
        "user": "smallroom",
        "default_max_tokens": 512,
        "conversation_percent": .6,
        "chunk_size": 256,
        "conversation": "conversation.json",
        "vi_mode": False
    }

keybindings = {}

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

check_libmagic()


class symchat():
    ''' Chat class '''
    def __init__(self, *args, **kwargs):
        # Autoflush output buffer
        sys.stdout = io.TextIOWrapper(
                open(sys.stdout.fileno(), 'wb', 0),
                write_through=True
            )

        if 'debug' in kwargs:
            self.debug = kwargs['debug']
        else:
            self.debug = False

        if 'working_directory' in kwargs:
            self.working_directory = kwargs['working_directory']
        else:
            self.working_directory = os.getcwd()

        self.symbiote_settings = symbiote_settings 

        # Load symbiote core 
        self.sym = core.symbiotes(settings=self.symbiote_settings)
        signal.signal(signal.SIGINT, self.sym.handle_ctrl_c)

        # Set symbiote home path parameters
        home_dir = os.path.expanduser("~")
        symbiote_dir = os.path.join(home_dir, ".symbiote")
        if not os.path.exists(symbiote_dir):
            os.mkdir(symbiote_dir)

        # Set symbiote conf file
        self.config_file = os.path.join(symbiote_dir, "config")
        if not os.path.exists(self.config_file):
            self.save_settings(settings=self.symbiote_settings)
        else:
            self.symbiote_settings = self.load_settings()

        # Get hash for current settings
        self.settings_hash = hash(json.dumps(self.symbiote_settings, sort_keys=True))

        # Set the conversations directory
        self.conversations_dir = os.path.join(symbiote_dir, "conversations")
        if not os.path.exists(self.conversations_dir):
            os.mkdir(self.conversations_dir)

        # Set the default conversation
        self.conversations_file = os.path.join(self.conversations_dir, self.symbiote_settings['conversation'])
        self.convo_file = os.path.basename(self.conversations_file)
        if not os.path.exists(self.conversations_file):
            self.sym.save_conversation([], self.conversations_file)

        # Set conversations catch-all file 
        self.conversations_dump = os.path.join(self.conversations_dir, "dump.json")
        if not os.path.exists(self.conversations_file):
            self.sym.save_conversation([], self.conversations_file)

        # Set symbiote shell history file
        history_file = os.path.join(symbiote_dir, "symbiote_shell_history")
        if not os.path.exists(history_file):
            open(history_file, 'a').close()

        self.history = FileHistory(history_file)


        # Load the default conversation
        self.current_conversation = self.sym.load_conversation(self.conversations_file)

        self.token_track = {
            'truncated_tokens': 0,
            'user_tokens': 0,
            'total_user_tokens': 0,
            'completion_tokens': 0,
            'total_completion_tokens': 0,
            'rolling_tokens': 0,
            'cost': 0
        }

        self.command_list = command_list
        commands = []
        for command in self.command_list:
            commands.append(command)

        self.command_completer = WordCompleter(commands)

        self.suppress = False
        self.role = "user"

    def symhelp(self):
        print("Symbiote Help Menu")
        print("------------------")
        print("Available keywords:")
        # Sort the command list by keys
        sorted_commands = sorted(command_list.items())

        # Set column width for the command column
        cmd_col_width = max(len(cmd) for cmd in self.command_list.keys()) + 2

        # Print the table with aligned columns
        for cmd, desc in sorted_commands:
            print("\t{:<{width}}{}".format(cmd, desc, width=cmd_col_width))

    def launch_animation(self, state):

        def hide_cursor():
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()

        def show_cursor():
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()

        def terminal_animation(stop_event):
                # define the animation frames
                #frames = ["|", "/", "-", "\\"]
                frames = []
                start_code_point = 0x1D300
                end_code_point = 0x1D300 + 87
                for code_point in range(start_code_point, end_code_point):
                    frames.append(chr(code_point))

                print()
                hide_cursor()

                # loop through the animation frames
                while not stop_event.is_set():
                    for frame in frames:
                        print(f"\r{frame}", end="", flush=True)
                        time.sleep(0.2)
                print()
                show_cursor()

        # create a thread for the terminal animation
        if state == True:
            # Create an Event object to signal the thread to stop
            self.stop_event = threading.Event()

            # Start the animation thread
            self.animation_thread = threading.Thread(target=terminal_animation, args=(self.stop_event,))
            self.animation_thread.start()
        else: 
            self.stop_event.set()
            self.animation_thread.join()
            print()

    def symconvo(self):
        conversation_files = self.sym.list_conversations(self.conversations_dir)

        if not conversation_files:
            return

        conversation_files.append(Choice("new", name="Create new conversation."))

        selected_file = inquirer.select(
            message="Select a conversation:",
            choices=conversation_files,
            mandatory=False
        ).execute()

        if selected_file == None:
            return

        if selected_file == "new":
            selected_file = inquirer.text(message="File name:").execute()
            self.conversations_file = os.path.join(self.conversations_dir, selected_file)
            self.current_conversation = self.sym.save_conversation([], self.conversations_file)

        self.symbiote_settings['conversation'] = selected_file
        self.conversations_file = os.path.join(self.conversations_dir, selected_file)
        self.current_conversation = self.sym.load_conversation(self.conversations_file)
        self.convo_file = os.path.basename(self.conversations_file)

        print(f"Loaded conversation: {selected_file}")

        return

    def symrole(self, role=False):
        # Handle role functionality
        available_roles = roles.get_roles()

        if not available_roles:
            return

        role_list = []
        for role in available_roles:
            role_list.append(role)

        selected_role = inquirer.select(
            message="Select a role:",
            choices=role_list,
            mandatory=False
        ).execute()

        if selected_role == None:
            return

        self.suppress = True
        self.send_message(available_roles[selected_role])

        return

    def symmodel(self, *args):
        # Handle model functionality
        model_list = self.sym.get_models()

        try:
            model_name = args[0]
            if model_name in model_list:
                selected_model = args[0]
            else:
                print(f"No such model: {model_name}")
                return None
        except:
            selected_model = inquirer.select(
                message="Select a model:",
                choices=model_list
            ).execute()

        self.symbiote_settings['model'] = selected_model
        self.sym.update_symbiote_settings(settings=self.symbiote_settings)

        return None


    def chat(self, *args, **kwargs):
        # Begin symchat loop
        #history = InMemoryHistory() 
        if 'run' in kwargs:
            self.run = kwargs['run']
        else:
            self.run = False

        if 'user_input' in kwargs:
            self.user_input = kwargs['user_input']

        os.system('reset')
        if 'working_directory' in kwargs:
            self.working_directory = kwargs['working_directory']
            self.previous_directory = self.working_directory
            os.chdir(self.working_directory)

        self.suppress = False
        bindings = KeyBindings()
       
        @bindings.add(Keys.ControlX)
        def _(event):
            self.sym.handle_control_x()
            #event.app.exit()

        #chat_session = PromptSession(key_bindings=bindings, completer=self.command_completer, vi_mode=self.symbiote_settings['vi_mode'], history=self.history, style=prompt_style)
        chat_session = PromptSession(key_bindings=bindings, vi_mode=self.symbiote_settings['vi_mode'], history=self.history, style=prompt_style)
        while True:
            # Chack for a change in settings and write them
            check_settings = hash(json.dumps(self.symbiote_settings, sort_keys=True)) 
            if check_settings != self.settings_hash:
                self.save_settings(settings=self.symbiote_settings)
                self.settings_hash = check_settings

            self.toolbar_data = f"Model: {self.symbiote_settings['model']}    Current Conversation: {self.convo_file}\nUser: {self.token_track['user_tokens']} Assistant: {self.token_track['completion_tokens']} Conversation: {self.token_track['truncated_tokens']} Total Used: {self.token_track['rolling_tokens']} Cost: ${self.token_track['cost']:.2f}"

            if self.user_input is None or self.user_input == "":
                self.user_input = chat_session.prompt(message="symchat> ",
                                                   multiline=True,
                                                   bottom_toolbar=self.toolbar_data,
                                                   vi_mode=self.symbiote_settings['vi_mode']
                                                )

            self.user_input = self.process_commands(self.user_input)

            if self.user_input is None or re.search(r'^\n+$', self.user_input) or self.user_input== "":
                self.user_input = ""
                if self.run:
                    break 

                continue

            if re.search(r'^shell::', self.user_input):
                shell.symBash().launch_shell()
                continue

            if re.search(r"^reset::", self.user_input):
                chat_session = PromptSession(key_bindings=bindings, vi_mode=self.symbiote_settings['vi_mode'], history=self.history, style=prompt_style)
                continue  

            self.send_message(self.user_input)

            self.user_input = ""

            if self.run:
                break

            continue

        self.sym.save_conversation(self.current_conversation, self.conversations_dump)

        return

    def send_message(self, user_input):
        if self.suppress and not self.run:
            self.launch_animation(True)

        returned = self.sym.send_request(user_input, self.current_conversation, suppress=self.suppress, role=self.role)

        if self.suppress and not self.run:
            self.launch_animation(False)
            pass

        self.current_conversation = returned[0]

        self.token_track['truncated_tokens'] = returned[1]
        self.token_track['user_tokens'] = returned[2]
        self.token_track['total_user_tokens'] += returned[2]
        self.token_track['completion_tokens'] = returned[3]
        self.token_track['total_completion_tokens'] += returned[3]
        self.token_track['rolling_tokens'] += self.token_track['truncated_tokens']


        if pricing[self.symbiote_settings['model']] is not None:
            prompt_cost = 0
            completion_cost = 0

            prompt_cost = (self.token_track['user_tokens'] / 1000 * pricing[self.symbiote_settings['model']]['prompt'])
            completion_cost = (self.token_track['completion_tokens'] / 1000 * pricing[self.symbiote_settings['model']]['completion'])
            self.token_track['cost'] += (prompt_cost + completion_cost) 
        else:
            self.token_track['cost'] = "unknown"

        self.sym.change_max_tokens(self.symbiote_settings['default_max_tokens'])
        self.suppress = False
        self.role = "user"

        return

    def symtokens(self):
        print(f"\nToken Details:\n\tLast User: {self.token_track['user_tokens']}\n\tTotal User: {self.token_track['total_user_tokens']}\n\tLast Completion: {self.token_track['completion_tokens']}\n\tTotal Completion: {self.token_track['total_completion_tokens']}\n\tLast Conversation: {self.token_track['truncated_tokens']}\n\tTotal Used Tokens: {self.token_track['rolling_tokens']}\n\tToken Cost: ${self.token_track['cost']:.2f}\n")
        return self.token_track

    def process_commands(self, user_input):

        if re.search(r'^help::', user_input):
            self.symhelp()
            return None

        if re.search(r'^convo::', user_input):
            self.symconvo()
            return None

        if re.search(r"^clear::", user_input):
            self.symclear()
            return None

        if re.search(r"^tokens::", user_input):
            self.symtokens()
            return None

        if re.search(r"^save::", user_input):
            self.save_settings(settings=self.symbiote_settings)
            return None

        if re.search(r'^exit::', user_input):
            self.save_settings(settings=self.symbiote_settings)
            os.system('reset')
            sys.exit(0)

        # Trigger to choose role
        role_pattern = r'^role::|role:(.*):'
        match = re.search(role_pattern, user_input)
        if match:
            self.suppress = True
            available_roles = roles.get_roles()

            if match.group(1):
                selected_role = match.group(1).strip()
            else:
                if not available_roles:
                    return

                role_list = []
                for role_name in available_roles:
                    role_list.append(role_name)

                selected_role = inquirer.select(
                    message="Select a role:",
                    choices=role_list,
                    mandatory=False
                ).execute()

                if selected_role == None:
                    return

            self.role = "system"

            return available_roles[selected_role] 

        # Trigger to display openai settings  
        setting_pattern = r'^setting::|setting:(.*):(.*):'
        match = re.search(setting_pattern, user_input)
        if match:
            if match.group(1):
                setting = match.group(1)
                set_value = match.group(2)
                if setting in self.symbiote_settings:
                    get_type = type(self.symbiote_settings[setting])
                    if get_type == bool:
                        if re.search(r'^false$|^0$|^off$', set_value):
                            set_value = False
                        else:
                            set_value = True
                    else:        
                        set_value = get_type(set_value) 

                    self.symbiote_settings[setting] = set_value
                    self.sym.update_symbiote_settings(settings=symbiote_settings)
            else:
                print("Current OpenAI Settings:")

                for setting in self.symbiote_settings:
                    print(f"\t{setting}: {self.symbiote_settings[setting]}")

            return None

        # Trigger for changing max_tokens. 
        maxtoken_pattern = r'^maxtoken::|maxtoken:(.*):'
        match = re.search(maxtoken_pattern, user_input)
        if match:
            if match.group(1):
                setmaxtoken = int(match.group(1))
                self.sym.change_max_tokens(setmaxtoken, update=True)
            else:
                print("Maxtoken menu needed.")

            return None

        # Trigger for changing gpt model 
        model_pattern = r'^model::|model:(.*):'
        match = re.search(model_pattern, user_input)
        if match:
            if match.group(1):
                model_name = match.group(1).strip()
                self.symmodel(model_name)
            else:
                self.symmodel()

            return None

        # Trigger for changing working directory in chat
        cd_pattern = r'^cd::|cd:(.*):'
        match = re.search(cd_pattern, user_input)
        if match:
            if match.group(1):
                requested_directory = match.group(1).strip()

            else:
                requested_directory = '~'

            if requested_directory == '-':
                requested_directory = self.previous_directory

            requested_directory = os.path.abspath(os.path.expanduser(requested_directory))
            if os.path.exists(requested_directory):
                self.previous_directory = self.working_directory
                self.working_directory = requested_directory 
                os.chdir(self.working_directory)
            else:
                print(f"Directory does not exit: {requested_directory}")

            return None

        # Trigger to get current working directory
        pwd_pattern = r'^pwd::'
        match = re.search(pwd_pattern, user_input)
        if match:
            print(self.working_directory)
            return None

        # Trigger for file:filename processing. Load file content into user_input for openai consumption.
        file_pattern = r'file::|file:(.*:)(.*):|file:(.*):{1,2}'
        match = re.search(file_pattern, user_input)
        file_path = None
        sub_command = None

        if match: 
            self.suppress = True
            if match.group(1):
                matched = match.group(1)
                if matched == "meta:":
                    sub_command = "meta"
                    if match.group(2):
                        file_path = os.path.expanduser(match.group(2))
                else:
                    file_path = os.path.expanduser(match.group(1))

            if file_path is None:
                start_path = "./"
                file_path = inquirer.filepath(
                        message="Insert file contents:",
                        default=start_path,
                        validate=PathValidator(is_file=True, message="Input is not a file"),
                        wrap_lines=True,
                        mandatory=False,
                        keybindings=keybindings
                    ).execute()

            if file_path is None:
                return None 
            
            file_path = os.path.expanduser(file_path)

            if not os.path.isfile(file_path):
                print(f"File not found: {file_path}")
                return None
            
            mime_type = magic.from_file(file_path, mime=True)

            if sub_command is not None:
                # Process file sub commands
                if sub_command == "meta":
                    meta_data = utils.extract_metadata(file_path)
                    content = json.dumps(meta_data)
                else:
                    print(f"Unknown sub command: {sub_command}")

                user_input = user_input[:match.start()] + content + user_input[match.end():]

            else:
                if re.search(r'^text\/', mime_type):
                    with open(file_path, 'r') as f:
                        content = f.read()

                elif re.search(r'^image\/', mime_type):
                    content = textract.process(file_path, method='tesseract', language='eng')

                elif mime_type == "application/pdf":
                    content = textract.process(file_path, method='tesseract', language='eng')

                else:
                    content = textract.process(file_path)

                content = content.encode('utf-8')

                file_content = f"The following is the contents of {file_path}.\nIMPORTANT: You will not respond until prompted.\nIMPORTANT: You will only consume the contents and confirm receipt.\nIMPORTANT: You will remember this information for future use.\n"
                file_content += '\n```\n{}\n```\n'.format(content)
                user_input = user_input[:match.start()] + file_content + user_input[match.end():]

            return user_input

        # Trigger for get:URL processing. Load website content into user_input for openai consumption.
        get_pattern = r'get::|get:(https?://\S+):'
        match = re.search(get_pattern, user_input)
        if match:
            self.suppress = True
            if match.group(1):
                url = match.group(1)
            else:
                url = inquirer.text(
                        message="URL to load:",
                        mandatory=False,
                        keybindings=keybindings
                    ).execute()
            
            if url == None:
                return None 

            print(f"Fetching content from: {url}")
            website_content = self.pull_website_content(url)
            user_input = re.sub(match.re, website_content, user_input)

            return user_input 

        # Trigger for ls:path processing. List the content of the specified directory.
        ls_pattern = r'ls:(.*):'
        match = re.search(ls_pattern, user_input)
        if match:
            self.suppress = True
            path = match.group(1)
            if os.path.isdir(path):
                dir_content = os.listdir(path)
                content = f"Directory content of {path}: \n" + "\n".join(dir_content)
                insert_content = ' ``` {} ``` '.format(content)
                user_input = re.sub(ls_pattern, insert_content, user_input)
            else:
                print("Directory not found. Please try again.")
                return None

            return user_input 

        # Trigger for tree:path processing. Perform a recursive directory listing of all files.
        tree_pattern = r'tree:(.*):|tree::'
        match = re.search(tree_pattern, user_input)
        if match:
            self.suppress = True
            if match.group(1):
                dir_path = match.group(1)
            else:
                start_path = "./"
                dir_path = inquirer.filepath(
                        message="Insert file contents:",
                        default=start_path,
                        validate=PathValidator(is_dir=True, message="Input is not dir"),
                        only_directories=True,
                        wrap_lines=True,
                        mandatory=False,
                        keybindings=keybindings
                    ).execute()

            if dir_path == None:
                return None 

            if os.path.isdir(dir_path):
                tree_content = tree.display_tree(dir_path, string_rep=True)

                tree_content = f"Tree-styled output of the directory {dir_path}:\n\n```\n{tree_content}\n```"
                user_input = re.sub(tree_pattern, tree_content, user_input)
            else:
                print("Directory not found. Please try again.")
                return None

            return user_input 

        return user_input

    def pull_website_content(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the website content: {e}")
            return ""

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove all script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get the text content
        text = soup.get_text()

        # Remove extra whitespace and newlines
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        # Encapsulate the extracted text within triple backticks
        text = f"Here is more content from the website {url}.\nIMPORTANT: Do not provide feedback from this content unless specifically asked.\n```{text}``` "

        return text

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def save_settings(self, settings):
        try:
            with open(self.config_file, "w") as file:
                json.dump(settings, file)
        except Exception as e:
            print(f"Error Writing: {e}")

    def load_settings(self):
        try:
            with open(self.config_file, "r") as file:
                symbiote_settings = json.load(file)
        except Exception as e:
            print(f"Error Reading: {e}")

        return symbiote_settings
