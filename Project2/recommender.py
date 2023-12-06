# Containts parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

import csv
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_user import login_required, UserManager, UserMixin, current_user
from read_data import check_and_read_data
from models import db, User, Movie, MovieGenre, Rating


# Running on http://127.0.0.1:5000/

#------------------ TODO LIST ------------------#
""" 
- tags und links einfügen 
- wie timestaps händeln?
- csv einlesen und in sql einfügen (tags?)
- wenn rating gerated worden ist farbe ändern oder so? Oder sterne system
- README.html lesen 
- wenn man Link für Film anklickt kommt man zur Seite (Kann man schon bild displayen auf unserer Website?)
"""
#------------------ TODO LIST ------------------#


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///movie_recommender.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "Movie Recommender"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_USERNAME = True  # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = True  # Simplify register form


# Create Flask app load app.config
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')
app.app_context().push()

# Initialize Flask-SQLAlchemy
db = SQLAlchemy(app)

# Create all database tables
db.create_all()
check_and_read_data(db)

# Setup Flask-User and specify the User data-model
user_manager = UserManager(app, db, User)


# The Home page is accessible to anyone
@app.route('/')
def home_page():
    # render home.html template
    return render_template("home.html")

# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
@login_required  # User must be authenticated
def movies_page():
    # IDEE : zum anklicken machen - based on tags - (Your Genre! / Your artists! / Your Vibe!)

    user= current_user
    print(user.username)
    print(user.id)

    # all movies rated with 5.0 stars 
    ratings = Rating.query.filter(Rating.rating_value == 5)#.limit(10).all()
    Movie_ids = []
    for r in ratings:
        Movie_ids.append(r.movie_id)


    # Idee für genre button einrichten oder so? 

    # provides output for one user with a specific ranking and a specific genre
    movies = db.session.query(Movie).join(Rating).join(MovieGenre).filter(
        Rating.user_id == user.id,
        Rating.rating_value >= 4,
        MovieGenre.genre == "Thriller", 
    ).limit(10).all()

    return render_template("rating.html", movies=movies)

@app.route('/rate', methods=['POST'])
@login_required
def rate():
    if request.method == 'POST':
        #['ratings.id', 'ratings.user_id', 'ratings.movie_id', 'ratings.rating_value']
        #columns = Rating.__table__.columns
        #print(columns)

        movie_id = request.form.get('movie_id')
        rating_value = int(request.form.get('rating'))
        
        # Checking if rating for movie was already submitted 
        existing_rating = Rating.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
        
        # if yes update rating  
        if existing_rating: 
            existing_rating.rating_value = rating_value
            db.session.commit()   

        # if not create new entry 
        else:
            # Speichern Sie die Bewertung für den aktuellen Benutzer und den Film
            rating = Rating(user_id=current_user.id, movie_id=movie_id, rating_value=rating_value)
            db.session.add(rating)
            db.session.commit()            

        return "Bewertung erfolgreich gespeichert!"


# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)


