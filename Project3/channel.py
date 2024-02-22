## channel.py - a simple message channel
##

from flask import Flask, request, render_template, jsonify
import json
import requests
from hangman import Hangman
import datetime
import re 
import random
import pygame 

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db


CHANNEL_AUTHKEY = '3790124726'
CHANNEL_NAME = "Hangman Channel"
CHANNEL_ENDPOINT = "http://localhost:5001" # don't forget to adjust in the bottom of the file
CHANNEL_FILE = 'messages.json'

HUB_AUTHKEY = 'Crr-K3d-2N'
HUB_URL = 'http://temporary-server.de'

GAME = Hangman()
COUNT = 0 

@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # send a POST request to server /channels
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             data=json.dumps({
            "name": CHANNEL_NAME,
            "endpoint": CHANNEL_ENDPOINT,
            "authkey": CHANNEL_AUTHKEY}))
    
    if response.status_code != 200:
        print("Error creating channel: "+str(response.status_code))
        return

def check_authorization(request):
    global CHANNEL_AUTHKEY
    # check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    global CHANNEL_NAME
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME}),  200
 
# GET: Return list of messages
@app.route('/', methods=['GET'])
def home_page():
    global COUNT 

    if not check_authorization(request):
        return "Invalid authorization", 400
    
    if COUNT == 0: 
        COUNT += 1
        send_bot_message("Hey let's play hangman! Write @hangman to play.", True)


    # fetch channels from server
    return jsonify(read_messages())
     

def send_bot_message(message, clear=False): 
    if message == None: 
        return 0 

    game_message = {
    "content": message,
    "sender": "Hangmanbot",
    "color" : "rgb(192, 40, 247)",
    "timestamp": datetime.datetime.now().isoformat()
    }
    
    print(game_message)
    if clear == True: 
        messages = []
    else: 
        messages = read_messages()

    messages.append({'content':game_message['content'], 'sender':game_message['sender'], 'color':game_message['color'], 'timestamp':game_message['timestamp']})
    save_messages(messages)  
    play_sound()
 

# Exception Handling
def guess_exceptions(guess):   
    match guess: 
        case str() if guess.isalpha() and len(guess) == 1:
            return 0, random.choice(["Mh let's see if that's correct...", "I'll check for your guess...", "Give me a second...", None, None, None])
        case str() if bool(re.search(r"\s", guess)) and bool(g.isalpha() for g in guess): 
            return -1, random.choice(["Give me one word that you guess is the final word, or one character.", "Is this your first time playing Hangman? Type in a word or a character.", "Only one character or word is possible.", "Oh wow okay. I can't handle all of it at once. Give me only one character or word please.", "Hey! The game is not fun this way. Give me one character or one word."])
        case str() if guess.isalnum() and guess.isalpha(): 
            return 1, random.choice(["Let's see if your word is correct.", "Are you nervous?", "*Drum roll*", "Mh interesting choice...", "Nice try!", None, None, None])
        case str() if guess.isnumeric(): 
            return -1, random.choice (["Write characters or words, not numbers", "This is not a number guessing game, but a word guessing game. Please enter characters or words.", "Is this a joke? Numbers are not part of the word"])
        case int(): 
            return -1, random.choice(["Write characters or words, not numbers", "This is not a number guessing game, but a word guessing game. Please enter characters or words.", "Is this a joke? Numbers are not part of the word"])
        case str() if any(char in "!?=()\{\}$§`°;.:-_ÄÖÜ@''\"\"/&%#+~*<>," for char in guess):
            return -1, random.choice(["What? This is definitely not part of a word. Write a character or a word.", "I do not understand u. Use a proper language please.", "Is this a joke? Special characters are safely not part of the word.", "Is it so hard to write one character or one word?"])
        case None : 
            return -1, "Please use something meaningful inputs like one character or one word."
        case str() if guess == " ": 
            return -1, "Please use something meaningful inputs like one character or one word."
        case _ : 
            return -1, "Please use something meaningful inputs like one character or one word."


def play_sound():
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    pygame.mixer.music.load("Message_sound.mp3")
    pygame.mixer.music.play()

def save_game_starter(game_starter): 
    with open("game_starter.txt", "w") as file:
        file.write(game_starter)

def get_game_starter(): 
    file_content = ""

    # Open the file in read mode
    with open("game_starter.txt", "r") as file:
        # Read each line of the file and append it to the file_content string
        for line in file:
            file_content += line

    # Return the file content as a string
    return file_content

