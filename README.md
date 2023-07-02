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
- Add scheduled checking ability. Look for change in file or on api result and provide a response.
- Create switch for processing audio during indexing.
- Make listen mode possible at the same time as interactive mode.
- Repair monitor mode window launch
- Add ability to recognize file paths or urls in copy buffer or entered text to interact with remote data.
- Add ability to pipe data into symbiote.
- Work on bottom toolbar with prompt_toolkit
- Create class for pull_content() function
- Handle ctrl-c in shell to stop a command not exit the shell
- The command properly when writing commandline scripts. Take into account the shells multi line command option.
- Take into account shell history when parsing symshell commands. When up arrow is used with a command:: keyword it is unrecognized.
- Add the ability to write, execute and read code output.
- Add embeddings capabilites. Use embeddings for custom searches across data sets.
- Token / Pricing history: Create a running total on pricing even after symbiote has been closed and reopened.
- Create pandas wrapper to do data manipulation on the command line.
- Add decay time to the conversation_percent.  Set the conversation_percent high for data consumption and decay over time until the consumption keywords are used again.
- Add self destruct and encryption options.
- Add hooks for alternate AI eg: ai21.com, 
- Begin comprehensive documentation on the use of symbiote.
- Create diy ai model builder for personal AI model creation.
- Intent capability.  Build in functionality that understands the intent of the data being used based on the user.
- Come up with proper adoption process for a users A.N.N.G.L.  Ensure that the users intent is good based off truth.
