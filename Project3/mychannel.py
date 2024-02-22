## channel.py - a simple message channel
##

from flask import Flask, request, render_template, jsonify
import json
import requests
import datetime
import numpy as np

from game import TicTacToeGame

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

HUB_URL = 'http://localhost:5555'
HUB_AUTHKEY = '1234567890'

# HUB_AUTHKEY = 'Crr-K3d-2N'
# HUB_URL = 'http://temporary-server.de'

CHANNEL_AUTHKEY = '0987654321'
CHANNEL_NAME = "Tic-tac-toe Channel"
CHANNEL_ENDPOINT = "http://localhost:5001" # don't forget to adjust in the bottom of the file
CHANNEL_FILE = CHANNEL_NAME+'messages.json'

ttt_game = TicTacToeGame()

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
    if not check_authorization(request):
        return "Invalid authorization", 400
    # fetch channels from server
    return jsonify(read_messages())

# POST: Send a message
@app.route('/', methods=['POST'])
def send_message():
    # fetch channels from server
    # check authorization header
    if not check_authorization(request):
        return "Invalid authorization", 400
    # check if message is present
    message = request.json
    if not message:
        return "No message", 400
    if not 'content' in message:
        return "No content", 400
    if not 'sender' in message:
        return "No sender", 400
    if not 'timestamp' in message:
        return "No timestamp", 400
    # add message to messages
    messages = read_messages()
    messages.append({'content':message['content'], 'sender':message['sender'], 'timestamp':message['timestamp']})
    bot_message(message, messages)
    save_messages(messages)
    return "OK", 200

def bot_message_1(message, messages):
    # respond to messages
    BOT_NAME = "Welcome_Bot"
    content = "Hello {}".format(message['sender'])
    messages.append({'content':content, 'sender':BOT_NAME, 'timestamp':datetime.datetime.now().isoformat()})
    save_messages(messages)
    return messages



         
def bot_message(message, messages):
    # respond to messages
    # tic-tac-toe
    # [TODO] commands: start new game, 
    #    game options: - symbol of first player / starting player
    #                  - 1 or two player game
    #                  - easy/hard mode (bot playing optimal strategy)
    
    

    # by default, bot has x symbol and player starts

    if message['content'].startswith("/ttt"):
        print("parsing message for ttt bot")
        c=""
        if "-h" in message['content'] or "--help" in message['content']:
            c += ttt_game.print_help()

        
        try:
            c += ttt_game.parse_message(message['content'][4:], message['sender'])
        except ValueError as e:
            c += str(e)
        except SystemExit as e:
            c += str(e)
        BOT_NAME = "Tic-tac-toe_Bot"
        messages.append({'content':c, 'sender':BOT_NAME, 'timestamp':datetime.datetime.now().isoformat()})
        save_messages(messages)

    return messages


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

# Start development web server
if __name__ == '__main__':
    app.run(port=5001, debug=True)