# POST: Send a message
@app.route('/', methods=['POST'])
def send_message(): 

    print("CHANNEL POST")
    global GAME
    # fetch channels from server
    # check authorization header
    if not check_authorization(request):
        return "Invalid authorization", 400
    # check if message is present
    message = request.json
    print("THIS IS THE MESSAGE", message)
    if not message:
        return "No message", 400
    if not 'content' in message:
        return "No content", 400
    # if not 'color' in message: 
    #     return "No color", 400
    if not 'sender' in message:
        return "No sender", 400
    if not 'timestamp' in message:
        return "No timestamp", 400
    
    # add message to messages
    messages = read_messages()
    messages.append({'content':message['content'], 'sender':message['sender'], 'color':message['color'], 'timestamp':message['timestamp']})
    save_messages(messages)
    play_sound()


    if is_ingame(GAME) == True and message['sender'] == get_game_starter(): 
        print(message['content'], GAME.guessed_letters)
        if message['content'] in GAME.guessed_letters: 
            send_bot_message('You already tried this guess. Try another.')       
        
        else: 
            # Exception handling 
            state, mess = guess_exceptions(message['content'])
            if  message['content'] == "@surrender" or message['content'] == "@hangman" :
                pass 
            else: 
                send_bot_message(mess)

            # Update values and give user feedback
            guessed_letter = [*message['content']]
            feedback = GAME.update_values(guessed_letter, state)
            if feedback == 1:
                send_bot_message("That word was not correct.") 

            send_bot_message(GAME.masked_word)

            surrender = False 
            # check for surrender 
            if message['content'] == "@surrender" :
                send_bot_message(random.choice(["Muhahahaha, you lost. :D ", "In the END it doesn't even matter. You tried so hard, to loose it all xD", "Flames to dust, Lovers to friends : Why do all good things come to an end?", "Well, my friend you gotta say. I won't play I won't play with y no way-ay-ay-ay. Na-na why don't u get a win?", "You want to be tough, better do what you can so beat it - but you are just too bad! So you beat it(beat it) beat it (beat it)! Now you are defeated.", "Tonight, I'm gonna have myself a real good time I feel alive. And the world is turning inside out, yeah, I'm floating around in ecstacy BUT you stop the game now :( !" ]))
                surrender = True

            # Win or loose condition 
            print(GAME.update_game_state(surrender))
            end, final_message = GAME.update_game_state(surrender)   
            if final_message is not None or surrender == True : 
                send_bot_message(final_message)
                if end == True : 
                    GAME = Hangman()

    elif is_ingame(GAME) == True and not (message['sender'] == get_game_starter()): 
        send_bot_message(random.choice(["Please wait until " + get_game_starter() + " finished the game. Afterwards you can start a new game with the @hangman command :).", "You can't start a game since "+get_game_starter()+ " is still in a game. What until the game is finished.", "There is already one game ongoing, so another can't be started. Be patient please until the game is finished.", "Thanks for your input here, but "+ get_game_starter() +"is currently in a game. Wait until the game is over.", "Quick note: Your messages are not recognized, because " + get_game_starter()+ "is currently playing a game. Wait until the game is over and you can start your own game.", "Please don't distract "+ get_game_starter()+ " when playing the game!"]))

    elif is_ingame(GAME) == False: 
        
        # Start game 
        if message['content'] == "@hangman":
            GAME.start()
            print(GAME.word)
            save_game_starter(message['sender'])
            send_bot_message("Okay, let's start! The word u have to guess is : "+ GAME.masked_word) 

        if message['content'] == "@surrender" :
            send_bot_message("You haven't even started a game yet that u can surrender! Type in @hangman to start a game.")  


    return "OK", 200

def is_ingame(game):
    return game.ingame 

def read_messages():
    global CHANNEL_FILE
    try:
        f = open(CHANNEL_FILE, 'r')
    except FileNotFoundError:
        return []
    try:
        messages = json.load(f)
    except json.decoder.JSONDecodeError:
        messages = []
    f.close()
    return messages

def save_messages(messages):
    global CHANNEL_FILE
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f) 

def update_messages(user, color, indices): 
    # JSON MESSAGES 
    messages = read_messages()

    for i in range(0,len(messages)): 
        if i in indices: 
            print(messages[i]['content'])
            messages[i]['sender'] = user
            messages[i]['color'] = color

    save_messages(messages)      

# Start development web server
if __name__ == '__main__':
    app.run(port=5001, debug=True)
