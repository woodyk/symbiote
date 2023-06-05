#!/usr/bin/env python3
#
# speech_capture.py

import pyaudio
import speech_recognition as sr

class SymSpeech():
    def __init__(self, dbug=False):
        # Create a recognizer instance
        self.r = sr.Recognizer()

        # Initialize PyAudio
        self.p = pyaudio.PyAudio()

        # Keyword
        self.keywords = "symbiote"

        # Start the stream in non-blocking mode
        self.stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024, input_device_index=p.get_default_input_device_info()['index'], start=False)

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

                # Stop the stream
                #stream.stop_stream()

                # Use recognize_google to convert audio to text
                try:
                    # Convert the audio to text
                    text = r.recognize_google(sr.AudioData(mdata, sample_rate=16000, sample_width=2))
                    print("Recognized: ", text)

                    # Check if the keyword is in the recognized text
                    if keyword.lower() in text.lower():
                        print("Keyword detected!")
                        # Execute your code here

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
