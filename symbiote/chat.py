#!/usr/bin/env python3
#
# chat.py

import time
import sys
import os
import io
import re
import signal
#import requests
import threading
#import textract
#import magic
#import subprocess
#import platform
import clipboard
import json
#import queue
#import webbrowser
import pprint

#from bs4 import BeautifulSoup

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
from prompt_toolkit.layout.containers import VSplit

import symbiote.roles as roles
import symbiote.speech as speech
import symbiote.codeextract as codeextract
import symbiote.webcrawler as webcrawler
import symbiote.utils as utils
import symbiote.core as core
from symbiote.themes import ThemeManager

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

start = time.time() 

command_list = {
        "help::": "This help output.",
        "convo::": "Load, create conversation.",
        "role::": "Load built in system roles.",
        "clear::": "Clear the screen.",
        "flush::": "Flush the current conversation from memory.",
        "tokens::": "Token usage summary.",
        "save::": "Save  self.symbiote_settingssetting:: changes.",
        "exit::": "Exit symbiote.",
        "setting::": "View, update symbiote settings.",
        "maxtoken::": "Change maxtoken setting.",
        "model::": "Change AI model.",
        "cd::": "Change working directory.",
        "pwd::": "Show current working directory.",
        "file::": "Load a file for submission.",
        "summary::": "Pull nouns, summary, and metadata for a file.",
        "extract::": "Extract data features for a given file or directory and summarize.",
        "code::": "Extract code and write files.",
        "get::": "Load a webpage for submission.",
        "crawl::": "Crawl a website for submission.",
        "tree::": "Load a directory tree for submission.",
        "shell::": "Load the symbiote bash shell.",
        "clipboard::": "Load clipboard contents into symbiote.",
        "ls::": "Load ls output for submission.",
        "search::": "Search index for specific data.",
        "history::": "Show discussion history.",
        "learn::": "Train AI model on given data in directory. *",
        "structure::": "Define a data scructure. *",
        "exec::": "Execute a command.",
        "render::": "Render an image from the provided text.",
        "replay::": "Replay the current conversation to the current model.",
        "prompter::": "Create prompts matched to datasets.",
        "reinforce::": "Reinforce the chat log.",
        "purge::": "Purge the last response given. eg. thumbs down",
        "note::": "Create a note that is tracked in a separate conversation",
        "whisper::": "Process audio file to text using whipser.",
        "theme::": "Change the theme for the symbiote cli.",
        "order::": "Issue an order",
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
        'whisper': [r'keyword whisper', 'whisper::'],
        'crawl': [r'keyword crawl website', 'crawl::'],
        'clipboard_url': [r'keyword get clipboard [url|\S+site]', 'clipboard:get:'],
        'clipboard': [r'keyword get clipboard', 'clipboard::'],
        'exit': [r'keyword exit now', 'exit::'],
        'help': [r'keyword (get|show) help', 'help::'],
        'tokens': [r'keyword (get|show) tokens', 'tokens::'],
        'extract': [r'keyword extract data', 'extract::'],
        'summary': [r'keyword summarize data', 'summary::'],
        'search': [r'keyword search query', 'search::'],
        'keyword': [r'keyword (get|show) keyword', 'keywords::'],
        'history': [r'keyword (get|show) history', 'history::'],
        'perifious': [r'(i cast|icast) periph', 'perifious::']
    }

prompt_colors = {
        'matrix_green': '#00FF41',
        'soft_green': '#06AC6C',
        'salmon_red': '#f95393',
        'dark_gray': '#2C2827',
        'light_blue': '#02788E',
        'burnt_yellow': '#E67000',
        'off_white': '#e5e5e5',
        'rich_yellow': '#DED300',
        'light_gray': '#9A9A9A',
        'gray': '#6e757c',
        'white': '#FFFFFF',
        'black': '#000000'
    }

