#!/usr/bin/env python3
#
# speech.py

import os
import time
import subprocess
import tempfile
import threading
import pyaudio
import speech_recognition as sr
from gtts import gTTS

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

class SymSpeech():
    def __init__(self, monitor=False, debug=False):
        self.monitor = monitor 
        self.debug = debug

        # Create a recognizer instance
        self.r = sr.Recognizer()

        # Keyword
        self.keywords = [ 
                    "symbiote",
                    "help",
                    "someone",
                    "bob"
                    ]

    def start_keyword_listen(self):
        t = threading.Thread(target=self.keyword_listen)
        t.start()
        return True

    def stop_keyword_listen(self):
        self.stop_listening.set()

    def keyword_listen(self):
        # Initialize PyAudio
        p = pyaudio.PyAudio()

        # Start the stream in non-blocking mode
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024, input_device_index=p.get_default_input_device_info()['index'], start=False)

        if self.debug:
            print("Listening...")

        text = ''
        data = b''

        while True:
            try:
                # Start the stream
                stream.start_stream()

                # Read a chunk from the stream
                data += stream.read(8000, exception_on_overflow = False)

                if len(data) > 100000:
                    data = b''
                    continue

                # Use recognize_google to convert audio to text
                try:
                    # Convert the audio to text
                    text = self.r.recognize_google(sr.AudioData(data, sample_rate=16000, sample_width=2))
                except sr.UnknownValueError:
                    # Google Speech Recognition could not understand audio
                    continue
                except sr.RequestError as e:
                    # Could not request results from Google Speech Recognition service
                    print("Could not request results from Google Speech Recognition service; {0}".format(e))
                    return False

            except IOError:
                pass

            if self.debug:
                if len(text) > 0:
                    print("Recognized: ", text)

            # Check if the keyword is in the recognized text
            for keyword in self.keywords:
                if keyword.lower() in text.lower():
                    data = b''
                    # Stop the stream
                    stream.stop_stream()

                    if self.debug:
                        print("Keyword detected!")

                    ready = "Yes?"
                    self.say(ready)
                    recorded = self.listen(5)

                    if recorded is None:
                        break

                    if self.monitor:
                        self.launch_window(recorded)
                    else:
                        return recorded

            text = '' 

    def say(self, say_message):
        try:
            text_to_speech = gTTS(text=say_message)
        except:
            print("Unable to get text to speech.")
            return

        # save the speech audio into a file
        with tempfile.NamedTemporaryFile(delete=True) as fp:
            tempfile_path = f"{fp.name}.mp3"

        text_to_speech.save(tempfile_path)

        # play the audio file
        pygame.mixer.init()
        pygame.mixer.music.load(tempfile_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy() == True:
            continue

        os.remove(tempfile_path)

    def listen(self, duration):
        request_text = str()
        with sr.Microphone() as source:
            if self.debug:
                print("Speak:")

            # read the audio data from the default microphone
            audio_data = self.r.record(source, duration=5)
            if self.debug:
                print("Recognizing...")

            # convert speech to text
            try:
                request_text = self.r.recognize_google(audio_data)
            except:
                # Google Speech Recognition could not understand audio
                requested_text = None 

            if self.debug:
                print(request_text)

            if len(request_text) < 4:
                request_text = None

            return request_text


    def launch_window(self, content):
        command = ["terminator", "-e"]
        issue_command = f'symbiote -q "{content}" -e'
        command.append(issue_command)

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        while process.poll() is None:
            time.sleep(1)

        if self.debug:
            print("Terminal closed.")

        return
