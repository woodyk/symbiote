#!/usr/bin/env python3
#
# chat.py

from rich import inspect
from rich.tree import Tree
from rich.console import Console
from rich.columns import Columns 
from rich.markdown import Markdown
from rich.panel import Panel
from rich.console import Group
from rich.markup import escape
from rich.padding import Padding
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.rule import Rule
from rich.theme import Theme
from rich.highlighter import Highlighter, RegexHighlighter
console = Console()
print = console.print
log = console.log

import time
import sys
import os
import io
import re
import importlib
import threading
import clipboard
import json
import base64
import requests
import qrcode
import subprocess
import tempfile
import platform

log("Loading pgeocode.")
import pgeocode
nomi = pgeocode.Nominatim('us')

from datetime import datetime
from pathlib import Path
from halo import Halo
from PIL import Image, ImageDraw, ImageColor
from urllib.parse import urlparse
from io import BytesIO
from bs4 import BeautifulSoup

log("Loading inquirerpy.")
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import PathValidator
from InquirerPy.prompts.filepath import FilePathCompleter

log("Loading prompt_toolkit.")
from prompt_toolkit import Application
from prompt_toolkit.document import Document
from prompt_toolkit.history import InMemoryHistory, FileHistory
from prompt_toolkit.shortcuts import PromptSession, print_container, prompt, input_dialog, yes_no_dialog, progress_dialog, message_dialog
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.completion import Completion, WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit.widgets import Label, SearchToolbar, Dialog, TextArea, Frame, Box, Button
from prompt_toolkit.layout.containers import Window, VSplit, Float, FloatContainer
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.cursor_shapes import CursorShape, ModalCursorShapeConfig

# Add these imports at the beginning of the file
#from symbiote.model_creator import create_model, train_model, evaluate_model

log("Loading symbiote roles.")
import symbiote.roles as roles
#log("Loading symbiote shell.")
#import symbiote.shell as shell
log("Loading symbiote speech.")
from symbiote.speech import SymSpeech
log("Loading symbiote utils.")
from symbiote.utils import Utilities
log("Loading symbiote themes.")
from symbiote.themes import ThemeManager
log("Loading symbiote MemoryStore.")
from symbiote.memory import MemoryStore

system = platform.system()

models = [
        "groq:llama-3.1-70b-versatile",
        "groq:mixtral-8x7b-32768",
        ] 

log("Loading ollama.")
from ollama import Client
olclient = Client(host='http://localhost:11434')
try:
    response = olclient.list()
    for model in response['models']:
        models.append("ollama:" + model['name'])
except Exception as e:
    pass

log("Loading openai.")
import openai
oaiclient = openai.OpenAI()
try:
    response = oaiclient.models.list()
    for model in response:
        models.append("openai:" + model.id)
except Exception as e:
    log(e)
    pass

log("Loading groq.")
from groq import Groq
try:
    grclient = Groq()
except Exception as e:
    log(e)

command_list = {
        "help::": "This help output.",
        "convo::": "Load, create conversation.",
        "roles::": "Load built in system roles.",
        "clear::": "Clear the screen.",
        "flush::": "Flush the current conversation from memory.",
        "save::": "Save self.settings and backup the ANNGL",
        "exit::": "Exit symbiote the symbiote CLI",
        "settings::": "View, change, or add settings for symbiote.",
        "model::": "Change the AI model being used.",
        "cd::": "Change working directory.",
        "file::": "Load a file for submission.",
        "memory::": "CRUD access to symbiote memory",
        "search::": "Search symbiote memory for information",
        "reload::": "Reload running python modules.",
        "weather::": "Display the current weater.",
        "inspect::": "Realtime python object inspector for current running session.",
        "webvuln::": "Run and summarize a web vulnerability scan on a given URL.",
        "deception::": "Run deception analysis on the given text",
        "geo::": "Check the geo location of an IP or a domains IP.",
        "fake_news::": "Run fake news analysis on the given text",
        "yt_transcript::": "Download the transcripts from youtube url for processing.",
        "image_extract::": "Extract images from a given URL and display them.",
        "analyze_image::": "Analyze an image or images from a website or file.",
        "w3m::|browser::": "Open a URL in w3m terminal web browser.",
        "qr::": "Generate a QR code from the given text.",
        "extract::": "Extract data features for a given file or directory and summarize.",
        "code::": "Extract code and write files.",
        "get::": "Get remote data based on uri http, ftp, ssh, etc...",
        "getip::": "Get your IP address information.",
        "crawl::": "Crawl remote data based on uri http, ftp, ssh, etc...",
        "shell::": "Work in shell mode and execute commands.",
        "clipboard::": "Load clipboard contents into symbiote.",
        "history::": "Show discussion history.",
        "$": "Execute a local cli command and learn from the execution fo the command.",
        "image::": "Render an image from the provided text.",
        "note::": "Create a note that is tracked in a separate conversation",
        "index::": "Index files into Elasticsearch.",
        "define::": "Request definition on keyword or terms.",
        "theme::": "Change the theme for the symbiote cli.",
        "view::": "View a file",
        "scroll::": "Scroll through the text of a given file a file",
        "google::": "Run a google search on your search term.",
        "wiki::": "Run a wikipedia search on your search term.",
        "headlines::|news::": "Get headlines from major news agencies.",
        "mail::": "Load e-mail messages from gmail.",
    }

audio_triggers = {
        'speech_off': [r'keyword speech off', 'settings:speech:0:'],
        'speech_on': [r'keyword speech on', 'settings:speech:1:'],
        'interactive': [r'keyword interactive mode', 'settings:listen:0:'],
        'settings': [r'keyword show setting', 'settings::'],
        'file': [r'keyword open file', 'file::'],
        'shell': [r'keyword (open shell|openshell)', 'shell::'],
        'role': [r'keyword change (role|roll)', 'roles::'],
        'conversation': [r'keyword change conversation', 'convo::'],
        'model': [r'keyword change model', 'model::'],
        'get': [r'keyword get website', 'get::'],
        'whisper': [r'keyword whisper', 'whisper::'],
        'crawl': [r'keyword crawl website', 'crawl::'],
        'clipboard_url': [r'keyword get clipboard [url|\S+site]', 'clipboard:get:'],
        'clipboard': [r'keyword get clipboard', 'clipboard::'],
        'exit': [r'keyword exit now', 'exit::'],
        'help': [r'keyword (get|show) help', 'help::'],
        'extract': [r'keyword extract data', 'extract::'],
        'summary': [r'keyword summarize data', 'summary::'],
        'keyword': [r'keyword (get|show) keyword', 'keywords::'],
        'history': [r'keyword (get|show) history', 'history::'],
        'perifious': [r'(i cast|icast) periph', 'perifious::'],
        'scroll': [r'keyword scroll file', 'scroll::'],
    }

# Define prompt_toolkit keybindings
global kb
kb = KeyBindings()

@kb.add('c-c')
def _(event):
    ''' Exit Application '''
    log("Control-C detected.")
    sys.exit(0) 

# Default settings for openai and symbiote module.
homedir = os.getenv('HOME')
symbiote_settings = {
        "model": "",
        "max_tokens": 512,
        "location": '',
        "stream": True,
        "user": "smallroom",
        "conversation": '',
        "vi_mode": False,
        "speech": False,
        "listen": False,
        "debug": False,
        "elasticsearch": "http://dockera.vm.sr:9200",
        "elasticsearch_index": "symbiote",
        "symbiote_path": os.path.join(homedir, ".symbiote"),
        "perifious": False,
        "role": "DEFAULT",
        "notes": os.path.join(homedir, ".symbiote") + "/notes.jsonl",
        "theme": 'default',
        "imap_username": '',
        "imap_password": '',
        "think": False,
        "markdown": True,
        "config_file": f"{homedir}/.symbiote/config"
    }

