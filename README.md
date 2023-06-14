# Symbiote AI Harness

##### Author: Wadih Khairallah


## Running symbiote
```
brew install libmagic tesseract
python -m spacy download en_core_web_sm
python -m nltk.downloader vader_lexicon

# Ubuntu
apt-get install portaudio19-dev libmagic1 tesseract-ocr
virtualenv .venv
pip3 install . 
```

For linux support on ubuntu be sure to add your user to the 'input' group.

# ToDo
- Add reindex option to summary.
- Create switch for processing audio during indexing.
- Make listen mode possible at the same time as interactive mode.
- Repair monitor mode window launch
- Add ability to recognize file paths or urls in copy buffer or entered text to interact with remote data.
- Add ability to pipe data into symbiote.
- Work on bottom toolbar with prompt_toolkit
- Retrofit prompt_toolkit instead of InquiererPy
- Create class for pull_content() function
- Add stop:: functionality to chat output.
- Handle ctrl-c in shell to stop a command not exit the shell
- Add command keyword auto completion
- Add tab completion to symchat shell
- The command properly when writing commandline scripts. Take into account the shells multi line command option.
- Work on live_mode.
- Add base64 function to push binary data to openai
- Take into account shell history when parsing symshell commands. When up arrow is used with a command:: keyword it is unrecognized.
- Add the ability to write, execute and read code output.
- Add completion mode vs chatCompletion
- Add the ability to change the openai settings within the shell
- Add embeddings capabilites. Use embeddings for custom searches across data sets.
- Add per minute token rate counter to the tool bar.
- Token / Pricing history: Create a running total on pricing even after symbiote has been closed and reopened.
- Create dynamic max_token and conversation % when dealing with large data injections.
- Create pandas wrapper to do data manipulation on the command line.
- Add decay time to the conversation_percent.  Set the conversation_percent high for data consumption and decay over time until the consumption keywords are used again.
- Add self destruct and encryption options.