# Configure prompt settings.
'''
prompt_style = Style.from_dict({
        '': prompt_colors['rich_yellow'], # typed text color
        'prompt': prompt_colors['light_blue'], # prompt color
        'bottom-toolbar': f'bg:{prompt_colors["white"]} {prompt_colors["gray"]}', # Bottom toolbar style
        'bottom-toolbar.off': f'bg:{prompt_colors["off_white"]} {prompt_colors["light_gray"]}',  # Bottom toolbar off style
    })
'''

pricing = {
       "gpt-4": { "prompt": .03, "completion": .06 },
       "gpt-4-32k": { "prompt": .06, "completion": .12},
       "gpt-4-0314": { "prompt": .06, "completion": .12},
       "gpt-4-0613": { "prompt": .06, "completion": .12},
       "gpt-3.5-turbo": { "prompt": .002, "completion": .002},
       "gpt-3.5-turbo-16k": { "prompt": .003, "completion": .004},
       "dummy": { "prompt": 0, "completion": 0},
       "someone": { "prompt": 0, "completion": 0}
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
        "role": "DEFAULT",
        "image_dir": os.path.join(homedir, ".symbiote") + "/images",
        "notes": os.path.join(homedir, ".symbiote") + "/notes.jsonl",
        "syntax_highlight": False,
        "theme": 'default',
    }

keybindings = {}

# Create a pretty printer
pp = pprint.PrettyPrinter(indent=4)

