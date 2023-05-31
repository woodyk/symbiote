#!/usr/bin/env python3
#
# monitor.py

import io
import sys
import re
import threading
import time
import subprocess
import clipboard
from pynput.keyboard import Listener

class KeyLogger:
    def __init__(self, schat, debug=False):
        global chat_is_active
        self.schat = schat
        self.debug = debug
        chat_is_active = False
        self.lastlog = ""
        self.chat_is_active = chat_is_active 
        self.command = ["terminator", "-e"]
        self.totallog = ""
        self.previousclip = ""


        self.key_mapping = {
                "Key.enter": ' ',
                "Key.space": ' '
            }

        schat.chat(user_input="role:HELP_ROLE:", run=True)

    def pull_clipboard(self):
        # Pull clipboard contents
        clipboard_content = clipboard.paste()
        if clipboard_content != self.previousclip:
            self.previousclip = clipboard_content

    def on_press(self, key):
        self.pull_clipboard()
        register_ctrl = False

        if self.chat_is_active:
            return

        try:
            pressed = re.sub('\'', "", str(key))

            if re.search(r'^Key\..*', pressed):
                if pressed in self.key_mapping:
                    pressed = self.key_mapping[pressed]
                elif re.search(r'^Key\.backspace', pressed):
                    self.lastlog = self.lastlog[:-1]
                    pressed = ""
                elif pressed == "Key.ctrl":
                    pass
                else:
                    pressed = ""

            if self.debug:
                print(pressed, end="")

            self.lastlog += pressed 

        except AttributeError:
            print("Unable to capture key.")

        if re.search(r":help::|Key\.ctrlh", self.lastlog):
            print("Help menu triggered")
            self.lastlog = re.sub(r':help::|Key.ctrlh', '', self.lastlog)
            self.chat_is_active = True
            issue_command = f'symbiote -q "{self.lastlog}"'
            self.command.append(issue_command)

            process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

            while process.poll() is None:
                time.sleep(1)

            self.command.pop()
            self.chat_is_active = False
            self.totallog += self.lastlog
            self.lastlog = ""  # reset the log

    def start(self):
        listener = Listener(on_press=self.on_press)
        self.t = threading.Thread(target=listener.start)
        self.t.start()