class symChat():
    def __init__(self, *args, **kwargs):
        self.config_file = symbiote_settings['config_file']
        settings = self.loadSettings()
        if settings is None:
            self.settings = symbiote_settings 
            settings = symbiote_settings

        self.settings = settings 
        self.conversation_history = []
        self.estimated_tokens = self.estimateTokenCount(json.dumps(self.conversation_history))
        self.audio_triggers = audio_triggers
        self.spinner = Halo(text='Processing ', spinner='dots')
        self.shell_mode = False
        self.command_register = []

        # initialize memory manager
        self.memory = MemoryStore()

        self.return_input = True

        if 'debug' in kwargs:
            self.settings['debug'] = kwargs['debug']
            
        if 'working_directory' in kwargs:
            self.working_directory = kwargs['working_directory']
        else:
            self.working_directory = os.getcwd()

        # Set symbiote home path parameters
        symbiote_dir = os.path.expanduser(self.settings['symbiote_path'])
        if not os.path.exists(symbiote_dir):
            os.mkdir(symbiote_dir)

        if 'stream' in kwargs:
            self.settings['stream'] = kwargs['stream']

        # Get hash for current settings
        self.default_hash = hash(json.dumps(self.settings, sort_keys=True)) 

        # Set the conversations directory
        self.conversations_dir = os.path.join(symbiote_dir, "conversations")
        if not os.path.exists(self.conversations_dir):
            os.mkdir(self.conversations_dir)

        # Set the default conversation
        if self.settings['conversation'] == '/dev/null':
            self.conversations_file = self.settings['conversation']
            self.convo_file = self.conversations_file
        else:
            self.conversations_file = os.path.join(self.conversations_dir, self.settings['conversation'])
            self.convo_file = os.path.basename(self.conversations_file)

        # Set symbiote shell history file
        history_file = os.path.join(symbiote_dir, "symbiote_shell_history")
        if not os.path.exists(history_file):
            open(history_file, 'a').close()

        self.history = FileHistory(history_file)

        # Load the default conversation
        #self.current_conversation = self.loadConversation(self.conversations_file)
        self.current_conversation = []

        # Load utils object
        self.symutils = Utilities(settings=self.settings)

        # Init the shell theme manager
        self.theme_manager = ThemeManager()
        self.prompt_style = self.theme_manager.get_theme(self.settings['theme'])

        self.command_list = command_list

        ''' Command completion for the prompt
        commands = []
        for command in self.command_list:
            commands.append(command)

        self.command_completer = WordCompleter(commands)
        '''

        # Get location details
        self.geo = nomi.query_postal_code(self.settings['location'])

        if 'suppress' in kwargs:
            self.suppress = kwargs['suppress']
        else:
            self.suppress = False

    def displaySettings(self):
        table = Table(show_header=True, expand=True, header_style="bold magenta")
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        for key, val in sorted(self.settings.items()):
            table.add_row(key, str(val))

        print(table)
        print()

    def displayHelp(self):
        table = Table(show_header=True, expand=True, header_style="bold magenta")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")

        for cmd, desc in sorted(self.command_list.items()):
            table.add_row(cmd, desc)

        print(table)
        print()

    def displayConvo(self, convo=False):
        conversations = sorted(self.getConversations(self.conversations_dir))

        if convo:
            selected_file = convo
        else:
            if not conversations:
                return
            conversations.insert(0, Choice("notes", name="Open notes conversation."))
            conversations.insert(0, Choice("clear", name="Clear conversation."))
            conversations.insert(0, Choice("export", name="Export conversation."))
            convesations.insert(0, Choice("new", name="Create new conversation."))

            selected_file = self.listSelector("Select a conversation:", conversations)

        if selected_file == None:
            return

        if selected_file == "new":
            selected_file = self.textPrompt("File name:")
        elif selected_file == "notes":
            selected_file = self.settings['notes']
        elif selected_file == "clear":
            clear_file = self.listSelector("Select a conversation:", conversations)

            clear_file = os.path.join(self.conversations_dir, clear_file)

            try:
                with open(clear_file, 'w') as file:
                    pass
            except:
                log(f"Unable to clear {clear_file}")

            if self.settings['conversation'] == os.path.basename(clear_file):
                self.current_conversation = self.sym.loadConversation(clear_file)

            log(f"Conversation cleared: {clear_file}")

            return
        elif selected_file == "export":
            export_file = self.listSelector("Select a conversation:", conversations)

            file_name = os.path.join(self.conversations_dir, export_file)
            self.sym.export_conversation(file_name)

            return
        
        if selected_file == "null": 
            self.conversations_file = '/dev/null'
            self.settings['conversation'] = self.conversations_file
            self.current_conversation = []
            self.convo_file = self.conversations_file
        else:
            self.settings['conversation'] = selected_file
            self.conversations_file = os.path.join(self.conversations_dir, selected_file)
            self.current_conversation = self.sym.loadConversation(self.conversations_file)
            self.convo_file = os.path.basename(self.conversations_file)

        log(f"Loaded conversation: {selected_file}")

        return

    def selectModel(self, *args):
        model_list = models
        print(f"Current Model: {self.settings['model']}")
        try:
            model_name = args[0]
            if model_name in model_list:
                selected_model = args[0]
            else:
                log(f"No such model: {model_name}")
                return None
        except:
            selected_model = self.listSelector("Select a model:", sorted(model_list))

        self.settings['model'] = selected_model
        self.saveSettings()

        return None

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
            user_input = kwargs['user_input']

        if 'working_directory' in kwargs:
            self.working_directory = kwargs['working_directory']
            self.previous_directory = self.working_directory
            os.chdir(self.working_directory)
      
        self.chat_session = PromptSession(key_bindings=kb, vi_mode=self.settings['vi_mode'], history=self.history, style=self.prompt_style)

        def getPrompt():
            # Bottom toolbar configuration
            if self.prompt_only:
                self.chat_session.bottom_toolbar = None
            else:
                self.chat_session.bottom_toolbar = f"Model: {self.settings['model']} | Role: {self.settings['role']}\nEstimated Tokens: {self.estimated_tokens} Shell Mode: {self.shell_mode}"

            if self.shell_mode is True:
                prompt_content = "shell mode> "
            else:
                prompt_content = f"{self.settings['role'].lower()}> "

            prompt = f"{prompt_content}"

            return prompt 

        while True:
            print()
            user_input = str()
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            current_date = now.strftime("%m/%d/%Y")

            # Chack for a change in settings and write them
            check_settings = hash(json.dumps(self.settings, sort_keys=True)) 

            self.estimated_tokens = self.estimateTokenCount(json.dumps(self.conversation_history))

            if self.settings['listen'] and self.run is False:
                if not hasattr(self, 'symspeech'):
                    self.symspeech = SymSpeech(settings=self.settings)
                    self.speechQueue = self.symspeech.start_keyword_listen()

                self.spinner.start()
                user_input = self.symspeech.keyword_listen()
                self.spinner.succeed('Completed')
                self.enable = True
                self.run = True

            # Get the current path
            current_path = os.getcwd()

            # Get the home directory
            home_dir = os.path.expanduser('~')

            # Replace the home directory with ~
            if current_path.startswith(home_dir):
                current_path = '~' + current_path[len(home_dir):]

            if self.run is False:
                user_input = self.chat_session.prompt(message=getPrompt(),
                                                   multiline=True,
                                                   default=user_input,
                                                   cursor=CursorShape.UNDERLINE,
                                                   #rprompt="right justified prompt tet",
                                                   vi_mode=self.settings['vi_mode'],
                                                   refresh_interval=0.5
                                                )

            '''
            try:
                user_input = self.processCommands(user_input)
            except Exception as e:
                log(f"Error processing commands in user_input: {e}")
                continue
            '''
            print()
            user_input = self.processCommands(user_input)

            if user_input is None or user_input == "":
                print()
                print(Rule(title=f"{current_date} {current_time}", style="gray54"))
                continue

            if check_settings != self.default_hash:
                self.saveSettings()
                self.default_hash = check_settings

            if user_input is None or re.search(r'^\n+$', user_input) or user_input == "":
                if self.run is True and self.enable is False:
                    return None 
                    break

                self.enable = False
                self.run = False
                continue

            returned = self.sendMessage(user_input)
            if returned is None:
                print(f"No response.")
            print()
            print(Rule(title=f"{current_date} {current_time}", style="gray54"))

            if self.shell_mode is True:
                if returned.startswith("`") and returned.endswith("`"):
                    returned = returned[1:-1]
                print(f"{returned}\n")
                response = self.yesNoPrompt("Execute command?")
                if response is True:
                    output = self.execCommand(returned)
                    print(f"\n{output}\n")
                    self.writeHistory('user', output)
                    continue

            print()

            if self.enable is True:
                self.run = False
                self.enable = False

            if self.run is True:
                return returned

    def writeHistory(self, role, text):
        hist_entry = {
                #"epoch": time.time(),
                "role": role,
                "content": text 
                }
        self.conversation_history.append(hist_entry)

    def think(self, user_input):
        available_roles = roles.get_roles()
        self.writeHistory('user', f"{available_roles['THINKING']}\n\nQUERY:\n{user_input}")

        num_ctx = 8092

        print('<THINKING>')
        response = str() 

        if self.settings['model'].startswith("openai"):
            model_name = self.settings['model'].split(":")
            model = model_name[1]
            # OpenAI Chat Completion
            try:
                stream = oaiclient.chat.completions.create(
                        model = model,
                        messages = self.conversation_history,
                        stream = True,
                        )
            except Exception as e:
                log(e)
                return response

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    print(chunk.choices[0].delta.content, end="", flush=True)
                    response += chunk.choices[0].delta.content

        elif self.settings['model'].startswith("ollama"):
            # Ollama Chat Completion
            model_name = self.settings['model'].split(":")

            model = model_name[1] + ":" + model_name[2]

            stream = olclient.chat(
                    model = model,
                    messages = self.conversation_history,
                    stream = True,
                    #format = "json",
                    options = { "num_ctx": num_ctx },
                    )

            for chunk in stream:
                print(chunk['message']['content'], end='', flush=True)
                response += chunk['message']['content']

        elif self.settings['model'].startswith("groq"):
            model_name = self.settings['model'].split(":")
            model = model_name[1]

            stream = grclient.chat.completions.create(
                    model = model,
                    messages = self.conversation_history,
                    stream = True,
                    )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    print(chunk.choices[0].delta.content, end='', flush=True)
                    response += chunk.choices[0].delta.content

        self.writeHistory('assistant', response)

        print()
        print('</THINKING>')
        self.suppress = False
        return response

    def sendMessage(self, user_input):
        assistant_prompt = "symbiote> "
        if self.settings['think'] is True:
            self.think(user_input)

        current_role = self.settings['role']
        available_roles = roles.get_roles()

        self.geo = nomi.query_postal_code(self.settings['location'])
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_date = now.strftime("%m/%d/%Y")

        suffix = f"time:{current_time},"
        suffix += f"date:{current_date},"
        suffix += f"operating system:{system},"
        for key, val in self.geo.items():
            if key == "accuracy":
                continue

            suffix += f"{key}: {val},"

        system_prompt = f"{available_roles[current_role]}\n{suffix.strip()}"
        self.writeHistory('system', system_prompt)
        self.writeHistory('user', user_input)

        '''
        self.estimated_tokens = self.estimateTokenCount(json.dumps(self.conversation_history))
        num_ctx = self.estimated_tokens + 8192
        if self.estimated_tokens > self.settings['max_tokens']:
            self.conversation_history = self.truncateHistory(self.conversation_history, self.settings['max_tokens'])
            self.estimated_tokens = self.estimateTokenCount(json.dumps(self.conversation_history))
            num_ctx = self.estimated_tokens + 8192
        '''
        num_ctx = self.settings['max_tokens']

        message = self.conversation_history

        if self.shell_mode is True:
            message = []
            current_role = "SHELL"
            self.suppress = True
            message.append({"role": "system", "content": available_roles[current_role]})
            message.append({"role": "user", "content": user_input})

        response = str() 
        streaming = self.settings['stream']
        markdown = self.settings['markdown']
        if self.shell_mode is True:
            streaming = False
            markdown = False

        if len(message) == 0:
            log(f"The user input is empty.  Possibly your input was too large.")
            return None

        if markdown is True and streaming is True:
           live = Live(console=console, refresh_per_second=5)
           live.start()

        if self.settings['model'].startswith("openai"):
            model_name = self.settings['model'].split(":")
            model = model_name[1]
            
            # Remove system messages from the history if using o1 models
            # o1 models do not allow role type of system
            # also streaming must be turned off
            if model.startswith("o1-"):
                streaming = False
                for message in self.conversation_history:
                    if message['role'] == 'system':
                        self.conversation_history.remove(message)

            # OpenAI Chat Completion
            try:
                stream = oaiclient.chat.completions.create(
                        model = model,
                        messages = message,
                        stream = streaming,
                        )
            except Exception as e:
                log(e)
                return None

            if self.suppress is True:
                response = stream.choices[0].message.content
            else:
                if streaming:
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            response += chunk.choices[0].delta.content
                            if markdown is True:
                                live.update(Markdown(response))
                            else:
                                log(chunk.choices[0].delta.content, end='', flush=True)
                else:
                    response = stream.choices[0].message.content
                    if markdown is True:
                        print(Markdown(response))
                    else:
                        print(response)

        elif self.settings['model'].startswith("ollama"):
            # Ollama Chat Completion
            model_name = self.settings['model'].split(":")
            model = model_name[1] + ":" + model_name[2]

            try:
                stream = olclient.chat(
                        model = model,
                        messages = message,
                        stream = streaming,
                        #format = "json",
                        options = { "num_ctx": num_ctx },
                        )
            except Exception as e:
                log(e)
                return None
            
            if self.suppress is True:
                response = stream['message']['content']
            else:
                if streaming:
                    for chunk in stream:
                        response += chunk['message']['content']
                        if markdown is True:
                            live.update(Markdown(response))
                        else:
                            print(chunk['message']['content'], end='', flush=True)
                else:
                    response = stream['message']['content']
                    if markdown is True:
                        print(Markdown(response))
                    else:
                        print(response)

        elif self.settings['model'].startswith("groq"):
            model_name = self.settings['model'].split(":")
            model = model_name[1]

            try:
                stream = grclient.chat.completions.create(
                        model = model,
                        messages = message,
                        stream = stream,
                        )
            except Exception as e:
                log(e)
                return None

            if self.suppress is True:
                response = stream.choices[0].message.content
            else:
                if streaming:
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            response += chunk.choices[0].delta.content
                            if markdown is True:
                                live.update(Markdown(response))
                            else:
                                print(chunk.choices[0].delta.content, end='', flush=True)
                else:
                    response = stream.choices[0].message.content
                    if markdown is True:
                        print(Markdown(response))
                    else:
                        print(response)
        try:
            if live.is_started:
                live.stop()
        except:
            pass

        self.writeHistory('assistant', response)

        if self.settings['speech'] and self.suppress is False:
            self.symspeech = SymSpeech()
            speech_thread = threading.Thread(target=self.symspeech.say, args=(response,))
            speech_thread.start()

        self.suppress = False

        return response

    def truncateHistory(self, history, size):
        tokens = self.estimateTokenCount(json.dumps(history))
        while tokens > size:
            history.pop(0)
            tokens = self.estimateTokenCount(json.dumps(history))

        return history

    def processCommands(self, user_input):
        def _checkCommand(user_input):
            command_pattern = r"(^|\b| )(?P<command_name>\w+):(?P<content>.*?):($|\b| )"

            # Lists to store the results
            commands = []
            surrounding_texts = []
            last_end = 0

            # Find all command matches
            for match in re.finditer(command_pattern, user_input):
                # Extract command name and content
                command_name = match.group("command_name")
                if match.group("content"):
                    content = match.group("content")
                else:
                    content = None

                # Append command info
                commands.append({
                    "command_name": command_name,
                    "content": content,
                    "start": match.start(),
                    "end": match.end()
                })

                # Capture surrounding text before each command
                start, end = match.span()
                if start > last_end:
                    surrounding_texts.append(user_input[last_end:start].strip())

                last_end = end

            # Append any remaining text after the last command
            if last_end < len(user_input):
                surrounding_texts.append(user_input[last_end:].strip())

            # If there is no surrounding text, return None
            if not any(surrounding_texts):
                return False
            else:
                return True
            '''
            # Process each command and replace it in the user_input
            offset = 0  # Track character offset for replacement
            for command in commands:
                command_name = command["command_name"]
                content = command["content"]

                # Attempt to call the function dynamically
                try:
                    func = command_functions.get(f"command_{command_name}")
                    if callable(func):
                        log(f"Calling function: {command_name} with content: {content}")
                        replacement_content = func(content)
                        replacement = f"\n```\n{replacement_content}\n```\n"

                        start = command["start"] + offset
                        end = command["end"] + offset
                        user_input = user_input[:start] + replacement + user_input[end:]

                        offset += len(replacement) - (end - start)
                    else:
                        log(f"No function found for command: {command_name}")
                except Exception as e:
                    log(f"Error calling function {command_name}: {e}")

            return user_input
            '''

        self.return_input = _checkCommand(user_input)

        # Audio keyword triggers
        for keyword in self.audio_triggers:
            if re.search(self.audio_triggers[keyword][0], user_input):
                user_input = self.audio_triggers[keyword][1]
                break

        self.registerCommand("test::")
        if user_input.startswith('test::'):
            print(Panel(Text("hello world", justify="center"), title="test"))
            print()
            print("[red]hello world[/red]")
            return None

        self.registerCommand("perifious::")
        if re.search(r'^perifious::', user_input):
            self.symspeech = speech.SymSpeech(debug=self.settings['debug'])
            self.symspeech.say('Your wish is my command!')
            if self.settings['perifious']:
                user_input = 'settings:perifious:0:'
            else:
                user_input = 'settings:perifious:1:'

        self.registerCommand("shell::")
        if re.search(r'^shell::', user_input):
            if self.shell_mode is False:
                self.shell_mode = True
                self.chat_session.style = self.theme_manager.get_theme("liveshell")
            else:
                self.shell_mode = False
                self.chat_session.style = self.theme_manager.get_theme(self.settings["theme"])

            log(f"Shell mode set: {self.shell_mode}")

            # needs to be fixed
            #shell.symBash().launch_shell()
            return None

        self.registerCommand("help::")
        if re.search(r'^help::', user_input):
            self.displayHelp()
            return None 

        self.registerCommand("clear::")
        self.registerCommand("reset::")
        if re.search(r"^clear::|^reset::", user_input):
            os.system('reset')
            return None

        self.registerCommand("save::")
        if re.search(r"^save::", user_input):
            self.saveSettings()
            return None

        self.registerCommand("exit::")
        if re.search(r'^exit::', user_input):
            self.saveSettings()
            os.system('reset')
            sys.exit(0)

        # Trigger to read clipboard contents
        self.registerCommand("clipboard::")
        clipboard_pattern = r'clipboard::|clipboard:(.*):'
        match = re.search(clipboard_pattern, user_input)
        if match:
            import symbiote.WebCrawler as webcrawler
            contents = clipboard.paste()
            if match.group(1):
                sub_command = match.group(1).strip()
                if sub_command == 'get':
                    if re.search(r'^https?://\S+', contents):
                        log(f"Fetching content from: {contents}")
                        crawler = webcrawler.WebCrawler(browser='firefox')
                        pages = crawler.pull_website_content(url, search_term=None, crawl=False, depth=None)
                        crawler.close()
                        website_content = str()
                        if pages:
                            for md5, page in pages.items():
                                website_content += page['content']
                        else:
                            log(f"Unable to fetch data for {url}")

                        user_input = user_input[:match.start()] + website_content + user_input[match.end():]
            else:
                user_input = user_input[:match.start()] + contents + user_input[match.end():]

            return user_input

        # Trigger to reload modules
        self.registerCommand("reload::")
        reload_pattern = r"reload::|reload:(.*):"
        match = re.search(reload_pattern, user_input)
        if match:
            if match.group(1):
                module = match.group(1)
                if module in list(sys.modules.keys()):
                    name = syss.modules.get(module)
                    log(f"Reloading {module}")
                    importlib.reload(module)
                else:
                    log(f"No such module: {module}")
            else:
                for module_name in list(sys.modules.keys()):
                    if module_name.startswith("symbiote."):
                        module = sys.modules.get(module_name)
                        log(f"Reloading {module}")
                        importlib.reload(module)

            return None

        # Trigger to choose role
        self.registerCommand("roles::")
        role_pattern = r'^roles::|roles:(.*):'
        match = re.search(role_pattern, user_input)
        if match:
            importlib.reload(roles)
            available_roles = roles.get_roles()

            if match.group(1):
                selected_role = match.group(1).strip()
                selected_role = selected_role.upper()
            else:
                if not available_roles:
                    return None

                role_list = []
                for role_name in available_roles:
                    role_list.append(role_name)

                print(f"Current Role: {self.settings['role']}")
                selected_role = self.listSelector("Select a role:", sorted(role_list))

                if selected_role is None:
                    return None

            if selected_role in available_roles:
                self.settings['role'] = selected_role 
                self.saveSettings()
            else:
                log(f"No such role: {selected_role}")

            return None

        # Trigger to display openai settings  
        self.registerCommand("settings::")
        setting_pattern = r'^settings::|settings:(.*):(.*):'
        match = re.search(setting_pattern, user_input)
        if match:
            if match.group(1):
                setting = match.group(1).lower()
                set_value = match.group(2)
                if setting in self.settings:
                    get_type = type(self.settings[setting])
                    if get_type == bool:
                        if re.search(r'^false$|^0$|^off$', set_value):
                            set_value = False
                        else:
                            set_value = True
                    else:
                        set_value = set_value

                    if setting == "location":
                        prior = str(set_value).lower()
                        try:
                            self.geo = nomi.query_postal_code(set_value)
                            set_value = self.geo['postal_code']
                            set_value = str(set_value).lower()
                        except Exception as e:
                            log(f"error {e}")

                        if str(set_value).lower() == prior:
                            try:
                                tmp = nomi.query_location(set_value, top_k=1)
                                set_value = tmp['postal_code'].iloc[0]
                            except Exception as e:
                                log(f"error {e}")
                                return None
                            
                            self.geo = nomi.query_postal_code(set_value)
                    self.settings[setting] = set_value
                    #self.sym.update_symbiote_settings(settings=self.settings)
                    self.symutils = Utilities(settings=self.settings)
                    self.saveSettings()
            else:
                self.displaySettings()

            return None 

        # Trigger for changing gpt model 
        self.registerCommand("model::")
        model_pattern = r'^model::|model:(.*):'
        match = re.search(model_pattern, user_input)
        if match:
            if match.group(1):
                model_name = match.group(1).strip()
                self.selectModel(model_name)
            else:
                self.selectModel()

            return None 

        # Trigger for changing the conversation file
        self.registerCommand("convo::")
        convo_pattern = r'^convo::|convo:(.*):'
        match = re.search(convo_pattern, user_input)
        if match:
            if match.group(1):
                convo_name = match.group(1).strip()
                self.displayConvo(convo_name) 
            else:
                self.displayConvo()
        
            return None 

        # Trigger for changing working directory in chat
        self.registerCommand("cd::")
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
                log(f"Directory does not exit: {requested_directory}")
                return None

            return None 

        # Trigger to list verbal keywords prompts.
        self.registerCommand("keywords::")
        keywords_pattern = r'^keywords::'
        match = re.search(keywords_pattern, user_input)
        if match:
            for keyword in self.audio_triggers:
                if keyword == 'perifious':
                    continue
                print(f'trigger: {self.audio_triggers[keyword][0]}')

            return None 

        # Trigger for extract:: processing. Load file content and generate a json object about the file.
        self.registerCommand("extract::")
        summary_pattern = r'^extract::|^extract:(.*):(.*):|^extract:(.*):'
        match = re.search(summary_pattern, user_input)
        file_path = None
        
        if match:
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
                #file_path = self.fileSelector("Extraction path:")
                file_path = self.displayFileBrowser()

            if file_path is None:
                return None

            file_path = os.path.expanduser(file_path)

            if os.path.isdir(file_path):
                # prompt to confirm path indexing
                index = inquirer.confirm(message=f'Index {file_path}?').execute()

                if index is True:
                    result = self.symutils.analyze_file(file_path)

                return result
            elif not os.path.isfile(file_path):
                log(f"File not found: {file_path}")
                return None

            summary = self.symutils.analyze_file(file_path)
            #summary = self.symutils.summarizeFile(file_path)
            #if self.settings['debug']:
            #    print(json.dumps(summary, indent=4))
            user_input = user_input[:match.start()] + json.dumps(summary) + user_input[match.end():]

            return user_input 

        # Trigger to flush current running conversation from memory.
        self.registerCommand("flush::")
        flush_pattern = r'^flush::'
        match = re.search(flush_pattern, user_input)
        if match:
            self.flushHistory()
            return None 

        # Trigger for history::. Show the history of the messages.
        self.registerCommand("history::")
        history_pattern = r'^history::|^history:(.*):'
        match = re.search(history_pattern, user_input)
        if self.settings['conversation'] == '/dev/null':
            return None

        if match:
            if match.group(1):
                history_length = int(match.group(1))
                print(history_length)
                time.sleep(4)
            else:
                history_length = False 
           
            history = str()
            for line in self.conversation_history:
                history += f"role: {line['role']}\n{line['content']}\n"
                print(f"role: {line['role']}")
                print(Markdown(line['content']))
                print()

            return None

        # Trigger for code:: extraction from provided text
        self.registerCommand("code::")
        code_pattern = r'code::|code:(.*):'
        match = re.search(code_pattern, user_input)
        if match:
            import symbiote.CodeExtract as codeextract
            codeRun = False
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
                last_message = self.conversation_history[-1]
                print(last_message['content'])
                codeidentify = codeextract.CodeBlockIdentifier(last_message['content'])

            files = codeidentify.process_text()
            for file in files:
                print(file)

            if codeRun:
                pass

            return files

        # Trigger for note:: taking.
        self.registerCommand("note::")
        note_pattern = r'^note::|^note:([\s\S]*?):'
        match = re.search(note_pattern, user_input)
        if match:
            if match.group(1):
                user_input = match.group(1)
            else:
                pass

            self.saveConversation(user_input, self.settings['notes'])

            return None

        # Trigger menu for cli theme change
        self.registerCommand("theme::")
        theme_pattern = r'theme::|theme:(.*):'
        match = re.search(theme_pattern, user_input)
        if match:
            if match.group(1):
                theme_name = match.group(1)
                prompt_style = self.theme_manager.get_theme(theme_name)
            else:
                theme_name, prompt_style = self.theme_manager.select_theme() 

            self.chat_session.style = prompt_style
            self.settings['theme'] = theme_name
            self.saveSettings()

            return None 

        # trigger terminal image rendering view:: 
        self.registerCommand("view::")
        view_pattern = r'view::|^view:(.*):|^view:(https?:\/\/\S+):'
        match = re.search(view_pattern, user_input)
        file_path = None

        if match:
            if match.group(1):
                file_path = match.group(1)
            else:
                #file_path = self.fileSelector('File name:')
                file_path = self.displayFileBrowser()
            
            if os.path.isfile(file_path):
                file_path = os.path.expanduser(file_path)
                file_path = os.path.abspath(file_path)
            elif os.path.isdir(file_path):
                log(f'Must be a file not a directory.')
                return None

            self.symutils.viewFile(file_path)
            print()

            return None

        # Trigger image analysis and reporting analyse_image::
        self.registerCommand("analyze_image::")
        analyze_image_pattern = r'^analyze_image::|^analyze_image:(.*):'
        match = re.search(analyze_image_pattern, user_input)

        if match:
            if match.group(1):
                image_path = match.group(1)
            else:
                #image_path = self.fileSelector('Image path:')
                image_path = self.displayFileBrowser()
                image_path = os.path.expanduser(image_path)
                image_path = os.path.abspath(image_path)

            self.spinner.start()
            import symbiote.ImageAnalysis as ia
            extractor = ia.ImageAnalyzer(detection=True, extract_text=True, backend='mtcnn') 
            results = extractor.analyze_images(image_path, mode='none')
            self.spinner.succeed('Completed')
            human_readable = extractor.render_human_readable(results)
            print(human_readable)

            content = f"Analyze the following details collected about the image or images and summarize the details.\n{human_readable}\n"

            return content

        # Trigger to find files by search find::
        self.registerCommand("find::")
        find_pattern = r'^find::|^find:(.*):'
        match = re.search(find_pattern, user_input)
        if match:
            if match.group(1):
                pattern = match.group(1)
                result = self.findFiles(pattern)
                return None

            result = self.findFiles()   

            return None

        # Trigger to init scrolling
        self.registerCommand("scroll::")
        scroll_pattern = r'scroll::|scroll:(.*):'
        match = re.search(scroll_pattern, user_input)
        if match:
            file_path = None
            if match.group(1):
                file_path = match.group(1)

            #file_path = self.fileSelector("File name:")
            file_path = self.displayFileBrowser()
            print(file_path)

            if file_path is None:
                return None

            file_path = os.path.expanduser(file_path)
            absolute_path = os.path.abspath(file_path)

            self.symutils.scrollContent(absolute_path)

            return None

        # Trigger for wikipedia search wiki::
        self.registerCommand("wiki::")
        wiki_pattern = r'wiki:(.*):'
        match = re.search(wiki_pattern, user_input)
        if match:
            if match.group(1):
                import symbiote.Wikipedia as wikipedia
                wiki = wikipedia.WikipediaSearch()
                search_term = match.group(1)
                results = wiki.search(search_term, 5)
                results_str = str()
                for result in results:
                    results_str += result['text']

                print(Panel(Text(results_str[:8000]), title=f"Wikipedia: {search_term}"))
                content = f"wikipedia search\n"
                content += '\n```\n{}\n```\n'.format(results_str)
                user_input = user_input[:match.start()] + content + user_input[match.end():]

                return user_input
            else:
                log("No search term provided.")
                return None

        # Trigger for headline analysis
        self.registerCommand("news::")
        self.registerCommand("headlines::")
        news_pattern = r'\bnews::|\bheadlines::'
        match = re.search(news_pattern, user_input)
        if match:
            import symbiote.headlines as hl
            gh = hl.getHeadlines()
            result = gh.scrape()
            print(Panel(Text(result), title=f"News Headlines"))
            content = f"Consolidate and summarize the following.\n"
            content += '\n```\n{}\n```\n'.format(result)
            user_input = user_input[:match.start()] + content + user_input[match.end():]

            return user_input

        # Trigger for google search or dorking
        self.registerCommand("google::")
        google_pattern = r'google:(.*):'
        match = re.search(google_pattern, user_input)
        if match:
            if match.group(1):
                import symbiote.googleSearch as gs
                search_term = match.group(1)
                search = gs.googleSearch()
                links = search.fetch_links(search_term)
                result = search.fetch_text_from_urls(links)
                result = self.cleanText(result)
                print(Panel(Text(result[:5000]), title=f"Search Result: {search_term}"))
                content = str()
                for link in links:
                    content += f"{link}\n"
                print(Panel(Text(content), title=f"Links:"))

                user_input = user_input[:match.start()] + result + user_input[match.end():]
                return user_input
            else:
                log("No search term provided.")
                return None

        # Trigger for define::
        self.registerCommand("define::")
        define_pattern = r'define:(.*):'
        match = re.search(define_pattern, user_input)
        if match:
            if match.group(1):
                term = match.group(1)
                content = f"""Provide the definition and details of "{term}". The response must be in markdown, .md format. The response should incude the following fields.

"term": {term} 
"definition": A brief definition of the {term}.
"examples": A list of 3 facts related to "{term}".
"related_terms": A list of 5 terms related to the searched term.
"""
                user_input = content

                return user_input

        # Trigger for imap mail checker mail::
        self.registerCommand("mail::")
        mail_pattern = r'mail::'
        match = re.search(mail_pattern, user_input)
        if match:
            import symbiote.GetEmail as mail
            mail_checker = mail.MailChecker(
                    username=self.settings['imap_username'],
                    password=self.settings['imap_password'],
                    mail_type='imap',
                    days=2,
                    unread=False,
                    #model=self.settings['model'],
                    model=None,
                    )
            email = mail_checker.check_mail()

            content = [] 
            for key, val in enumerate(email):
                content.append(f"Message: {key}")
                content.append(f"\tDate: {val['date']}")
                content.append(f"\tFrom: {val['from']}")
                content.append(f"\tTo: {val['to']}")
                content.append(f"\tSubject: {val['subject'][:30]}")
                #content.append(f"\tBody Size: {len(val['body'])} chars")
                content.append("")
                #content.append(f"\tBody:\n\t\t{val['body'][:]}\n")

            content = "\n".join(content)

            if email is None:
                log(f"No emails to analyze.")
                return None

            review = json.dumps(email)
            prompt = f"Create a report from the following in a nice format."
            review = f"{prompt}\n```json\n{review}\n```\n"
            print(Panel(Text(content), title=f"Emails: {self.settings['imap_username']}"))
            print()
            user_input = user_input[:match.start()] + review + user_input[match.end():]

            return user_input

        # Trigger for w3m web browser functionality browser::
        self.registerCommand("w3m::")
        self.registerCommand("browser::")
        browser_pattern = r'w3m:(.*):|browser:(.*):'
        match = re.search(browser_pattern, user_input)
        if match:
            if match.group(1):
                url = match.group(1)
                self.openW3m(url)
            else:
                self.openW3m()

            return None

        # Trigger to extract images from a url image_extract::
        self.registerCommand("image_extract::")
        image_extract_pattern = r'^image_extract:(.*):'
        match = re.search(image_extract_pattern, user_input)
        if match:
            if match.group(1):
                url = match.group(1)
                self.urlImageExtract(url)
            else:
                log('No url specified.')

            return None

        # Trigger for qr code generation qr::
        self.registerCommand("qr::")
        qr_pattern = r'qr:([\s\S]*?):'
        match = re.search(qr_pattern, user_input)
        if match:
            if match.group(1):
                content = match.group(1)
                self.generateQr(content)
            else:
                log("No content provided for the qr.")

            return None

        # Trigger for weather::
        self.registerCommand("weather::")
        weather_pattern = r"weather::|weather:(.*):"
        match = re.search(weather_pattern, user_input)
        if match:
            if match.group(1):
                location = match.group(1)
            else:
                location = self.settings['location']

            if location is None:
                log("No location set in settings::")
                return None

            result = self.getWeather(location)
            self.memory.create("weather_command", result)

            if result is None:
                log(f"Unable to get weather for {location}")
                return None

            weather = json.dumps(result['current_condition']) 
            print(Panel(Text(weather), title=f"Weather: {location}"))
            content = f"Analyze the following weather details and provide a well formatted weather report for {location}.\n```json\n{weather}```"
            user_input = user_input[:match.start()] + content + user_input[match.end():]

            return user_input

        # Trigger for inspect:: command to inspect running python objects.
        self.registerCommand("inspect::")
        inspect_pattern = r'inspect::|inspect:(.*):'
        match = re.search(inspect_pattern, user_input)
        if match:
            if match.group(1):
                obj = match.group(1)
            else:
                all_objs = list({**globals(), **locals()}.keys())
                obj = self.listSelector("Objects:", all_objs)

            if obj:
                obj = eval(obj, globals(), locals())
                inspect(obj, methods=True, help=True, all=True)
            else:
                log(f"No object selected.")

            print()
            return None

        # Trigger for memory:: management
        self.registerCommand("memory::")
        memory_pattern = r"^memory::|^memory:(.*):"
        match = re.search(memory_pattern, user_input)
        if match:
            if match.group(1):
                info = match.group(1)

            inspect(self.memory.structure())

            return None

        # Trigger for search:: on memory 
        self.registerCommand("search::")
        search_pattern = r"search::|search:(.*):"
        match = re.search(search_pattern, user_input)
        if match:
            if match.group(1):
                search_term = match.group(1)
            else:
                search_term = self.textPrompt("Search term|regex>") 

            text_result = self.getSearchResults(search_term)

            if text_result:
                self.memory.create("search_command", str(text_result))
                if self.return_input:
                    self.writeHistory("user", text_result)
                else:
                    content = f"```json\n{text_result}\n```"
                    user_input = user_input[:match.start()] + content + user_input[match.end():]
                    return user_input

            return None

        # Trigger for file:: processing. Load file content into user_input for ai consumption.
        # file:: - opens file or directory to be pulled into the conversation
        self.registerCommand("file::")
        file_pattern = r'file::|file:(.*):'
        match = re.search(file_pattern, user_input)
        if match: 
            file_path = None
            if match.group(1):
                file_path = match.group(1)
            else:
                file_path = self.displayFileBrowser()

            if file_path is None:
                log(f"No such file or directory: {file_path}")
                return None 
            
            file_path = os.path.expanduser(file_path)
            file_path = os.path.abspath(file_path)

            if os.path.isfile(file_path):
                content = self.symutils.extractText(file_path)
                print(Panel(Text(content), title=f"Content: {file_path}"))
                self.memory.create("file_command", content)

                file_content = f"File name: {file_path}\n"
                file_content += '\n```\n{}\n```\n'.format(content)
                user_input = user_input[:match.start()] + file_content + user_input[match.end():]
            elif os.path.isdir(file_path):
                log(f"Directory crawling is temporarily disabled due to memory consumption.")
                return None
                content = self.symutils.extractDirText(file_path)
                if content is None:
                    log(f"No content found in directory: {file_path}")
                    return None
                print(Panel(Text(content), title=f"Content: {file_path}"))
                user_input = user_input[:match.start()] + dir_content + user_input[match.end():]

            return user_input

        # Trigger image:: execution for AI image generation
        self.registerCommand("image::")
        image_pattern = r'^image:([\s\S]*?):'
        match = re.search(image_pattern, user_input)
        if match:
            if match.group(1):
                query = match.group(1)
                self.fluxImageGenerator(query)
            else:
                log(f"No image description provided.")

            return None

        # Trigger system execution of a command
        self.registerCommand("$")
        self.registerCommand("run::")
        exec_pattern = r'^\$(.*)|run:(.*):'
        match = re.search(exec_pattern, user_input)
        if match:
            if match.group(1):
                command = match.group(1)
                result = self.execCommand(command)
                if result:
                    print(Panel(Text(result), title=f"Command: {command}"))
                    self.writeHistory('user', result)
                return None
            elif match.group(2):
                command = match.group(2)
                result = self.execCommand(command)
                print(Panel(Text(result), title=f"Command: {command}"))
                content = f"\n```{command}\n{result}\n```\n"
                user_input = user_input[:match.start()] + content + user_input[match.end():]
                return user_input

            return None

        # Trigger for getip::
        self.registerCommand("getip::")
        getip_pattern = r'getip::'
        match = re.search(getip_pattern, user_input)
        if match:
            ipinfo = self.getIp()
            report = self.ifaceReport(ipinfo)
            self.memory.create("getip_command", report)

            print(Panel(Text(report), title=f"Network Info:"))

            content = str()
            content = f"\n```network_info\n{ipinfo}\n```"
            
            if _checkCommand:
                self.writeHistory('user', content)
                return None

            user_input = user_input[:match.start()] + content + user_input[match.end():]

            return user_input

        # Trigger for get:URL processing. Load website content into user_input for model consumption.
        self.registerCommand("get::")
        get_pattern = r'get::|get:(https?://\S+):'
        match = re.search(get_pattern, user_input)
        if match:
            crawl = False
            website_content = str() 
            if match.group(1):
                url = match.group(1)
            else:
                url = self.textPrompt("URL to load:")
            
            if url is None:
                log(f"No URL given: {url}")
                return None 

            content = str()
            css = str()
            script = str()
            links = str()
            link_list = []
            
            log(f"Fetching {url}...")
            import symbiote.WebCrawler as webcrawler
            crawler = webcrawler.WebCrawler(browser='firefox')
            pages = crawler.pull_website_content(url, search_term=None, crawl=crawl, depth=None)
            crawler.close()

            if pages:
                for md5, item in pages.items():
                    content += item['content']
                    link_list = link_list + item['links']
                    links += "\n".join(item['links'])
                    css += "\n".join(item['css'])
                    script += "\n".join(item['scripts'])
            else:
                log(f"No content gathered for {url}")
                return None

            self.memory.create("get_command",
                               {"content": content,
                                "links": link_list,
                                "css": css,
                                "scripts": script
                                })

            content = self.cleanText(content)
            css = self.cleanText(css)
            script = self.cleanText(script)

            '''
            print(Panel(Text(content[:1000]), title=f"Content: {url}"))
            if css:
                print(Panel(Text(css[:1000]), title=f"CSS: {url}"))
            if script:
                print(Panel(Text(script[:1000]), title=f"Scripts: {url}"))
            if len(links) > 0:
                print(Panel(Text(links), title=f"Links: {url}"))
            '''
            user_input = user_input[:match.start()] + content + user_input[match.end():]

            return user_input 

        # Trigger for fake news analysis fake_news::
        self.registerCommand("fake_news::")
        fake_news_pattern = r'\bfake_news::|\bfake_news:(.*):'
        match = re.search(fake_news_pattern, user_input)
        if match:
            data = None
            if match.group(1):
                data = match.group(1)
            else:
                data = self.textPrompt("URL or text to analyze:")

            if data is None:
                log(f"No data provided.")
                return None

            self.spinner.start()
            import symbiote.FakeNewsAnalysis as fake_news
            detector = fake_news.FakeNewsDetector()
            if self.isValidUrl(data) is True:
                text = detector.download_text_from_url(data)
            else:
                text = data

            result = detector.analyze_text(text)
            self.spinner.succeed('Completed')
            if result:
                output = json.dumps(result, indent=4)
                print(Panel(Text(output), title=f"FakeNew Analysis: {data}"))
                user_input = f"The following results are from a fake news analyzer.  Analyze the following json document and provide a summary and report of the findings.\n{result}"
            else:
                log(f"No results for {data}")
                return None
            
            return user_input

        # Trigger for downloading youtube transcripts yt_transcript::
        self.registerCommand("yt_transcript::")
        yt_transcript_pattern = r'yt_transcript::|yt_transcript:(.*):'
        match = re.search(yt_transcript_pattern, user_input)
        if match:
            if match.group(1):
                yt_url = match.group(1)
            else:
                yt_url = self.textPrompt("Youtube URL:")

            if yt_url == None:
                log(f"No transciprts url set.")
                return None

            log(f"Fetching youtube transcript from: {yt_url}")

            import symbiote.YoutubeUtility as ytutil
            yt = ytutil.YouTubeUtility(yt_url)
            transcript = yt.get_transcript()
            if transcript:
                print(Panel(Text(transcript), title=f"Transcripts: {yt_url}"))
                user_input = user_input[:match.start()] + transcript + user_input[match.end():]
            else:
                log(f"No transcripts found.")
                return None

            return user_input

        # Trigger web vulnerability scan webvuln::
        self.registerCommand("webvuln::")
        webvuln_pattern = r'webvuln::|webvuln:(.*):'
        match = re.search(webvuln_pattern, user_input)
        if match:
            if match.group(1):
                url = match.group(1)
            else:
                url = self.textPrompt("URL to scan:")

            if self.isValidUrl(url):
                import symbiote.WebVulnerabilityScan as web_vuln
                scanner = web_vuln.SecurityScanner(headless=True, browser='firefox')
                scanner.scan(url)
                report = scanner.generate_report()
                print(Panel(Text(report), title=f"Report: {url}"))
                user_input = f"Review the following web vulnerability scan and provide details and action items.\n{report}"
                return user_input
            else:
                return None

        # Trigger for textual deception analysis deception::
        self.registerCommand("deception::")
        deception_pattern = r'deception::|deception:(.*):'
        match = re.search(deception_pattern, user_input)
        analysis_src = None
        if match:
            if match.group(1):
                analysis_src = match.group(1)
            else:
                analysis_src = self.textPrompt("Text or URL:")

            if analysis_src == None:
                log("No content to analyze.")
                return None

            self.spinner.start()
            import symbiote.DeceptionDetection as deception
            detector = deception.DeceptionDetector()
            results = detector.analyze_text(analysis_src)
            self.spinner.succeed('Completed')
            if results:
                content = json.dumps(results, indent=4)
                print(Panel(Text(content), title=f"Deception Analysis Summary"))
                user_input = f"Review the following JSON and create a report on the deceptive findings.\n{content}"
            else:
                log("No results returned.")
                return None

            return user_input

        # Trigger for crawl:URL processing. Load website content into user_input for model consumption.
        self.registerCommand("crawl::")
        crawl_pattern = r'crawl::|crawl:(https?://\S+):'
        match = re.search(crawl_pattern, user_input)
        if match:
            crawl = True
            website_content = str() 
            if match.group(1):
                url = match.group(1)
            else:
                url = self.textPrompt("URL to load:")
            
            if url == None:
                log(f"No URL specified...")
                return None 

            crawler = webcrawler.WebCrawler(browser='firefox')
            self.spinner.start()
            pages = crawler.pull_website_content(url, search_term=None, crawl=crawl, depth=None)
            crawler.close()
            self.spinner.succeed('Completed')
            for md5, page in pages.items():
                content += page['content']
            print(Panel(Text(content), title=f"Content: {url}"))
            user_input = user_input[:match.start()] + content + user_input[match.end():]
            print()
            return user_input 

        return user_input

    def saveSettings(self):
        try:
            with open(self.config_file, "w") as file:
                json.dump(self.settings, file, indent=4, sort_keys=True)
        except Exception as e:
            log(f"Error Writing: {e}")
            return None

    def loadSettings(self):
        try:
            with open(self.config_file, "r") as file:
                settings = json.load(file)
        except Exception as e:
            log(f"Error Reading: {e}")
            return None

        print(settings)

        return settings

    def createDialog(self, title, text):
        message_dialog(
            title=title,
            text=text).run()

    def fileSelector(self, message, start_path='./'):
        result = inquirer.filepath(
                message=message,
                default=start_path,
                #validate=PathValidator(is_file=True, message="Input is not a file"),
                wrap_lines=True,
                mandatory=False,
            ).execute()
        return result

    def listSelector(self, message, selection):
        result = inquirer.select(
                message=message,
                choices=selection,
                mandatory=False).execute()
        return result 

    def textPrompt(self, message):
        result = inquirer.text(
                message=message,
                mandatory=False,
            ).execute()
        return result

    def yesNoPrompt(self, question="Continue?"):
        answer = inquirer.confirm(message=question, default=False).execute()
        return answer
            
    def findFiles(self, pattern=None):
        # Recursively get a list of all files from the current directory
        all_files = []
        for root, dirs, files in os.walk('.'):
            for f in files:
                full_path = os.path.join(root, f)
                all_files.append(full_path)

        if pattern is None:
            # Prompt user for a pattern (regex)
            pattern = prompt("Enter a pattern (regex) to search for files: ")

        try:
            # Filter files based on the regex pattern
            matching_files = []
            for file in all_files:
                if re.search(pattern, file):
                    matching_files.append(file)

            if len(matching_files) > 0:
                selected_file = self.listSelector("Matching files:", sorted(matching_files))
                return selected_file
            else:
                log(f"No matching file found for: {pattern}")
                return None

        except re.error:
            log("Invalid regex pattern!")

    def loadConversation(self):
        self.conversations_file = conversations_file
        data = []

        if os.path.exists(self.conversations_file):
            try:
                with open(conversations_file, 'r') as file:
                    for line in file:
                        data.append(json.loads(line))

            except Exception as e:
                log("Error: opening %s: %s" % (conversations_file, e))
                sys.exit(10)

        return data

    def saveConversation(self, role, text):
        ''' Save conversation output to loaded conversation file '''
        json_conv = {
                "epoch": time.time(),
                "role": role,
                "content": text 
                }

        jsonl_string = json.dumps(json_conv)

        with open(self.conversations_file, 'a+') as file:
            #json.dump(data, file, indent=2)
            file.write(jsonl_string + "\n")

    def estimateTokenCount(self, text):
        # Estimate tokens based on the average number of characters per token
        average_chars_per_token = 4

        # Calculate the number of tokens
        token_count = len(text) / average_chars_per_token

        # Return the rounded token count
        return round(token_count)

    def cleanText(self, text):
        # Remove leading and trailing whitespace
        text = text.strip()

        # Replace multiple spaces with a single space
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n+', '\n', text)

        # Remove any non-ASCII characters (optional, based on your needs)
        text = re.sub(r'[^\x00-\x7F]+', '', text)

        # Normalize dashes and remove unnecessary punctuation
        #text = re.sub(r'[–—]', '-', text)  # Normalize dashes
        #text = re.sub(r'[“”]', '"', text)  # Normalize quotes
        #text = re.sub(r"[‘’]", "'", text)  # Normalize apostrophes

        # Optionally remove or replace other special characters
        # You can customize this step according to your needs
        # For example, remove non-alphanumeric except common punctuation
        #text = re.sub(r'[^\w\s.,!?\'"-]', '', text)

        # Further replace double punctuation (optional)
        text = re.sub(r'\.{2,}', '.', text)  # Replace multiple dots with a single dot

        #text = text.lower()

        return text

    def imageBase64(self, image_path):
        # Open the image
        try:
            with Image.open(image_path) as img:
                # Convert to PNG format if not already in JPEG, JPG, or PNG
                if img.format not in ['JPEG', 'JPG', 'PNG']:
                    with io.BytesIO() as output:
                        img.save(output, format="PNG")
                        png_data = output.getvalue()
                else:
                    with io.BytesIO() as output:
                        img.save(output, format=img.format)
                        png_data = output.getvalue()

            # Encode the PNG image to base64
            png_base64 = base64.b64encode(png_data).decode('utf-8')
        except Exception as e:
            log(f"Error processing image: {e}")
            return None

    def describeImage(self, image_path):
        try:
            encoded_image = self.imageBase64(image_path)
        except:
            return None

        # Call the Ollama API with the LLaVA model
        try:
            response = ollama.generate(
                model='minicpm-v',
                prompt=prompt,
                images=[encoded_image]
            )

            # Extract the generated text from the response
            detected_objects = response['response']
            return detected_objects
        except Exception as e:
            log(f"Error processing image: {e}")
            return None

    def pythonTool(self, code):
        # Start the Python subprocess in interactive mode
        python_interpreter = sys.executable 
        child = pexpect.spawn(python_interpreter, ['-i'], encoding='utf-8')

        # Wait for the initial prompt
        child.expect('>>> ')

        # Initialize a string to store the interaction log
        interaction_log = str()

        # Split the code into lines
        lines = code.strip().split('\n')

        # Iterate through each line of code and send it to the subprocess
        for i, line in enumerate(lines):
            try:
                # Send the line to the Python interpreter
                child.sendline(line)

                # Log the input line
                interaction_log += f">>> {line}\n"

                # Expect and capture all outputs until the next primary prompt
                while True:
                    index = child.expect([r'>>> ', r'\.\.\. ', pexpect.EOF])
                    interaction_log += child.before.strip() + "\n"
                    if index == 0:  # '>>> ' prompt indicates primary prompt
                        print(child.before.strip())
                        break
                    elif index == 1:  # '... ' prompt indicates continuation
                        print(child.before.strip())
                        # If this is the last line, send an empty line to execute the block
                        if i == len(lines) - 1:
                            child.sendline('')
                    elif index == 2:  # EOF indicates the end of the output
                        print(child.before.strip())
                        return interaction_log.strip()
            except pexpect.EOF:
                print(child.before.strip())
                interaction_log += child.before.strip() + "\n"
                break
            except pexpect.ExceptionPexpect as e:
                log(f"Error executing line '{line}': {e}")
                interaction_log += f"Error executing line '{line}': {e}\n"
                break
       
        # Close the child process
        child.close()

        return interaction_log.strip()

    def fluxImageGenerator(self, query_text):
        self.spinner.start()
        # Get the API key from environment variables
        api_key = os.getenv("HUGGINGFACE_API_KEY")

        # Set up the API URL and headers
        API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        headers = {"Authorization": f"Bearer {api_key}"}

        def query(payload):
            response = requests.post(API_URL, headers=headers, json=payload)
            return response.content

        image_bytes = query({
            "inputs": query_text,
        })

        # You can access the image with PIL.Image for example
        image = Image.open(io.BytesIO(image_bytes))
        self.spinner.succeed('Completed')

        # Open the image for viewing
        image.show()

    def generateQr(self, text: str, center_color: str = "#00FF00", outer_color: str = "#0000FF", back_color: str = "black", dot_size: int = 10, border_size: int = 10):
        # Create a QR code object
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # Higher error correction
            box_size=dot_size,
            border=4,
        )

        # Add data to the QR code
        qr.add_data(text)
        qr.make(fit=True)

        # Get the QR code matrix
        qr_matrix = qr.get_matrix()
        qr_size = len(qr_matrix)

        # Create a new image with a background color
        img_size = qr_size * dot_size + 2 * border_size
        img = Image.new("RGBA", (img_size, img_size), back_color)
        draw = ImageDraw.Draw(img)

        # Calculate the gradient
        def getGradientColor(x, y, center_x, center_y, inner_color, outer_color, max_dist):
            # Distance from the center
            dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            ratio = min(dist / max_dist, 1)

            # Interpolating the color
            r1, g1, b1 = inner_color
            r2, g2, b2 = outer_color

            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)

            return (r, g, b)

        # Center of the QR code
        center_x = img_size // 2
        center_y = img_size // 2
        max_dist = ((center_x) ** 2 + (center_y) ** 2) ** 0.5

        # Convert hex colors to RGB
        center_color_rgb = ImageColor.getrgb(center_color)
        outer_color_rgb = ImageColor.getrgb(outer_color)

        # Draw the QR code with gradient dots
        for y in range(qr_size):
            for x in range(qr_size):
                if qr_matrix[y][x]:
                    x1 = x * dot_size + border_size
                    y1 = y * dot_size + border_size
                    fill_color = getGradientColor(x1, y1, center_x, center_y, center_color_rgb, outer_color_rgb, max_dist)
                    draw.ellipse([x1, y1, x1 + dot_size, y1 + dot_size], fill=fill_color)

        # Display the image
        img.show()

    def openW3m(self, website_url='https://google.com'):
        try:
            subprocess.run(['w3m', website_url])
        except FileNotFoundError:
            log("Error: w3m is not installed on your system. Please install it and try again.")
        except Exception as e:
            log(f"An error occurred: {e}")

    def urlImageExtract(self, url, mode='merged', images_per_row=3):
        # Send a request to the URL
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code != 200:
            raise Exception(f"Failed to fetch the webpage: {response.status_code}")

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all image tags
        img_tags = soup.find_all('img')
        images = []
        img_sources = []

        # Loop through all the image tags and open them
        for img_tag in img_tags:
            img_url = img_tag.get('src')

            # Handle relative URLs
            if img_url and not img_url.startswith(('http://', 'https://')):
                img_url = requests.compat.urljoin(url, img_url)

            try:
                # Get the image content
                img_response = requests.get(img_url)

                # Check the content type to ensure it's an image
                content_type = img_response.headers.get('Content-Type')
                if 'image' in content_type:
                    img = Image.open(BytesIO(img_response.content))
                    images.append(img)
                    img_sources.append(img_url)
                else:
                    log(f"Skipped non-image content at {img_url}")
            except Exception as e:
                log(f"Failed to open image: {img_url} - {e}")

        if not images:
            log("No images found.")
            return

        if mode == 'merged':
            # Determine the size of the resulting image
            max_width = max(img.width for img in images)
            max_height = max(img.height for img in images)
            total_width = images_per_row * max_width
            total_height = (len(images) + images_per_row - 1) // images_per_row * max_height

            # Create a new blank image
            combined_image = Image.new('RGB', (total_width, total_height), (255, 255, 255))

            # Paste each image into the combined image
            for index, img in enumerate(images):
                x = (index % images_per_row) * max_width
                y = (index // images_per_row) * max_height
                combined_image.paste(img, (x, y))

            # Display the combined image
            combined_image.show()

        elif mode == 'individual':
            # Show each image individually
            for img in images:
                img.show()

    def isValidUrl(self, url):
        if re.search(r'^https?://\S+', url):
            return True
        else:
            return False

    def execCommand(self, command):
        try:
            process = subprocess.Popen(command, shell=True, text=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            output = stdout + stderr
        except KeyboardInterrupt:
            log("\nCommand interrupted by Control-C.", flush=True)
            if process:
                process.terminate()
                process.wait()
        except subprocess.CalledProcessError as e:
            # Combine stdout and stderr from the exception
            output = e.stdout + e.stderr if e.stdout or e.stderr else "Command exited with a status other than 0."

        # Return the combined output
        return output.strip()

    def displayFileBrowser(self):
        """Terminal-based file browser using prompt_toolkit to navigate and select files."""
        current_path = Path.home()  # Start in the user's home directory
        #current_path = Path.cwd()
        files = []
        selected_index = 0  # Track the selected file/folder index
        scroll_offset = 0  # Track the starting point of the visible list
        show_hidden = False  # Initialize hidden files visibility

        terminal_height = int(os.get_terminal_size().lines)
        max_display_lines = terminal_height - 4  # Reduce by 2 for header and footer lines

        def updateFileList():
            """Update the list of files in the current directory, with '..' as the first entry to go up."""
            nonlocal files, selected_index, scroll_offset
            # List current directory contents and insert '..' at the top for navigating up
            all_files = [".."] + sorted(current_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))

            # Filter out hidden files if `show_hidden` is False
            files = [f for f in all_files if isinstance(f, str) or show_hidden or not f.name.startswith('.')]

            selected_index = 0
            scroll_offset = 0

        def getDisplayText():
            """Display text for the current directory contents with the selected item highlighted."""
            text = []
            visible_files = files[scroll_offset:scroll_offset + max_display_lines]
            for i, f in enumerate(visible_files):
                real_index = scroll_offset + i
                prefix = "> " if real_index == selected_index else "  "
                
                # Use only the file or directory name for display
                display_name = f if isinstance(f, str) else f.name
                display_name += "/" if isinstance(f, Path) and f.is_dir() else ""
                
                line = f"{prefix}{display_name}"
                text.append((f"{'yellow' if real_index == selected_index else 'white'}", line))
                text.append(('', '\n'))
            return text

        # Initialize file list with the home directory contents
        updateFileList()

        # Key bindings
        kb = KeyBindings()

        @kb.add("up")
        def moveUp(event):
            nonlocal selected_index, scroll_offset
            selected_index = (selected_index - 1) % len(files)
            # Scroll up if the selection goes above the visible area
            if selected_index < scroll_offset:
                scroll_offset = max(0, scroll_offset - 1)

        @kb.add("down")
        def moveDown(event):
            nonlocal selected_index, scroll_offset
            selected_index = (selected_index + 1) % len(files)
            # Scroll down if the selection goes beyond the visible area
            if selected_index >= scroll_offset + max_display_lines:
                scroll_offset = min(len(files) - max_display_lines, scroll_offset + 1)

        @kb.add("enter")
        def enterDirectory(event):
            nonlocal current_path
            selected_file = files[selected_index]

            if selected_file == "..":
                # Move up to the parent directory
                current_path = current_path.parent
                updateFileList()
            elif isinstance(selected_file, Path) and selected_file.is_dir():
                # Enter the selected directory
                current_path = selected_file
                updateFileList()
            elif isinstance(selected_file, Path) and selected_file.is_file():
                # Select the file and exit
                event.app.exit(result=str(selected_file))  # Return the file path as a string

        @kb.add("escape")
        def cancelSelection(event):
            event.app.exit(result=None)  # Exit with None if canceled

        @kb.add("c-h")
        def toggleHidden(event):
            """Toggle the visibility of hidden files."""
            nonlocal show_hidden
            show_hidden = not show_hidden
            updateFileList()

        # Layout with footer for shortcut hint
        header_window = Frame(Window(FormattedTextControl(lambda: f"Current Directory: {current_path}"), height=1))
        file_list_window = Window(content=FormattedTextControl(getDisplayText), wrap_lines=False, height=max_display_lines)
        footer_window = Window(content=FormattedTextControl(lambda: "Press Ctrl-H to show/hide hidden files. Escape to exit."), height=1, style="grey")

        layout = Layout(HSplit([
            header_window, 
            file_list_window,
            footer_window
        ]))

        # Application
        app = Application(layout=layout, key_bindings=kb, full_screen=True, refresh_interval=0.1)

        # Run the application and return the selected file path (or None if canceled)
        return app.run()

    def flushHistory(self):
        self.conversation_history = []
        self.current_conversation = []

    def registerCommand(self, command):
        self.command_register.append(command)

    def getConversations(self, path):
        files = os.listdir(path)
        if not files:
            log("No conversations found.")

        conversations = []
        for file in files:
            if re.search(r'\S+.jsonl$', file):
                conversations.append(file)

        return conversations

    def displayPager(self, text):
        search_field = SearchToolbar()

        output_field = TextArea(
                text,
                scrollbar=True,
                search_field=search_field,
                )

        kb = KeyBindings()

        @kb.add("escape")
        @kb.add("q")
        def _(event):
            event.app.exit()

        framing = Frame(
                output_field,
                title="Content Viewer",
                )

        layout = Layout(framing, focused_element=output_field)

        app = Application(
                layout=layout,
                key_bindings=kb,
                mouse_support=True,
                full_screen=True
                )

        return app.run()

    def getWeather(self, location="33004"):
        text = None 
        try:
            # Format the URL for wttr.in with the specified location
            url = f'https://wttr.in/{location}?format=j1'
            response = requests.get(url)

            if response.status_code == 200:
                text = json.loads(response.text)
                return text 
            else:
                log(f"Failed to get weather data. Status code: {response.status_code}")
        except Exception as e:
            log(f"An error occurred: {e}")

        return text

    def getIp(self):
        import netifaces
        import dns.resolver
        network_info = {
            "interfaces": {},
            "dns_resolvers": [],
            "default_gateways": {},
            "external_ip": "", 
        }

        try:
            # Format the URL for wttr.in with the specified location
            url = f'https://api.ipify.org'
            response = requests.get(url)

            if response.status_code == 200:
                network_info['external_ip'] = response.text
            else:
                log(f"Failed to get weather data. Status code: {response.status_code}")
        except Exception as e:
            log(f"An error occurred: {e}")

        # Gather information about each network interface
        for interface in netifaces.interfaces():
            interface_info = {}
            addresses = netifaces.ifaddresses(interface)
            
            # IPv4 information
            if netifaces.AF_INET in addresses:
                ipv4_info = addresses[netifaces.AF_INET][0]
                interface_info["ipv4"] = {
                    "address": ipv4_info.get("addr"),
                    "netmask": ipv4_info.get("netmask"),
                    "broadcast": ipv4_info.get("broadcast")
                }
            
            # IPv6 information
            if netifaces.AF_INET6 in addresses:
                ipv6_info = addresses[netifaces.AF_INET6][0]
                interface_info["ipv6"] = {
                    "address": ipv6_info.get("addr"),
                    "netmask": ipv6_info.get("netmask"),
                    "broadcast": ipv6_info.get("broadcast")
                }
            
            # MAC address (hardware address)
            if netifaces.AF_LINK in addresses:
                mac_info = addresses[netifaces.AF_LINK][0]
                interface_info["mac"] = mac_info.get("addr")
            
            # Add interface information to the main dictionary
            network_info["interfaces"][interface] = interface_info

        # Collect DNS resolvers
        try:
            with open('/etc/resolv.conf', 'r') as file:
                for line in file:
                    if line.startswith('nameserver'):
                        network_info["dns_resolvers"].append(line.split()[1])
        except FileNotFoundError:
            network_info["dns_resolvers"] = ["Could not read /etc/resolv.conf"]

        # Collect default gateway information
        gateways = netifaces.gateways()
        for family, gateway_info in gateways.get("default", {}).items():
            if family == netifaces.AF_INET:
                network_info["default_gateways"]["ipv4"] = {
                    "gateway": gateway_info[0],
                    "interface": gateway_info[1]
                }
            elif family == netifaces.AF_INET6:
                network_info["default_gateways"]["ipv6"] = {
                    "gateway": gateway_info[0],
                    "interface": gateway_info[1]
                }

        return network_info

    def ifaceReport(self, network_info):
        report = []
        report.append("Network Information\n" + "="*20)

        # External IP
        report.append("\nExternal IP:")
        if network_info["external_ip"]:
            report.append(f"  - {network_info['external_ip']}")
        else:
            report.append("  None")

        # DNS Resolvers
        report.append("\nDNS Resolvers:")
        if network_info["dns_resolvers"]:
            for resolver in network_info["dns_resolvers"]:
                report.append(f"  - {resolver}")
        else:
            report.append("  None")

        # Default Gateways
        report.append("\nDefault Gateways:")
        gateway_devs = []
        ipv4_gateway = network_info["default_gateways"].get("ipv4")
        if ipv4_gateway:
            report.append(f"  Gateway: {ipv4_gateway['gateway']}")
            report.append(f"  Interface: {ipv4_gateway['interface']}")
            gateway_devs.append(ipv4_gateway['interface'])

        ipv6_gateway = network_info["default_gateways"].get("ipv6")
        if ipv6_gateway:
            report.append(f"  Gateway: {ipv6_gateway['gateway']}")
            report.append(f"  Interface: {ipv6_gateway['interface']}")
            gateway_devs.append(ipv6_gateway['interface'])

        # Interface information
        report.append(f"\nInterfaces:")
        for interface, details in network_info["interfaces"].items():
            primary = "" 
            if interface in gateway_devs:
                primary = " *primary" 

            mac = details.get("mac", None)
            # IPv4 Info
            ipv4_info = details.get("ipv4")
            if ipv4_info:
                report.append(f"  {interface}:{primary}")
                report.append(f"    Address: {ipv4_info.get('address')}")
                report.append(f"    Netmask: {ipv4_info.get('netmask')}")
                report.append(f"    Broadcast: {ipv4_info.get('broadcast')}")
                if mac is not None:
                    report.append(f"    Mac: {mac}")

                continue

            # IPv6 Info
            ipv6_info = details.get("ipv6")
            if ipv6_info:
                report.append(f"  {interface}:{primary}")
                report.append(f"    Address: {ipv6_info.get('address')}")
                report.append(f"    Netmask: {ipv6_info.get('netmask')}")
                report.append(f"    Broadcast: {ipv6_info.get('broadcast')}")
                if mac is not None:
                    report.append(f"    Mac: {mac}")

                continue

        # Join the report list into a single string
        return "\n".join(report)

    def getSearchResults(self, search_term=None):
        if search_term.startswith("/") and search_term.endswith("/"):
            search_pattern = rf"{search_term[1:-1]}" 
            try:
                search_for = re.compile(search_pattern)
            except Exception as e:
                log(f"Invalid regex pattern: {e}")
                return None
        elif search_term is None:
            log(f"Variable search_term is empty.")
            return None
        else:
            search_for = search_term

        results = self.memory.search(search_for)

        json_results = []

        if results:
            for result in results:
                result_entry = {
                    "search_term": search_term,
                    "key": result['key'],
                    "parent": result['parent'],
                    "type": result['type'],
                    "snippets": []  # This will hold each highlighted snippet
                }

                parent = []
                header_text = Text.from_markup(
                    f"[bold bright_cyan]Key:[/bold bright_cyan] {result['key']}\n"
                    f"[bold bright_cyan]Parent:[/bold bright_cyan] {result['parent']}\n"
                    f"[bold bright_cyan]Type:[/bold bright_cyan] {result['type']}()\n"
                    f"[bold bright_cyan]Matched:[/bold bright_cyan] {search_term}\n"
                    )
                parent.append(header_text)

                # Loop through each snippet in the result
                for idx, snip in enumerate(result['snippets']):
                    snip = escape(snip.strip())
                    if len(snip) > 0:
                        if isinstance(search_for, re.Pattern):
                            highlighted_text = re.sub(
                                search_pattern,
                                f"[bold bright_green underline]\\g<0>[/bold bright_green underline]",
                                snip,
                                flags=re.IGNORECASE
                            )
                        else:
                            highlighted_text = re.sub(
                                re.escape(search_for),
                                f"[bold bright_green underline]{search_term}[/bold bright_green underline]",
                                snip,
                                flags=re.IGNORECASE
                            )

                        snippet = Text.from_markup(f"{highlighted_text.strip()}") 
                        parent.append(Padding(snippet, (1, 0, 1, 4), style="on grey15"))
                        parent.append(Text(""))

                        result_entry["snippets"].append(snip)

                parent.pop() 
                panel_group = Group(*parent)
                print(Panel(panel_group, title=f"Key: {result['key']}", padding=(1, 2)))

                if len(result_entry["snippets"]) > 0:
                    json_results.append(result_entry)
        else:
            console.log(f"No results for: {search_term}")
            return None

        return escape(json.dumps(json_results, indent=4)) 
