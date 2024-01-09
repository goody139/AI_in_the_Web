# Containts parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

from flask import Flask, render_template, request
from flask_user import login_required, UserManager, current_user
from read_data import check_and_read_data
from helper_functions import *
from models import *
import pandas as pd
import random

# Running on http://127.0.0.1:5000/



class ConfigClass(object):
    """ Flask application config """

    # FLASK
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # FLASK SQALCHEMY 
    SQLALCHEMY_DATABASE_URI = 'sqlite:///movie_recommender.sqlite' 
    SQLALCHEMY_TRACK_MODIFICATIONS = False 

    # FLASK-USER 
    USER_APP_NAME = "MADVISOR - Your Movie Advisor"
    USER_ENABLE_EMAIL = False  
    USER_ENABLE_USERNAME = True  
    USER_REQUIRE_RETYPE_PASSWORD = True  


# CREATE FLASK APP 
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')
app.app_context().push()

db.init_app(app) 
db.create_all()  
user_manager = UserManager(app, db, User) 

# CREATE DATABASE 
check_and_read_data(db)


@app.route('/')
def home_page():
    """ Home page """
    return render_template("home.html")

@app.route('/FavMov')
def fav_mov_page():
    """ Favorite Movies """
    faves = get_fav_movies(current_user.id)
    movies= get_movies(faves)
    _, _, _, result_list, _ = prepare_movie_template(movies, current_user.id)
    return render_template("fav_movies.html", user_id= current_user.id, movies=movies, results=result_list, faves=faves)

@app.route('/movies')
@login_required 
def movies_page():
    """ Movies page """
    
    # DEFAULT -- 10 best rated movies with random genre 
    genre_list = genre_list = ['Action', 'Adventure', 'Animation', 'Children', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western', 'Other']
    #movies = filter_best([], random.choice(genre_list), 10, db, include=False, user_id=current_user.id)
    movies, scores = build_recommender(genre=[random.choice(genre_list)], tag=None, algo="Best rated movies", number=10, user_id="off", include="", db=db)
    faves, tag_list, genre_list, result_list, title_list = prepare_movie_template(movies, current_user.id, scores)

    return render_template("movies.html", user_id= current_user.id, tag_list= tag_list, genre_list= genre_list, title_list=title_list, results=result_list, faves=faves)

@app.route('/recommend', methods=['POST'])
@login_required
def recomend():
    """ Recommendation functionality """

    if request.method == 'POST':
        
        # GET filter options 
        user_id = request.form.get('user_id')
        tag = request.form.get('tag')
        genre = request.form.get('genre')
        number = request.form.get('number')
        algorithm = request.form.get('algorithm')
        include = request.form.get('include')

        # ADAPT values to python 
        filter_options = [genre, tag]

        for i in range(0, len(filter_options)): 

            # Nothing 
            if filter_options[i] == "0": 
                filter_options[i]= []

            # Several
            elif ',' in filter_options[i]: 
                filter_options[i] = filter_options[i].split(',')

            # Single  
            else: 
               filter_options[i] = [ filter_options[i] ]


        # EXCEPTIONS 
        if number == "0": 
            number = 10

        if genre == "other": 
            filter_options[0] = "(no genres listed)"

        
        # BUILD model  
        movies, normalized_scores = build_recommender(genre=filter_options[0], tag=filter_options[1], algo=algorithm, number= int(number), include=include, db=db, user_id=int(user_id))  
        faves, tag_list, genre_list, result_list, title_list = prepare_movie_template(movies, user_id, normalized_scores)

        print("FINISHED")
        return render_template("movies_content.html", tag_list= tag_list, genre_list= genre_list, title_list=title_list, movies=movies, results=result_list, faves=faves)

@app.route('/rate', methods=['POST'])
@login_required
def rate():
    """ Rating functionality """

    if request.method == 'POST':

        # PROVIDE Links
        movie_id = request.form.get('movie_id')
        rating_value = int(request.form.get('rating'))
      
        # CHECK : Rating already submitted? 
        existing_rating = Rating.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
        
        # If yes, update Rating 
        if existing_rating: 
            existing_rating.rating_value = rating_value
            db.session.commit()   

        # Else create new entry 
        else:
            rating = Rating(user_id=current_user.id, movie_id=movie_id, rating_value=rating_value)
            db.session.add(rating)
            db.session.commit()            

        return "Bewertung erfolgreich gespeichert!"

@app.route('/like', methods=['POST'])
@login_required
def like():
    """ Like functionality """

    # CHECK : Like already in database?
    movie_id = request.form.get('movie_id')
    existing_like= Favorite.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    
    # If no, CREATE new database entry 
    if existing_like == None: 
        new_like = Favorite(user_id=current_user.id, movie_id= movie_id, favorite_movie=True)
        db.session.add(new_like)
        db.session.commit()

    # UNLIKE  
    elif existing_like.favorite_movie == True: 
        print("UNLIKE MOVIE ")
        existing_like.favorite_movie = False
        db.session.commit()
 
    # LIKE  
    elif existing_like.favorite_movie == False: 
        print("LIKE MOVIE")
        existing_like.favorite_movie = True
        db.session.commit()     

    return "movie liked or unliked successfully"

@app.route('/predict/<user_id>/<movie_id>')
def predict(user_id, movie_id):
    # Load user and movie data from the database (replace 'users' and 'movies' with your actual table names)
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()

    cursor.execute("SELECT * FROM movies WHERE movie_id = ?", (movie_id,))
    movie_data = cursor.fetchone()

    if user_data is None or movie_data is None:
        return "User or movie not found"

    # Prepare data for prediction
    user = user_data[0]  # Replace with the actual user data extraction logic
    item = movie_data[0]  # Replace with the actual movie data extraction logic

    # Make a prediction
    prediction = model.predict(user, item)

    # Assuming prediction is a rating, convert it to a probability (replace this logic with your own)
    probability = (prediction + 1) / 2 * 100  # Example

    return f"The predicted probability that user {user_id} likes movie {movie_id} is: {probability:.2f}%"

# START SERVER 
if __name__ == '__main__':
    app.run(port=5000, debug=True)


