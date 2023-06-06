#!/usr/bin/env python3
#
# speech_capture.py

import pyaudio
import pyttsx3
import speech_recognition as sr

class SymSpeech():
    def __init__(self, debug=False):
        self.debug = debug

        # Create a recognizer instance
        self.r = sr.Recognizer()

        # Keyword
        self.keywords = "symbiote"

        # initialize the pyttsx3 engine
        self.engine = pyttsx3.init()

    def keyword_listen(self):
        # Initialize PyAudio
        self.p = pyaudio.PyAudio()

        # Start the stream in non-blocking mode
        self.stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024, input_device_index=p.get_default_input_device_info()['index'], start=False)

        if self.debug:
            print("Listening...")

        data = b''
        mdata = b''
        while True:
            try:
                # Start the stream
                stream.start_stream()

                # Read a chunk from the stream
                data = stream.read(8000, exception_on_overflow = False)
                mdata = mdata + data


                # Use recognize_google to convert audio to text
                try:
                    # Convert the audio to text
                    text = r.recognize_google(sr.AudioData(mdata, sample_rate=16000, sample_width=2))
                    if self.debug:
                        print("Recognized: ", text)

                    # Check if the keyword is in the recognized text
                    if keyword.lower() in text.lower():
                        if self.debug:
                            print("Keyword detected!")

                        ready = "Symbiote here. How can I help you?"
                        self.say(ready)

                        # Stop the stream
                        stream.stop_stream()

                        self.listen(5)

                    mdata = b''

                except sr.UnknownValueError:
                    # Google Speech Recognition could not understand audio
                    print("Unknown Error")
                    pass
                except sr.RequestError as e:
                    # Could not request results from Google Speech Recognition service
                    print("Could not request results from Google Speech Recognition service; {0}".format(e))
            except IOError:
                pass

    def say(self, user_input):
        try:
            self.engine.say(user_input)
            self.engine.runAndWait()
        except:
            print("Unable to say text.")

    def listen(self, duration):
        with sr.Microphone() as source:
            if self.debug:
                print("Speak:")

            # read the audio data from the default microphone
            audio_data = r.record(source, duration=5)
            if self.debug:
                print("Recognizing...")

            # convert speech to text
            text = r.recognize_google(audio_data)
            if self.debug:
                print(text)

        return text
