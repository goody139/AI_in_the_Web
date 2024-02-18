from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
import datetime
import requests

db = SQLAlchemy()

# Define the User data-model.
# NB: Make sure to add flask_user UserMixin as this adds additional fields and properties required by Flask-User
class Channel(db.Model):
    __tablename__ = 'channels'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')
    name = db.Column(db.String(100, collation='NOCASE'), nullable=False)
    endpoint = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
    authkey =  db.Column(db.String(100, collation='NOCASE'), nullable=False)
    last_heartbeat = db.Column(db.DateTime(), nullable=True, server_default=None)

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///chat_server.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning


# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary

SERVER_AUTHKEY = '1234567890'



# The Home page is accessible to anyone
@app.route('/')
def home_page():
    # render home.html template
    channels = Channel.query.all()
    return render_template("home.html")


def health_check(endpoint, authkey):
    # make GET request to URL
    # add authkey to request header
    response = requests.get(endpoint+'/health', headers={'Authorization': 'authkey '+authkey})
    if response.status_code != 200:
        return False
    # TODO: check payload
    return True


# Flask REST route for POST to /channels
@app.route('/channels', methods=['POST'])
def create_channel():
    print("post channels")
    global SERVER_AUTHKEY

    record = json.loads(request.data)

    # check if authorization header is present
    if 'Authorization' not in request.headers:
        return "No authorization header", 400
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + SERVER_AUTHKEY:
        return "Invalid authorization header ({})".format(request.headers['Authorization']), 400
    if 'name' not in record:
        return "Record has no name", 400
    if 'endpoint' not in record:
        return "Record has no endpoint", 400
    if 'authkey' not in record:
        return "Record has no authkey", 400
    if not health_check(record['endpoint'], record['authkey']):
        return "Channel is not healthy", 400

    update_channel = Channel.query.filter_by(endpoint=record['endpoint']).first()
    print("TTTTTTHIIIIIIIIIISSSSSSSSSSSS iis update channel", update_channel)
    if update_channel:  # Channel already exists, update it
        update_channel.name = record['name']
        update_channel.HUB_AUTHKEY = record['authkey']
        update_channel.active = False
        db.session.commit()
        if not health_check(record['endpoint'], record['authkey']):
            return "Channel is not healthy", 400
        return  jsonify(created=False, id=update_channel.id), 200
    else:
        channel = Channel(name=record['name'], endpoint=record['endpoint'], authkey=record['authkey'],
                      last_heartbeat=datetime.datetime.now(), active=True)
        db.session.add(channel)
        db.session.commit()

        return jsonify(created=True, id=channel.id), 200


@app.route('/channels', methods=['GET'])
def get_channels():
    channels = Channel.query.all()
    return jsonify(channels=[{'name':c.name, 'endpoint':c.endpoint, 'authkey':c.authkey} for c in channels]), 200



# Start development web server
if __name__ == '__main__':
    app.run(port=5555, debug=True)
