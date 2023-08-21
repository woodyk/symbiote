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
import clipboard
import json
import queue
import pygame
import pygame.freetype

from bs4 import BeautifulSoup

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import PathValidator
from pynput.keyboard import Controller, Key

from prompt_toolkit import Application
from prompt_toolkit.history import InMemoryHistory, FileHistory
from prompt_toolkit.shortcuts import PromptSession, prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit.widgets import TextArea, Frame, Box
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.containers import HSplit, VSplit

import symbiote.core as core
import symbiote.shell as shell
import symbiote.roles as roles
import symbiote.utils as utils
import symbiote.speech as speech
import symbiote.logo as logo

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
        "summary::": "Pull nouns, summary, and metadata for a file.",
        "get::": "Load a webpage for submission.",
        "tree::": "Load a directory tree for submission.",
        "shell::": "Load the symbiote bash shell.",
        "clipboard::": "Load clipboard contents into symbiote.",
        "ls::": "Load ls output for submission.",
        "search::": "Search index for specific data.",
        "history::": "Show discussion history.",
        "learn::": "Train AI model on given data in directory. *",
        "structure::": "Define a data scructure. *",
        }


audio_triggers = {
        'speech_off': [r'keyword speech off', 'setting:speech:0:'],
        'speech_on': [r'keyword speech on', 'setting:speech:1:'],
        'interactive': [r'keyword interactive mode', 'setting:listen:0:'],
        'settings': [r'keyword show setting', 'setting::'],
        'file': [r'keyword open file', 'file::'],
        'shell': [r'keyword (open shell|openshell)', 'shell::'],
        'role': [r'keyword change (role|roll)', 'role::'],
        'conversation': [r'keyword change conversation', 'convo::'],
        'model': [r'keyword change model', 'model::'],
        'get': [r'keyword get website', 'get::'],
        'clipboard_url': [r'keyword get clipboard [url|\S+site]', 'clipboard:get:'],
        'clipboard': [r'keyword get clipboard', 'clipboard::'],
        'exit': [r'keyword exit now', 'exit::'],
        'help': [r'keyword (get|show) help', 'help::'],
        'tokens': [r'keyword (get|show) tokens', 'tokens::'],
        'summary': [r'keyword summarize file', 'summary::'],
        'search': [r'keyword search query', 'search::'],
        'keyword': [r'keyword (get|show) keyword', 'keywords::'],
        'history': [r'keyword (get|show) history', 'history::'],
        'perifious': [r'(i cast|icast) periph', 'perifious::']
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
           "gpt-3.5-turbo": { "prompt": .002, "completion": .002},
           "gpt-3.5-turbo-16k": { "prompt": .003, "completion": .004}
           }

# Default settings for openai and symbiot module.
homedir = os.getenv('HOME')
symbiote_settings = {
        "model": "gpt-3.5-turbo",
        "max_tokens": 512,
        "temperature": 0.6,
        "top_p": 1,
        "n": 0,
        "stream": True,
        "stop": "<<<stop>>>",
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "logit_bias": 0,
        "user": "smallroom",
        "default_max_tokens": 512,
        "conversation_percent": .6,
        "chunk_size": 256,
        "completion": False,
        "conversation": "conversation.jsonl",
        "vi_mode": False,
        "speech": False,
        "listen": False,
        "debug": False,
        "elasticsearch": "http://dockera.vm.sr:9200",
        "elasticsearch_index": "symbiote",
        "symbiote_path": os.path.join(homedir, ".symbiote"),
        "perifious": False,
        "role": "DEFAULT"
    }

keybindings = {}

