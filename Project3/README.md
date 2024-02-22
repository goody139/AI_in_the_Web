# AI_in_the_Web
Tobias Thelen 
University Osnabrück
Winter term 2023 

## Project 2: Build a movie Recommender system 
This repository is meant to provide our solution for project 3. 
The project is deployed on one of the servers provided for the course and reachable [through this link from within the university network](INSERT YOUR LINK HERE)


### Authors 
Hannah Köster & Lisa Golla 

### Task 
 Build an interesting channel for the distributed message board
  - Implement some chatbot for your channel, i.e. messages will not only be provided by users but also generated automatically
  - It's totally up to you to come up with some interesting ideas
  - Possible Examples:
      - Guessing games
      - ELIZA style chatbot
      - Calculation bot - try to interpret input as a calculation task
      - Service bot - provide some kind of statistics about the input
  - Design a fancy client 

### File Structure 
In the Project3 Folder the .py files for the hub, channels and client can be found as well as the requirements.txt file. The hangman.py file contains a class which handles the hangman game. Also there is a mp3 sound file, for a message sound, as well as a game_starter.txt file, where the current game starter user is saved. The messages and replayScript json files contain all the messages that have been sent in the chat. Finally there is the chat_server.sqlite file saving the current channels that are registered.

### Usage 
Navigate to the Project3 Folder and run: *python hub.py* , after that *python channel.py* , then *flask -app channel.py register* (do this for all channels), then finally *python client.py*. If you haven't done so yet, when running the code for the first time you need to run *nltk.download('words')* to access the words in your code.

### Hint 
We use the library pygame to play a sound when messages are sent and the re library to handle not allowed inputs from the user. For the hangman game we sample randomly words from the nltk.corpus that should be guessed. The Message_sound.mp3 is token with a free licence from https://pixabay.com/sound-effects/search/messaging/.

### Features 

   - Chatbot for 2 channels
   - Hangman game
   - Tik Tak Toe game
   - Message sound
   - Fancy designed client
   - Pop up window to decide color and name for a user connected to a cookie 

### Preview 
![m]()

