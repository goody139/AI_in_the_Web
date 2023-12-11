# Containts parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_user import login_required, UserManager, UserMixin, current_user
from read_data import check_and_read_data
from helper_functions import create_links, get_movie_poster_links, movie_poster, create_tags, create_content
from models import User, Movie, MovieGenre, Rating, Link, Tag, db


# Running on http://127.0.0.1:5000/

#------------------ TODO LIST ------------------#
""" 
--> movie posters that could not be found / are still missing 

movie IDS :
keys = [128, 678, 791, 875, 979, 1107, 1423, 2851, 4051, 4207, 4568, 5069, 5209, 7646, 7669, 7762, 7841, 7842, 26453, 26587, 26614, 26649, 26693, 26761, 26849, 26887, 27002, 27036, 27251, 27611, 27708, 27751, 31193, 32294, 32600, 38198, 40697, 42602, 49917, 51024, 52281, 53883, 55207, 57772, 61406, 62336, 62970, 63433, 64167, 65135, 65359, 66544, 66934, 69524, 69849, 70521, 71160, 72982, 77177, 79299, 84847, 85780, 86237, 86487, 90647, 90945, 92475, 93008, 93040, 93988, 95717, 95738, 96471, 96518, 96520, 99532, 99764, 100044, 100553, 105250, 106642, 107780, 108727, 115111, 115969, 121035, 122260, 122926, 126430, 127180, 127390, 131724, 137859, 139130, 140481, 140737, 141816, 142115, 147250, 147328, 147330, 148675, 150548, 151763, 152284, 152711, 159817, 163809, 167570, 170705, 171011, 171495, 171749, 172497, 172825, 172909, 173535, 173873, 174053, 174403, 175693, 176329, 178129, 179135, 180263, 180777, 184257, 185135, 193579]
Einfach so lassen? Oder mit der Google API nocheinmal versuchen zu füllen? 
- wie timestaps händeln? : "wenn advanced recommender system benötigt" Thelen
- movielens anmeldung ?
- wenn rating gerated worden ist farbe ändern oder so? Oder sterne system
- Content auch von API accessen? und in Database speichern?
- Rating algorithm : 
    For a given user: 
        find similar values 
        for all objects that dont have a value yet predict 
        return recommendation 

    --> schauen, ob die gleichen filme hoch gerated werden, oder ähnliches genre ?! 
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

db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = UserManager(app, db, User)  # initialize Flask-User management



# Create all database tables if not initialized yet 
check_and_read_data(db)


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
    # so etwas zum sliden? 

    # bilder in html displayen für movie ID 

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
        Rating.rating_value >= 1,
        MovieGenre.genre == "Comedy", 
    ).limit(10).all()
    print(movies)

    # result list 
    MOVIEID, IMDB, TMBID = create_links(movies) 
    poster_links = movie_poster(movies)
    tags = create_tags(movies) 
    contents = create_content(movies) 

    result_list = zip(movies, MOVIEID, IMDB, TMBID, poster_links, tags, contents)

    return render_template("rating.html", movies=movies, movieid=MOVIEID, imdb=IMDB, tmbid=TMBID, results=result_list)

@app.route('/rate', methods=['POST'])
@login_required
def rate():
    if request.method == 'POST':

        # provide links for movie 
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