class symchat():
    ''' Chat class '''
    def __init__(self, *args, **kwargs):
        # Autoflush output buffer
        sys.stdout = io.TextIOWrapper(
                open(sys.stdout.fileno(), 'wb', 0),
                write_through=True
            )

        self.orig_stdout = sys.stdout

        self.symbiote_settings = symbiote_settings 
        self.audio_triggers = audio_triggers
        self.flush = False
        self.logging = True
        self.timeout = 30

        if 'debug' in kwargs:
            self.symbiote_settings['debug'] = kwargs['debug']
            
        if 'working_directory' in kwargs:
            self.working_directory = kwargs['working_directory']
        else:
            self.working_directory = os.getcwd()

        self.exit = False

        if 'output' in kwargs:
            self.output = kwargs['output']
        else:
            self.output = True
       
        # Set symbiote home path parameters
        home_dir = os.path.expanduser("~")
        symbiote_dir = self.symbiote_settings['symbiote_path']
        if not os.path.exists(symbiote_dir):
            os.mkdir(symbiote_dir)

        # Set image save path for AI renderings
        if not os.path.exists(self.symbiote_settings['image_dir']):
            os.mkdir(self.symbiote_settings['image_dir'])

        # Set symbiote conf file
        self.config_file = os.path.join(symbiote_dir, "config")
        if not os.path.exists(self.config_file):
            self.save_settings(settings=self.symbiote_settings)
        else:
            self.symbiote_settings = self.load_settings()

        if 'stream' in kwargs:
            self.symbiote_settings['stream'] = kwargs['stream']

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
        if self.symbiote_settings['conversation'] == '/dev/null':
            self.conversations_file = self.symbiote_settings['conversation']
            self.convo_file = self.conversations_file
        else:
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

        # Init the shell theme manager
        self.theme_manager = ThemeManager()
        self.prompt_style = self.theme_manager.get_theme(self.symbiote_settings['theme'])

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

    def set_stdout(self, state):
        if state is False:
            sys.stdout = open(os.devnull, 'w')
        elif state is True:
            sys.stdout = self.orig_stdout 
        else:
            print("Invalid state. Use 0 to suppress stdout and 1 to restore stdout.")

    def cktime(self):
        stop = time.time()
        diff = stop - start
        print(start, stop, diff)

    def keyboardContinue(self):
        keyboard = Controller()

        keyboard.press(Key.esc)
        keyboard.press(Key.enter)

        # Small delay for certain applications that might need it
        time.sleep(0.1)

        keyboard.release(Key.esc)
        keyboard.release(Key.enter)

    def symhelp(self):
        self.suppress = True
        self.exit = True
        help_output = "Symbiote Help Menu\n------------------\nAvailable keywords:\n"
        # Sort the command list by keys
        sorted_commands = sorted(command_list.items())

        # Set column width for the command column
        cmd_col_width = max(len(cmd) for cmd in self.command_list.keys()) + 2

        # Print the table with aligned columns
        for cmd, desc in sorted_commands:
            #print("\t{:<{width}}{}".format(cmd, desc, width=cmd_col_width))
            help_output += "\t{:<{width}}{}\n".format(cmd, desc, width=cmd_col_width)

        print(help_output)
        return help_output

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

            conversation_files.insert(0, Choice("null", name="Do not record conversations."))
            conversation_files.insert(0, Choice("notes", name="Open notes conversation."))
            conversation_files.insert(0, Choice("clear", name="Clear conversation."))
            conversation_files.insert(0, Choice("export", name="Export conversation."))
            conversation_files.insert(0, Choice("new", name="Create new conversation."))

            selected_file = inquirer.select(
                message="Select a conversation:",
                choices=conversation_files,
                mandatory=False
            ).execute()

        if selected_file == None:
            return

        if selected_file == "new":
            selected_file = inquirer.text(message="File name:").execute()
        elif selected_file == "notes":
            selected_file = self.symbiote_settings['notes']
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
        elif selected_file == "export":
            export_file = inquirer.select(
                message="Select a conversation:",
                choices=conversation_files,
                mandatory=False
            ).execute()

            file_name = os.path.join(self.conversations_dir, export_file)
            self.sym.export_conversation(file_name)

            return
        
        if selected_file == "null": 
            self.conversations_file = '/dev/null'
            self.symbiote_settings['conversation'] = self.conversations_file
            self.current_conversation = []
            self.convo_file = self.conversations_file
        else:
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

    def process_input(self, *args, **kwargs):
        if 'user_input' in kwargs:
            user_input = kwargs['user_input']
            query = user_input
        else:
            return None

        if 'working_directory' in kwargs:
            working_directory = kwargs['working_directory']
            os.chdir(working_directory)
        else:
            working_directory = os.getcwd()


        self.set_stdout(False)
        user_input = self.process_commands(user_input)
        self.save_settings(settings=self.symbiote_settings)
        self.set_stdout(True)

        if self.exit:
            self.exit = False
            return None, None, None, None, None, None, query, user_input

        returned = self.send_message(user_input)

        return returned

    def chat(self, *args, **kwargs):
        # Begin symchat loop
        #history = InMemoryHistory() 
        if 'run' in kwargs:
            self.run = kwargs['run']
        else:
            self.run = False

        if 'prompt_only' in kwargs:
            self.prompt_only = kwargs['prompt_only']
        else:
            self.prompt_only = False

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
       
        self.chat_session = PromptSession(key_bindings=bindings, vi_mode=self.symbiote_settings['vi_mode'], history=self.history, style=self.prompt_style)

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

            if self.prompt_only:
                self.chat_session.bottom_toolbar = None
            else:
                self.chat_session.bottom_toolbar = f"Model: {self.symbiote_settings['model']}\nCurrent Conversation: {self.convo_file}\nLast Char Count: {self.token_track['last_char_count']}\nToken Usage:\nUser: {self.token_track['user_tokens']} Assistant: {self.token_track['completion_tokens']} Conversation: {self.token_track['truncated_tokens']} Total Used: {self.token_track['rolling_tokens']}\nCost: ${self.token_track['cost']:.2f}\ncwd: {current_path}"

            if self.run is False:
                self.user_input = self.chat_session.prompt(message="symchat> ",
                                                   multiline=True,
                                                   default=self.user_input,
                                                   vi_mode=self.symbiote_settings['vi_mode']
                                                )

            self.user_input = self.process_commands(self.user_input)


            if check_settings != self.settings_hash:
                self.save_settings(settings=self.symbiote_settings)
                self.settings_hash = check_settings

            if self.exit:
                self.exit = False
                self.user_input = ""
                continue

            if self.user_input is None or re.search(r'^\n+$', self.user_input) or self.user_input== "":
                if self.run is True and self.enable is False:
                    return None 
                    break
                self.user_input = ""

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

    def send_message(self, user_input):
        #if self.suppress and not self.run:
        #    self.launch_animation(True)
        #self.current_conversation = self.sym.load_conversation(self.conversations_file)

        if self.symbiote_settings['debug']:
            pp.pprint(self.current_conversation)

        returned = self.sym.send_request(user_input, self.current_conversation, completion=self.symbiote_settings['completion'], suppress=self.suppress, role=self.role, flush=self.flush, logging=self.logging, timeout=self.timeout, output=self.output)

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
            prompt_cost = (self.token_track['user_tokens'] / 1000 * pricing[self.symbiote_settings['model']]['prompt'])
            completion_cost = (self.token_track['completion_tokens'] / 1000 * pricing[self.symbiote_settings['model']]['completion'])
            self.token_track['cost'] += (prompt_cost + completion_cost) 
        else:
            prompt_cost = 0
            completion_cost = 0
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
        self.suppress = True
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
            print("disabled needs work")
            #shell.symBash().launch_shell()
            return None

        if re.search(r'^help::', user_input):
            output = self.symhelp()
            return output 

        if re.search(r"^clear::|^reset::", user_input):
            os.system('reset')
            return None

        if re.search(r"^tokens::", user_input):
            output = self.symtokens()
            return output

        if re.search(r"^save::", user_input):
            self.save_settings(settings=self.symbiote_settings)
            return None

        if re.search(r'^exit::', user_input):
            self.save_settings(settings=self.symbiote_settings)
            os.system('reset')
            sys.exit(0)

        # Trigger prompter:: on a directory of files to have prompts created that explain the file
        prompter_pattern = r'prompter::|prompter:(.*):'
        match = re.search(prompter_pattern, user_input)
        if match:
            self.exit = True
            if match.group(1):
                file_path = match.group(1)

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

            prompts = {}

            return prompts 

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
                        crawler = webcrawler.WebCrawler(browser='firefox')
                        pages = crawler.pull_website_content(url, search_term=None, crawl=False, depth=None)
                        for md5, page in pages.items():
                            website_content += page['content']
                        user_input = user_input[:match.start()] + website_content + user_input[match.end():]
            else:
                user_input = user_input[:match.start()] + contents + user_input[match.end():]

            return user_input

        # Trigger to choose role
        role_pattern = r'^role::|role:(.*):'
        match = re.search(role_pattern, user_input)
        if match:
            self.suppress = True
            import symbiote.roles as roles
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
        system_pattern = r'^system:(.*):'
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
            self.suppress = True
            self.exit = True
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

            return self.symbiote_settings 

        # Trigger for changing max_tokens. 
        maxtoken_pattern = r'^maxtoken::|maxtoken:(.*):'
        match = re.search(maxtoken_pattern, user_input)
        if match:
            self.suppress = True
            self.exit = True
            if match.group(1):
                setmaxtoken = int(match.group(1))
                self.sym.change_max_tokens(setmaxtoken, update=True)
            else:
                print("Maxtoken menu needed.")
                return None

            return setmaxtoken

        # Trigger for changing gpt model 
        model_pattern = r'^model::|model:(.*):'
        match = re.search(model_pattern, user_input)
        if match:
            self.suppress = True
            self.exit = True
            if match.group(1):
                model_name = match.group(1).strip()
                self.symmodel(model_name)
            else:
                self.symmodel()

            return self.symbiote_settings['model'] 

        # Trigger for changing the conversation file
        convo_pattern = r'^convo::|convo:(.*):'
        match = re.search(convo_pattern, user_input)
        if match:
            self.suppress = True
            self.exit = True
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
            self.suppress = True
            self.exit = True
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

            return requested_directory 

        # Trigger to list verbal keywords prompts.
        keywords_pattern = r'^keywords::'
        match = re.search(keywords_pattern, user_input)
        if match:
            self.suppress = True
            self.exit = True
            for keyword in self.audio_triggers:
                if keyword == 'perifious':
                    continue
                print(f'trigger: {self.audio_triggers[keyword][0]}')

            return self.audio_triggers 

        # Trigger to get current working directory
        pwd_pattern = r'^pwd::'
        match = re.search(pwd_pattern, user_input)
        if match:
            self.suppress = True
            self.exit = True
            print(self.working_directory)
            return self.working_directory 

        # Trigger for extract:: processing. Load file content and generate a json object about the file.
        summary_pattern = r'extract::|extract:(.*):(.*):|extract:(.*):'
        match = re.search(summary_pattern, user_input)
        file_path = None
        
        if match:
            self.suppress = True
            self.exit = True

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
                        message="Extract file features:",
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
                index = inquirer.confirm(message=f'Index {file_path}?').execute()

                if index is True:
                    result = self.symutils.createIndex(file_path, reindex=False)

                return result
            elif not os.path.isfile(file_path):
                print(f"File not found: {file_path}")
                return None

            result = self.symutils.createIndex(file_path, reindex=False)

            #summary = self.symutils.summarizeFile(file_path)

            #if self.symbiote_settings['debug']:
            #    print(json.dumps(summary, indent=4))

            #user_input = user_input[:match.start()] + json.dumps(summary) + user_input[match.end():]

            return None 

        # Trigger to flush current running conversation from memory.
        flush_pattern = r'^flush::'
        match = re.search(flush_pattern, user_input)
        if match:
            self.suppress = True
            self.exit = True
            self.current_conversation = []

            return None 

        # Trigger for search:: to search es index
        search_pattern = r'^search::|^search:(.*):'
        match = re.search(search_pattern, user_input)
        if match:
            self.suppress = True
            self.exit = True
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
        if self.symbiote_settings['conversation'] == '/dev/null':
            return

        if match:
            self.suppress = True
            self.exit = True
            if match.group(1):
                history_length = int(match.group(1))
                print(history_length)
                time.sleep(4)
            else:
                history_length = False 

            history = self.sym.export_conversation(self.symbiote_settings['conversation'], history=True, lines=history_length)

            return history

        # Trigger for rendering images from text input
        render_pattern = r'^render:(.*):'
        match = re.search(render_pattern, user_input)
        if match:
            self.suppress = True
            self.exit = True
            if match.group(1):
                query = match.group(1)
                result = self.sym.process_openaiImage(query)
                if result is not None:
                    command = f"open {self.symbiote_settings['image_dir']}"
                    self.symutils.exec_command(command)

            return result

        # Trigger for code:: extraction from provided text
        ''' Add options for running, extracting and editing code on the fly '''
        code_pattern = r'code::|code:(.*):'
        match = re.search(code_pattern, user_input)
        if match:
            codeRun = False
            self.suppress = True
            codeidentify = codeextract.CodeBlockIdentifier(last_message['content'])
            if match.group(1):
                text = match.group(1)
                if re.search(r'^https?://\S+', text):
                    print(f"Fetching content from: {url}")
                    website_content = self.symutils.pull_website_content(url, browser="firefox")
                    codeidentify = codeextract.CodeBlockIdentifier(website_content)
                elif text == 'run':
                    codeRun = True
                else:
                    # process any text placed in code:<text>: for extraction
                    codeidentify = codeextract.CodeBlockIdentifier(text)
            else:
                # process the last conversation message for code to extract
                last_message = self.current_conversation[-1]
                codeidentify = codeextract.CodeBlockIdentifier(last_message['content'])

            files = codeidentify.process_text()
            for file in files:
                print(file)

            if codeRun:
                pass

            return files

        # Trigger for purge:: removing the last message received
        purge_pattern = r'purge::|purge:(.*):'
        match = re.search(purge_pattern, user_input)
        if match:
            self.suppress = True
            if match.group(1):
                last_messages = match.group(1)
            else:
                last_message = 1

            prompt = "IMPORTANT: The response provided was not correct."
            user_input = prompt + user_input

            return user_input

        # Trigger for note:: taking.  Take the note provided and query the current model but place the note and results
        # in a special file for future tracking.
        note_pattern = r'^note::|^note:(.*):'
        match = re.search(note_pattern, user_input)
        if match:
            self.suppress = True
            self.exit = True
            if match.group(1):
                user_input = match.group(1)
            else:
                pass

            self.sym.save_conversation(user_input, self.symbiote_settings['notes'])

            return None

        # Trigger menu for cli theme change
        theme_pattern = r'theme::|theme:(.*):'
        match = re.search(theme_pattern, user_input)
        if match:
            self.suppress = True
            self.exit = True
            if match.group(1):
                theme_name = match.group(1)
                prompt_style = self.theme_manager.get_theme(theme_name)
            else:
                theme_name, prompt_style = self.theme_manager.select_theme() 

            self.chat_session.style = prompt_style
            self.symbiote_settings['theme'] = theme_name
            self.sym.update_symbiote_settings(settings=self.symbiote_settings)
            self.save_settings(settings=self.symbiote_settings)

            return theme_name


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

        # Trigger system execution of a command
        exec_pattern = r'exec:(.*):'
        match = re.search(exec_pattern, user_input)
        if match:
            self.suppress = True
            self.exit = True
            if match.group(1):
                command = match.group(1)
                result = self.symutils.exec_command(command)
                if result:
                    print(result)
            else:
                print(f"No command specified")

            return result

        # Trigger to replay prior log data.
        replay_pattern = r'replay::|replay:(.*):'
        match = re.search(replay_pattern, user_input)
        if match:
            self.logging = False
            old_timeout = self.timeout
            self.timeout = 1
            user_content = ''
            for message in self.current_conversation:
                if message['role'] == 'user':
                    user_content = message['content']
                elif message['role'] == 'assistant' or message['role'] == 'system':
                    returned_content = message['content']
                    trole = message['role']
                    if user_content:
                        input_data = f'role: user\n\n{user_content}\n\nrole: {trole}\n\n{returned_content}\n'
                        print(input_data)
                        print("--------")
                        response = self.send_message(input_data)
                    else:
                        continue

            self.logging = True
            self.timeout = old_timeout

            return None

        # Trigger for whisper:audiofile: processing.  Load audio file and convert to text using whipser.
        whisper_pattern = r'whisper::|whisper:(.*):'
        match = re.search(whisper_pattern, user_input)
        if match:
            self.suppress = True
            if match.group(1):
                file_path = match.group(1)
            elif file_path is None:
                start_path = "./"
                file_path = inquirer.filepath(
                        message="Transcribe audio file:",
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

            if os.path.isfile(file_path):
                root, ext = os.path.splitext(file_path)

                if ext != ".mp3":
                    print(f"Filetype must be .mp3")
                    return None

                content = self.sym.process_openaiTranscribe(file_path)
                print(f"Audio Transcription:\n{content}\n")

                audio_content = f"File name: {absolute_path}\n"
                audio_content += '\n```\n{}\n```\n'.format(content)
                user_input = user_input[:match.start()] + audio_content + user_input[match.end():]
            else:
                print(f"Error: {file_path} is not a file.")
                return None

            return user_input


        # Trigger for get:URL processing. Load website content into user_input for model consumption.
        get_pattern = r'get::|get:(https?://\S+):'
        match = re.search(get_pattern, user_input)
        if match:
            crawl = False
            self.suppress = True
            website_content = ''
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

            print(f"Fetching web page content from: {url}")

            crawler = webcrawler.WebCrawler(browser='firefox')
            pages = crawler.pull_website_content(url, search_term=None, crawl=crawl, depth=None)
            for md5, page in pages.items():
                website_content += page['content']
            user_input = user_input[:match.start()] + website_content + user_input[match.end():]
            return user_input 

        # Trigger for crawl:URL processing. Load website content into user_input for model consumption.
        get_pattern = r'crawl::|crawl:(https?://\S+):'
        match = re.search(get_pattern, user_input)
        if match:
            crawl = True
            self.suppress = True
            website_content = ''
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

            print(f"Crawling content from: {url}")

            crawler = webcrawler.WebCrawler(browser='firefox')
            pages = crawler.pull_website_content(url, search_term=None, crawl=crawl, depth=None)
            for md5, page in pages.items():
                website_content += page['content']
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
                print(user_input)
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

