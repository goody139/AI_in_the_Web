# Containts parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html
#
# This file contains an example Flask-User application.
# To keep the example simple, we are applying some unusual techniques:
# - Placing everything in one file
# - Using class-based configuration (instead of file-based configuration)

import csv
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_user import login_required, UserManager, UserMixin, current_user

# Running on http://127.0.0.1:5000/

#------------------ TODO LIST ------------------#
""" 
- Rankings der User accessen und selection von movies anzeigen lassen 
- auf Github pushen und mit Hannah organisieren / besprechen 
- vermutlich ratings von csv file benutzen und einfügen? oder beispiel?
- wie timestaps händeln?
- csv einlesen und in sql einfügen (ratings und tags)
- wenn gerated worden ist farbe ändern oder so? Oder sterne system
- README.html lesen 
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

# Define the User data-model.
# NB: Make sure to add flask_user UserMixin as this adds additional fields and properties required by Flask-User
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    username = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    email_confirmed_at = db.Column(db.DateTime())

    # User information
    first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
    genres = db.relationship('MovieGenre', backref='movie', lazy=True)

class MovieGenre(db.Model):
    __tablename__ = 'movie_genres'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    genre = db.Column(db.String(255), nullable=False, server_default='')

""" Save Ratings """
class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'))
    rating_value = db.Column(db.Integer)


def check_and_read_data(db):
    # check if we have movies in the database
    # read data if database is empty
    if Movie.query.count() == 0:
        # read movies from csv
        with open('data/movies.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        id = row[0]
                        title = row[1]
                        movie = Movie(id=id, title=title)
                        db.session.add(movie)
                        genres = row[2].split('|')  # genres is a list of genres
                        for genre in genres:  # add each genre to the movie_genre table
                            movie_genre = MovieGenre(movie_id=id, genre=genre)
                            db.session.add(movie_genre)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movies read")

    # Rating daten einlesen 
    if Rating.query.count() == 0:
        with open('data/ratings.csv', newline='', encoding='utf8') as csvfile:
            # my code
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    # userId,movieId,rating,timestamp
                    # UserID, movieID, ratingValue
                    try:
                        userID = row[0]
                        movieID = row[1]
                        ratingValue = row[2]
                        ratings = Rating(user_id=userID, movie_id=movieID, rating_value=ratingValue)
                        db.session.add(ratings)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " ratings read")

    # für filme auch tags einlesen? wenn film gerated mit tag auch andere filme mit tag anzeigen? 

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
    # String-based templates

    user= current_user

    print(user.username)
    print(user.id)

    # first 10 movies
    movies = Movie.query.limit(10).all()

    # only Romance movies
    movies = Movie.query.filter(Movie.genres.any(MovieGenre.genre == 'Horror')).limit(10).all()

    # only Romance AND Horror movies
    # movies = Movie.query\
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Romance')) \
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Horror')) \
    #     .limit(10).all()

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


