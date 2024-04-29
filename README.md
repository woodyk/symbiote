# Project: Symbiote



## Vision
Symbiote - an innovative personal data integration assistant that not only logs your life's milestones but also helps analyze your health, finances, personal behavior, and so much more. Symbiote creates a multi-generational legacy, allowing future generations to connect with their family's past like never before.

Imagine a world where you live beyond the constraints of time and space, where your experiences, knowledge, and wisdom are not lost but perpetuated and made accessible for generations. A world where your legacy is not just a collection of tangible assets, but an evolving digital tapestry of your life, enriched with your insights and personal growth.

In this world, your life's journey becomes an open book, not just for your descendants, but also for yourself. The lessons you've learned, the milestones you've achieved, and the adventures you've embarked on are at your fingertips, ready to be revisited or shared at any moment.

This is the world that Symbiote seeks to create. A world where each individual's life story becomes a part of an enduring digital heritage, shaping the wisdom of generations to come. Through Symbiote, we are not just remembering and preserving our past, but we are also forging a future that values the richness of human experience, the strength of shared knowledge, and the power of connected memories.

Welcome to the era where you are not just a fleeting moment in time, but a continuous, evolving narrative shaping the world one life story at a time. Welcome to Symbiote!

##### Author: Wadih Khairallah

## Donate:
BitCoin: 36Mg8UnAhVU5ZqSikQmbVXGG3rpYZRGNjC

## Running symbiote
```
brew install protobuf libmagic tesseract
python -m spacy download en_core_web_sm
python -m nltk.downloader vader_lexicon

# Ubuntu
apt-get install portaudio19-dev libmagic1 tesseract-ocr
virtualenv .venv
pip3 install -r requirements.txt
./app.py -i
pip3 install six --upgrade
```

Add the following with your API keys to your .bashrc
```
export GOOGLE_API_KEY="your_google_api_key_here"
export GOOGLE_CX="your_google_search_code_here"
export OPENAI_API_KEY="your_openai_api_key_here"
```
For linux support on ubuntu be sure to add your user to the 'input' group.

# ToDo
- Built in devops tool kit for interacting with the commands you run and configurations you create
- Create documentation and usage guide.
- Create usable demo cases.
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
- Create visual concept rendering capability for interacting with your ANNGL.  Visualize concepts in near real time.
- Model creation kit. Create and use personal AI models for specific functions.
- Tie in pathfinder concepts.
- Real time user monitoring that allows your symbiote to key off of actions you are performing.  Remember paper clip ;)


# Potential AI plugins
huggingface
claude.ai
perplexity.ai
mistral.ai