class symchat():
    ''' Chat class '''
    def __init__(self, *args, **kwargs):
        # Autoflush output buffer
        sys.stdout = io.TextIOWrapper(
                open(sys.stdout.fileno(), 'wb', 0),
                write_through=True
            )

        self.symbiote_settings = symbiote_settings 
        self.audio_triggers = audio_triggers

        if 'debug' in kwargs:
            self.symbiote_settings['debug'] = kwargs['debug']
            
        if 'working_directory' in kwargs:
            self.working_directory = kwargs['working_directory']
        else:
            self.working_directory = os.getcwd()
       
        # Set symbiote home path parameters
        home_dir = os.path.expanduser("~")
        symbiote_dir = self.symbiote_settings['symbiote_path']
        if not os.path.exists(symbiote_dir):
            os.mkdir(symbiote_dir)

        # Set symbiote conf file
        self.config_file = os.path.join(symbiote_dir, "config")
        if not os.path.exists(self.config_file):
            self.save_settings(settings=self.symbiote_settings)
        else:
            self.symbiote_settings = self.load_settings()

        # Load symbiote core 
        self.sym = core.symbiotes(settings=self.symbiote_settings)
        signal.signal(signal.SIGINT, self.sym.handle_control_c)

        # Get hash for current settings
        self.settings_hash = hash(json.dumps(self.symbiote_settings, sort_keys=True))

        # Set the conversations directory
        self.conversations_dir = os.path.join(symbiote_dir, "conversations")
        if not os.path.exists(self.conversations_dir):
            os.mkdir(self.conversations_dir)

        # Set the default conversation
        self.conversations_file = os.path.join(self.conversations_dir, self.symbiote_settings['conversation'])
        self.convo_file = os.path.basename(self.conversations_file)

        # Set conversations catch-all file 
        self.conversations_dump = os.path.join(self.conversations_dir, "dump.jsonl")

        # Set symbiote shell history file
        history_file = os.path.join(symbiote_dir, "symbiote_shell_history")
        if not os.path.exists(history_file):
            open(history_file, 'a').close()

        self.history = FileHistory(history_file)

        # Load the default conversation
        self.current_conversation = self.sym.load_conversation(self.conversations_file)

        # Load utils object
        self.symutils = utils.utilities(settings=self.symbiote_settings)

        self.token_track = {
            'truncated_tokens': 0,
            'user_tokens': 0,
            'total_user_tokens': 0,
            'completion_tokens': 0,
            'total_completion_tokens': 0,
            'rolling_tokens': 0,
            'last_char_count': 0,
            'cost': 0,
            'model_tokens': 0,
            'system_count': 0
        }

        self.command_list = command_list
        commands = []
        for command in self.command_list:
            commands.append(command)

        self.command_completer = WordCompleter(commands)

        if 'suppress' in kwargs:
            self.suppress = kwargs['suppress']
        else:
            self.suppress = False

        self.role = "user"

    def keyboardContinue(self):
        keyboard = Controller()

        keyboard.press(Key.esc)
        keyboard.press(Key.enter)

        # Small delay for certain applications that might need it
        time.sleep(0.1)

        keyboard.release(Key.esc)
        keyboard.release(Key.enter)

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

                hide_cursor()

                # loop through the animation frames
                while not stop_event.is_set():
                    for frame in frames:
                        print(f"{frame}", end="", flush=True)
                        time.sleep(0.3)
                        print("\b", end="", flush=True)
                        if stop_event.is_set():
                            break
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

    def symconvo(self, convo=False):
        conversation_files = sorted(self.sym.list_conversations(self.conversations_dir))

        if convo:
            selected_file = convo
        else:
            if not conversation_files:
                return

            conversation_files.append(Choice("new", name="Create new conversation."))
            conversation_files.append(Choice("clear", name="Clear conversation."))

            selected_file = inquirer.select(
                message="Select a conversation:",
                choices=conversation_files,
                mandatory=False
            ).execute()

        if selected_file == None:
            return

        if selected_file == "new":
            selected_file = inquirer.text(message="File name:").execute()
        elif selected_file == "clear":
            clear_file = inquirer.select(
                message="Select a conversation:",
                choices=conversation_files, 
                mandatory=False
            ).execute()

            clear_file = os.path.join(self.conversations_dir, clear_file)

            try:
                with open(clear_file, 'w') as file:
                    pass
            except:
                print(f"Unable to clear {clear_file}")

            if self.symbiote_settings['conversation'] == os.path.basename(clear_file):
                self.current_conversation = self.sym.load_conversation(clear_file)

            print(f"Conversation cleared: {clear_file}")

            return

        self.symbiote_settings['conversation'] = selected_file
        self.conversations_file = os.path.join(self.conversations_dir, selected_file)
        self.current_conversation = self.sym.load_conversation(self.conversations_file)
        self.convo_file = os.path.basename(self.conversations_file)

        print(f"Loaded conversation: {selected_file}")

        return

    def symrole(self, role=False):
        # Handle role functionality
        self.suppress = True
        available_roles = roles.get_roles()

        if not available_roles:
            return

        if role in available_roles:
            self.send_message(available_roles[role])
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

        if 'completion' in kwargs:
            self.completion = kwargs['completion']
        else:
            self.completion = False

        if 'suppress' in kwargs:
            self.suppress = kwargs['suppress']
        else:
            self.suppress = False

        if 'enable' in kwargs:
            self.enable = kwargs['enable']
            self.run = True
        else:
            self.enable = False

        if 'user_input' in kwargs:
            self.user_input = kwargs['user_input']

        if 'working_directory' in kwargs:
            self.working_directory = kwargs['working_directory']
            self.previous_directory = self.working_directory
            os.chdir(self.working_directory)

        bindings = KeyBindings()

        @bindings.add('c-q')
        def _(event):
            self.user_input = "" 
       
        chat_session = PromptSession(key_bindings=bindings, vi_mode=self.symbiote_settings['vi_mode'], history=self.history, style=prompt_style)

        while True:
            # Chack for a change in settings and write them
            check_settings = hash(json.dumps(self.symbiote_settings, sort_keys=True)) 

            if self.token_track['system_count'] > self.token_track['model_tokens']:
                self.symrole(self.symbiote_settings['role'])
                self.token_track['system_count'] = 0

            if self.symbiote_settings['listen'] and self.run is False:
                if not hasattr(self, 'symspeech'):
                    self.symspeech = speech.SymSpeech(settings=self.symbiote_settings)
                    self.speechQueue = self.symspeech.start_keyword_listen()

                self.launch_animation(True)
                self.user_input = self.symspeech.keyword_listen()
                self.launch_animation(False)
                self.enable = True
                self.run = True


            # Get the current path
            current_path = os.getcwd()

            # Get the home directory
            home_dir = os.path.expanduser('~')

            # Replace the home directory with ~
            if current_path.startswith(home_dir):
                current_path = '~' + current_path[len(home_dir):]

            self.toolbar_data = f"Model: {self.symbiote_settings['model']} Current Conversation: {self.convo_file}\nLast Char Count: {self.token_track['last_char_count']}\nUser: {self.token_track['user_tokens']} Assistant: {self.token_track['completion_tokens']} Conversation: {self.token_track['truncated_tokens']} Total Used: {self.token_track['rolling_tokens']} Cost: ${self.token_track['cost']:.2f}\ncwd: {current_path}"

            if self.run is False:
                self.user_input = chat_session.prompt(message="symchat> ",
                                                   multiline=True,
                                                   default=self.user_input,
                                                   bottom_toolbar=self.toolbar_data,
                                                   vi_mode=self.symbiote_settings['vi_mode']
                                                )

            self.user_input = self.process_commands(self.user_input)

            if check_settings != self.settings_hash:
                self.save_settings(settings=self.symbiote_settings)
                self.settings_hash = check_settings

            if self.user_input is None or re.search(r'^\n+$', self.user_input) or self.user_input== "":
                self.user_input = ""
                if self.run is True and self.enable is False:
                    return "OK"
                    break

                self.enable = False
                self.run = False
                continue

            returned = self.send_message(self.user_input)

            self.user_input = ""

            if self.enable is True:
                self.run = False
                self.enable = False

            if self.run is True:
                return returned

            continue

        return 

    def send_message(self, user_input):
        #if self.suppress and not self.run:
        #    self.launch_animation(True)
        self.current_conversation = self.sym.load_conversation(self.conversations_file)

        returned = self.sym.send_request(user_input, self.current_conversation, completion=self.symbiote_settings['completion'], suppress=self.suppress, role=self.role)
        #if self.suppress and not self.run:
        #    self.launch_animation(False)
        #    pass

        self.current_conversation = returned[0]

        self.token_track['truncated_tokens'] = returned[1]
        self.token_track['user_tokens'] = returned[2]
        self.token_track['total_user_tokens'] += returned[2]
        self.token_track['completion_tokens'] = returned[3]
        self.token_track['total_completion_tokens'] += returned[3]
        self.token_track['rolling_tokens'] += self.token_track['truncated_tokens']
        self.token_track['last_char_count'] = returned[4]
        self.token_track['model_tokens'] = returned[5]

        self.token_track['system_count'] = returned[2] + returned[3]

        if pricing[self.symbiote_settings['model']] is not None:
            prompt_cost = 0
            completion_cost = 0

            prompt_cost = (self.token_track['user_tokens'] / 1000 * pricing[self.symbiote_settings['model']]['prompt'])
            completion_cost = (self.token_track['completion_tokens'] / 1000 * pricing[self.symbiote_settings['model']]['completion'])
            self.token_track['cost'] += (prompt_cost + completion_cost) 
        else:
            self.token_track['cost'] = "unknown"

        self.sym.change_max_tokens(self.symbiote_settings['default_max_tokens'])
        self.role = "user"

        if self.symbiote_settings['speech'] and self.suppress is False:
            if not hasattr(self, 'symspeech'):
                #self.symspeech = speech.SymSpeech(debug=self.symbiote_settings['debug'])
                self.symspeech = speech.SymSpeech()

            last_message = self.current_conversation[-1]
            speech_thread = threading.Thread(target=self.symspeech.say, args=(last_message['content'],))
            speech_thread.start()

        self.suppress = False

        return returned

    def symtokens(self):
        print(f"\nToken Details:\n\tLast User: {self.token_track['user_tokens']}\n\tTotal User: {self.token_track['total_user_tokens']}\n\tLast Completion: {self.token_track['completion_tokens']}\n\tTotal Completion: {self.token_track['total_completion_tokens']}\n\tLast Conversation: {self.token_track['truncated_tokens']}\n\tTotal Used Tokens: {self.token_track['rolling_tokens']}\n\tToken Cost: ${self.token_track['cost']:.2f}\n")
        return self.token_track

    def process_commands(self, user_input):
        # Audio keyword triggers
        for keyword in self.audio_triggers:
            if re.search(self.audio_triggers[keyword][0], user_input):
                user_input = self.audio_triggers[keyword][1]
                break

        if re.search(r'^perifious::', user_input):
            self.symspeech = speech.SymSpeech(debug=self.symbiote_settings['debug'])
            self.symspeech.say('Your wish is my command!')
            if self.symbiote_settings['perifious']:
                user_input = 'setting:perifious:0:'
            else:
                user_input = 'setting:perifious:1:'

        if re.search(r'^shell::', user_input):
            shell.symBash().launch_shell()
            return None

        if re.search(r'^help::', user_input):
            self.symhelp()
            return None

        if re.search(r"^clear::|^reset::", user_input):
            os.system('reset')
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

        # Trigger to read clipboard contents
        clipboard_pattern = r'clipboard::|clipboard:(.*):'
        match = re.search(clipboard_pattern, user_input)
        if match:
            self.suppress = True
            contents = clipboard.paste()
            if match.group(1):
                sub_command = match.group(1).strip()
                if sub_command == 'get':
                    if re.search(r'^https?://\S+', contents):
                        print(f"Fetching content from: {contents}")
                        website_content = self.pull_website_content(contents)
                        user_input = user_input[:match.start()] + website_content + user_input[match.end():]
            else:
                user_input = user_input[:match.start()] + contents + user_input[match.end():]

            return user_input

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
                    choices=sorted(role_list),
                    mandatory=False
                ).execute()

                if selected_role == None:
                    return

            self.role = "system"
            self.symbiote_settings['role'] = selected_role 

            return available_roles[selected_role] 

        # Trigger to apply a system role
        system_pattern = r'^system::(.*)'
        match = re.search(system_pattern, user_input)
        if match:
            self.suppress = True
            system_prompt = match.group(1).strip()
            self.role = "system"

            return system_prompt

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
                    self.sym.update_symbiote_settings(settings=self.symbiote_settings)
                    self.symutils = utils.utilities(settings=self.symbiote_settings)
                    self.save_settings(settings=self.symbiote_settings)
            else:
                print("Current Symbiote Settings:")
                sorted_settings = sorted(self.symbiote_settings) 
                for setting in sorted_settings:
                    if self.symbiote_settings['perifious'] is False and setting == 'perifious':
                        continue
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

        # Trigger for changing the conversation file
        convo_pattern = r'^convo::|convo:(.*):'
        match = re.search(convo_pattern, user_input)
        if match:
            if match.group(1):
                convo_name = match.group(1).strip()
                self.symconvo(convo_name) 
            else:
                self.symconvo()
        
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

        # Trigger to list verbal keywords prompts.
        keywords_pattern = r'^keywords::'
        match = re.search(keywords_pattern, user_input)
        if match:
            for keyword in self.audio_triggers:
                if keyword == 'perifious':
                    continue
                print(f'trigger: {self.audio_triggers[keyword][0]}')

            return None

        # Trigger to get current working directory
        pwd_pattern = r'^pwd::'
        match = re.search(pwd_pattern, user_input)
        if match:
            print(self.working_directory)
            return None

        # Trigger for summary:: processing. Load file content and generate a json object about the file.
        summary_pattern = r'summary::|summary:(.*):(.*):|summary:(.*):'
        match = re.search(summary_pattern, user_input)
        file_path = None
        
        if match:
            self.suppress = True
            index = False

            if match.group(1):
                file_path = match.group(1)
                screenshot_pattern = r'^screenshot$'
                if re.search(screenshot_pattern, file_path):
                    file_path = self.symutils.getScreenShot()
                    index = True

            if match.group(2):
                reindex = match.group(2)
                if reindex.lower() == ("1" or "true"):
                    reindex = True
                else:
                    reindex = False

            if file_path is None:
                start_path = "./"
                file_path = inquirer.filepath(
                        message="Summarize file:",
                        default=start_path,
                        #validate=PathValidator(is_file=True, message="Input is not a file"),
                        wrap_lines=True,
                        mandatory=False,
                        keybindings=keybindings
                    ).execute()

            if file_path is None:
                return None

            file_path = os.path.expanduser(file_path)

            if os.path.isdir(file_path):
                # prompt to confirm path indexing
                if index is False:
                    index = inquirer.confirm(message=f'Index {file_path}?').execute()

                if index is True:
                    self.symutils.createIndex(file_path, reindex=reindex)

                return None
            elif not os.path.isfile(file_path):
                print(f"File not found: {file_path}")
                return None

            self.symutils.createIndex(file_path, reindex=reindex)

            #summary = self.symutils.summarizeFile(file_path)

            #if self.symbiote_settings['debug']:
            #    print(json.dumps(summary, indent=4))

            #user_input = user_input[:match.start()] + json.dumps(summary) + user_input[match.end():]

            return None 

        # Trigger to search es index
        search_pattern = r'^search::|^search:(.*):'
        match = re.search(search_pattern, user_input)
        if match:
            self.suppress = True
            if match.group(1):
                query = match.group(1)
            elif self.symbiote_settings['listen']:
                obj = speech.SymSpeech(debug=self.symbiote_settings['debug'])
                obj.say("What do you want to search for?")
                query = obj.listen(5)
                print(query)
                del obj
            else:
                query = inquirer.text(message="Search Term:").execute()
            
            if query is not None:
                results = self.symutils.searchIndex(query)

                user_input = self.symutils.grepFiles(results, query)
                if self.symbiote_settings['debug']:
                    print(json.dumps(results, indent=4))
                    print(user_input)
            else:
                return None

            return user_input

        # Trigger for history::. Show the history of the messages.
        history_pattern = r'^history::|^history:(.*):'
        match = re.search(history_pattern, user_input)
        if match:
            if match.group(1):
                history_length = int(match.group(1)) + 1
            else:
                history_length = 10

            lines = str()
            for message in self.current_conversation[-history_length:]:
                if message['role'] == 'assistant':
                    lines += f"ROLE: {message['role']}:\n{message['content']}\n\n"


            size = os.get_terminal_size()

            text_area = TextArea(text=lines,
                                 scrollbar=True,
                                 width=(size.columns - 10),
                                 height=30,
                                 focus_on_click=True)


            frame = Frame(text_area, title='History')

            box = Box(frame)

            layout = Layout(HSplit([box]))

            app = Application(layout=layout)
            kb = KeyBindings()

            @kb.add('c-q')
            def _(event):
                event.app.exit()

            app = Application(layout=layout, full_screen=False, key_bindings=kb).run()

            return None


        # Trigger for file:filename processing. Load file content into user_input for ai consumption.
        # file:: - opens file or directory to be pulled into the conversation
        file_pattern = r'file::|file:(.*):|learn:(.*):'
        match = re.search(file_pattern, user_input)
        file_path = None
        sub_command = None
        learn = False

        if match: 
            if re.search(r'^file', user_input):
                self.suppress = True
            elif re.search(r'^learn', user_input):
                learn = True
            else:
                self.suppress = False

            if match.group(1):
                meta_pattern = r'meta:(.*)'
                matched = match.group(1)

                matchb = re.search(meta_pattern, matched)
                if matchb:
                    sub_command = "meta"
                    if matchb.group(1):
                        file_path = os.path.expanduser(matchb.group(1))
                else:
                    file_path = os.path.expanduser(match.group(1))

            if file_path is None:
                start_path = "./"
                file_path = inquirer.filepath(
                        message="Insert file contents:",
                        default=start_path,
                        #validate=PathValidator(is_file=True, message="Input is not a file"),
                        wrap_lines=True,
                        mandatory=False,
                        keybindings=keybindings
                    ).execute()

            if file_path is None:
                return None 
            
            file_path = os.path.expanduser(file_path)
            absolute_path = os.path.abspath(file_path)

            if learn:
                self.symutils.learnFiles(absolute_path)
                return None

            if sub_command is not None:
                # Process file sub commands
                if sub_command == "meta":
                    meta_data = self.symutils.extractMetadata(file_path)
                    content = json.dumps(meta_data)
                else:
                    print(f"Unknown sub command: {sub_command}")
                    return None

                meta_content = f"File name: {absolute_path}\n"
                meta_content += '\n```\n{}\n```\n'.format(content)
                user_input = user_input[:match.start()] + meta_content + user_input[match.end():]

            elif os.path.isfile(file_path):
                content = self.symutils.extractText(file_path)

                file_content = f"File name: {absolute_path}\n"
                file_content += '\n```\n{}\n```\n'.format(content)
                user_input = user_input[:match.start()] + file_content + user_input[match.end():]

            elif os.path.isdir(file_path):
                dir_content = self.symutils.extractDirText(file_path)
                if dir_content is None:
                    return dir_content
                user_input = user_input[:match.start()] + dir_content + user_input[match.end():]

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
            user_input = user_input[:match.start()] + website_content + user_input[match.end():]

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
        # Headers with User-Agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers)
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
        text = f"URL / Website: {url}.\n\n```{text}```\n\n"
        text = str(text)

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
                settings = json.load(file)
        except Exception as e:
            print(f"Error Reading: {e}")

        for setting in self.symbiote_settings:
            if setting not in settings:
                settings[setting] = self.symbiote_settings[setting]

        return settings

class ChatInterface:
    def __init__(self, width, height):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.font = pygame.freetype.Font(None, 24)
        self.input_box = pygame.Rect(100, 100, 140, 32)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.active = False
        self.text = ''
        self.done = False
        self.messages = []

    def draw(self):
        self.screen.fill((30, 30, 30))
        txt_surface = self.font.render(self.text, self.color)
        width = max(200, txt_surface[1].width+10)
        self.input_box.w = width
        self.font.render_to(self.screen, (self.input_box.x+5, self.input_box.y+5), self.text, self.color)
        pygame.draw.rect(self.screen, self.color, self.input_box, 2)

        y = 5
        for message in self.messages:
            self.font.render_to(self.screen, (5, y), message, pygame.Color('white'))
            y += 20

        pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.input_box.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    response = self.send_message(self.text)
                    self.messages.append('You: ' + self.text)
                    self.messages.append('Bot: ' + response)
                    self.text = ''
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode

    def run(self):
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                self.handle_event(event)
            self.draw()

    def send_message(self, message):
        # Replace this with your chatbot's response method
        return "I received your message: " + message

    
    # Call if needed
    #if __name__ == "__main__":
    #    chat = ChatInterface(800, 600)
    #    chat.run()
