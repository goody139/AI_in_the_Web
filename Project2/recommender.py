#-------------------------- IMPORT ---------------------------------#
# Flask
from flask import Flask, render_template, request
from flask_user import login_required, UserManager, current_user
from sqlalchemy import func, desc, select
from jinja_markdown2 import MarkdownExtension

# Own files 
from models import *
from helper_functions import *
from read_data import check_and_read_data

# Python 
import time
import numpy as np
import pandas as pd
import concurrent
import os
import requests
import random

# Lenskit
from lenskit.algorithms import basic, als, bias
from lenskit.algorithms.user_knn import UserUser

# # Whoosh library 
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser, OrGroup
from whoosh import index, scoring
#-------------------------------------------------------------------#

"""
Recommender Script

Author: Hannah KÃ¶ster & Lisa Golla
University Course: AI in the Web
Date: 19.1.2024

Description:
This Python script contains all the functionalities for the Flask App "MADvisor". This App recommends and filters 
movies. 

Usage:
python recommender.py 

Dependencies:
Can be found in the requirements.txt file of the github repository : https://github.com/goody139/AI_in_the_Web/Project2

Note:
This code contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html
and uses and TMDB API. An API key is required.

The following features are implemented 
    - Watchlist (Favorite Movies)
    - Prediction how much a user likes a movie 
    - Several types of recommendation algorithms 
    - A filter method for movies (Genre, Tag, searchbar(description, title, reviews, tag), recommendation algorithm)
    - Apply a descending / ascending order based on certain values (runtime, average rating, title, match)
    - A Rating functionality 
    - Display information of movies (movie-poster, links to movie, runtime, description, reviews, average rating)
    - A view for one movie in detail (youtube videos, similar movies)
    - A rated movies & recommendation overview display 

"""

# APP CONFIGURATION 
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///movie_recommender.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "MADvisor"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_USERNAME = True  # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = True  # Simplify register form
    USER_AFTER_REGISTER_ENDPOINT = 'home_page'
    USER_AFTER_CONFIRM_ENDPOINT = 'home_page'
    USER_AFTER_LOGIN_ENDPOINT = 'home_page'
    USER_AFTER_LOGOUT_ENDPOINT = 'home_page'


# CREATE FLASK APP 
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  
app.app_context().push()  
db.init_app(app)  
db.create_all()  
user_manager = UserManager(app, db, User)  

# FIT ALL MODELS BEFORE STARTING APP 
try:
    model_popular, model_bias, model_user_user, model_item_item, model_implicit_mf, model_random, algos = fit_models()
    model_dict = {"Recommended for you":model_implicit_mf, "Other users also liked":model_user_user, "Based on the movies you liked":model_item_item, "Most popular":model_popular}
except ValueError:
    print("Warning: empty database")

# SET VARIABLES 
MKL_THREADING_LAYER = "tbb" # Lenskit variable to make code more efficient 
results_per_page = 10
genre_list = ['Action', 'Adventure', 'Animation', 'Children', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western', '(no genres listed)']
app.jinja_env.add_extension(MarkdownExtension)

# INITIALIZE DATABASE & INDEX 
@app.cli.command('initdb')
def initdb_command():
    """Creates the database table."""
    
    # DATABASE 
    global db
    check_and_read_data(db)

    print('Initialized the database.')

# INITIALIZE DATABASE & INDEX 
@app.cli.command('initindex')
def initdb_command():
    """Creates the index."""

    # WHOOSH INDEX 
    if not os.path.exists("whoosh_index"):
        os.mkdir("whoosh_index")

    schema = Schema(id=ID(stored=True), title=TEXT(stored=True), overview=TEXT(stored=True), tag=TEXT(stored=True), review=TEXT(stored=True))
    ix = create_in("whoosh_index", schema)
    writer = ix.writer()

    # INDEX MOVIES 
    for movie in Movie.query.all():
        r_list = [r.review for r in movie.reviews]
        merged_r =  "".join(r_list)
        t_list = [t.tag for t in movie.tags]
        merged_t =  " ".join(t_list)

        writer.add_document(id=str(movie.id), title=movie.title, overview=movie.blurb, tag=merged_t, review=merged_r)

    writer.commit()
    print('Initialized the index.')

# HOME PAGE 
@app.route('/')
def home_page():
    """ Home page """
    return render_template("home.html")

# MOVIES
@app.route('/movies')
@login_required  
def movies_page():
    """ Displays movies and offers to filter for movies """
    movies, scores = get_recommendations(model_random, user_id=current_user.id, number=results_per_page)

    return render_movies_template(movies, "movies.html", show_recommendation=True, show_search=True)

# RECOMMENDATIONS
@app.route('/recommendations')
@login_required  
def recommendations_page():
    """ Recommendation functionality """
    
    # Handle exceptions 
    if not 'recommender' in request.args:
        return "No recommender choice provided", 400
    else:
        try:
            recommender = request.args['recommender']
        except ValueError:
            return "Malformed request parameters provided", 400

        model = None
        genre = None

        # Check for recommender type 
        if recommender == "Popular":
            model = model_popular
        elif recommender == "Bias":
            model = model_bias
        elif recommender == "User":
            model = model_user_user
        elif recommender == "Item":
            model = model_item_item
        elif recommender == "mf":
            model = model_implicit_mf
        elif recommender == "TopGenre":
            try:
                genre = request.args['genre']
            except ValueError:
                return "Malformed request parameters provided", 400
            if not genre in genre_list:
                return "Malformed request parameters provided", 400
        else:
            return "Malformed request parameters provided", 400

        # Get recommendations
        if not genre:
            q, _ = get_recommendations(model, user_id=current_user.id, number=results_per_page)
        else:
            q = filter_best(tag=[], genre=[genre], number=results_per_page, db=db, include="0", user_id=current_user.id)

    return render_movies_template(q,  "movies.html", show_recommendation=True)

# RECOMMENDATION OVERVIEW 
@app.route('/recommendations_overview')
@login_required  
def recommendations_overview():
    """ Provides an appealing overview of personal recommendations. Movies of different recommendation types are displayed. """

    movies = []
    headings = []
    types = []

    # implicit_mf 
    imf_movies, _ = get_recommendations(model_implicit_mf, user_id=current_user.id, number=results_per_page)
    if len(imf_movies)>2:
        movies.append(imf_movies)
        headings.append("Recommended for you")
        types.append("mf")

    # user-user based
    user_movies, _ = get_recommendations(model_user_user, user_id=current_user.id, number=results_per_page)
    if len(user_movies)>2:
        movies.append(user_movies)
        headings.append("Other users also liked")
        types.append("User")

    # item-item based
    item_movies, _ = get_recommendations(model_item_item, user_id=current_user.id, number=results_per_page)
    if len(item_movies)>2:
        movies.append(item_movies)
        headings.append("Based on the movies you liked")
        types.append("Item")

    # popular based
    popular_movies, _ = get_recommendations(model_popular, user_id=current_user.id, number=results_per_page)
    if len(popular_movies)>2:
        movies.append(popular_movies)
        headings.append("Most popular")
        types.append("Popular")

    # watch list
    movie_ids = get_watchlist_movies()
    watchlist_movies = Movie.query.filter(Movie.id.in_(movie_ids)).limit(results_per_page).all()
    if len(watchlist_movies)>2:
        movies.append(watchlist_movies)

        headings.append("From your watchlist")
        types.append("watchlist")

    # top-rated in random
    genre = random.choice(genre_list)

    genre_movies = filter_best(tag=[], genre=[genre], number=results_per_page, db=db, include="0", user_id=current_user.id)
    print(genre, genre_movies, len(genre_movies))
    if len(genre_movies)>2:
        movies.append(genre_movies)
        headings.append("Top rated movies in {}".format(genre))
        types.append("TopGenre&genre="+genre)

    print(movies, headings, types)
    print(len(movies), len(headings), len(types))

    return render_template("recommendations_overview.html", movies_and_headings=zip(movies, headings, types))

# LOAD MORE 
@app.route('/load-more-results', methods=['POST'])
@login_required  
def more_results():
    """ Gets more movies for the load more functionality """
    
    # Handle exceptions 
    if not 'type' in request.form:
        return "No type of content to filter provided", 400

    if not 'page' in request.form:
        return "No page number provided", 400
    
    else:       
        try:
            request_type = request.form.get('type')[1:]
            page_number = int(request.form.get('page'))+1
            if  'genres' in request.form:
                genres = request.form.get('genres').split(",")
            if  'tags' in request.form:
                tags = request.form.get('tags').split(",")

        except ValueError:
            return "Malformed request parameters provided", 400


        # Filter based on request type 
        movies = Movie.query
        if request_type == 'movies':
            movies, _ = get_recommendations(model_random, user_id=current_user.id, number=results_per_page*page_number)
        elif request_type == 'watchlist':
            movies =  Movie.query.filter(Movie.id.in_(select(WatchList.movie_id))).limit(results_per_page*page_number).all()
        elif request_type == 'recommendations':
            if not 'recommender' in request.form:
                return "No recommender choice provided", 400
            else:
                try:
                    recommender = request.form.get('recommender')
                except ValueError:
                    return "Malformed request parameters provided", 400


                model = None
                genre = None

                # Check for recommender algorithm 
                if recommender == "Popular":
                    model = model_popular
                elif recommender == "Bias":
                    model = model_bias
                elif recommender == "User":
                    model = model_user_user
                elif recommender == "Item":
                    model = model_item_item
                elif recommender == "mf":
                    model = model_implicit_mf
                elif recommender == "TopGenre":
                    
                    try:
                        genre = request.form.get('genre')
                    except ValueError:
                        return "Malformed request parameters provided", 400
                    if not genre in genre_list:
                        return "Malformed request parameters provided", 400
                else:
                    return "Malformed request parameters provided", 400

                # Get recommendations
                if not genre:
                    movies, _ = get_recommendations(model, user_id=current_user.id, number=results_per_page*page_number)
                else:
                    movies = filter_best(tag=[], genre=[genre], number=results_per_page*page_number, db=db, include="0", user_id=current_user.id)

        else:
            return "Invalid type", 400      

        show_more = False if len(movies) < results_per_page*page_number else True
        movies = movies[results_per_page*(page_number-1):]
        
        return render_movies_template(movies, "movies_list.html", show_more=show_more)
    
# MOVIE DETAIL 
@app.route('/movie')
@login_required  
def movie():  
    """ Displays one movie in detail and shows similar ones """

    # Handle exceptions 
    if not 'id' in request.args:
        return "No movie id provided", 400
    else:
        try:
            movie_id = int(request.args['id'])
        except ValueError:
            return "Malformed request parameters provided", 400

        # Get necessary information of movie 
        movie = Movie.query.filter(Movie.id==movie_id).first()

        avg = MovieRating.query.filter(MovieRating.movie_id==movie_id).with_entities(func.avg(MovieRating.rating)).first()
        avg_rating = np.array(avg).flatten()[0]

        scores = model_item_item.predict_for_user(current_user.id, [movie_id])
        scores = [round((score - 0) / (6 - 0) * 100) for score in scores]
        probability = scores[0]       

        tags = np.array([t.tag for t in movie.tags])
        tags, counts = np.unique(tags, return_counts=True)
        sorted_indices = np.argsort(counts)
        sorted_indices = np.flip(sorted_indices)
        tags = tags[sorted_indices]
        
        rating = MovieRating.query.filter(MovieRating.user_id==current_user.id, MovieRating.movie_id==movie.id).order_by(desc(MovieRating.timestamp)).first()
        if rating:
            rating = rating.rating
        watchlisted = WatchList.query.filter(WatchList.user_id==current_user.id, WatchList.movie_id==movie.id).first()

        # # TODO get similar movies - move this to read data!!!
        # with open("secrets/tmdb_api.txt", "r") as file:
        #     api_key = file.read()
        # # request data for the movie https://api.themoviedb.org/3/movie/{movie_id}/similar
        # response = requests.get("https://api.themoviedb.org/3/movie/{}/similar?api_key={}".format(movie.links[0].tmdb_id, api_key))
        
        similar_movies = []
        try:
            results = SimilarMovie.query.filter(SimilarMovie.query_tmdb_id==movie.links[0].tmdb_id).all()
            
            for m in results:
                m_id = m.sim_movie_tmdb_id
                print(m_id)
                db_id = MovieLinks.query.filter(MovieLinks.tmdb_id==m_id).first()
                if db_id:
                    print("appending: ", db_id)
                    print("appending: ", db_id)
                    sim_movie = Movie.query.get(db_id.id)
                    if sim_movie:
                        print("appending: ", sim_movie)
                        similar_movies.append(sim_movie)
        except KeyError:
            pass

        return render_template("movie_detail.html", m=movie, tags=tags, rating=rating, watchlisted=watchlisted, avg_rating=avg_rating, probability=probability, similar_movies=similar_movies)

# WATCHLIST
@app.route('/watchlist')
@login_required  
def watchlist_page():   
    """ Shows movies on a user's watchlist (denoted by a heart symbol)""" 

    movie_ids = get_watchlist_movies()
    q = Movie.query.filter(Movie.id.in_(movie_ids))

    return render_movies_template(q, "movies.html", show_more=False)

@app.route('/watchlist_change', methods=['POST'])
@login_required  
def toggle_watchlist():
    """ Handles a change in the watchlist and amends the data in the database accordingly """

    # Handle exceptions 
    if not 'm' in request.form:
        return "No movie provided", 400
    else:
        try:
            movie_id = int(request.form.get('m'))
        except ValueError:
            return "Malformed request parameters provided", 400

        # Check if movie is already on watchlist
        result = WatchList.query.filter(WatchList.user_id==current_user.id, WatchList.movie_id==movie_id).first()
        added = None
        
        if result:
            # Remove from watchlist 
            WatchList.query.filter(WatchList.user_id==current_user.id, WatchList.movie_id==movie_id).delete()
            db.session.commit()
        else:
            # Add to watch list
            watchlist_item = WatchList(user_id=current_user.id, movie_id=movie_id, timestamp=time.time())
            db.session.add(watchlist_item)
            db.session.commit()
            added = True

    return render_template("watchlist_toggle.html", added=added, movie_id=movie_id)

# RATED MOVIES  
@app.route('/rated-movies')
@login_required  
def rated_page():   
    """ Displays already rated movies for a certain user """ 

    ratings = MovieRating.query.filter(MovieRating.user_id==current_user.id).with_entities(MovieRating.movie_id).all()
    movie_ids = np.array(ratings).flatten()
    q = Movie.query.filter(Movie.id.in_(movie_ids.tolist()))

    return render_movies_template(q, "movies.html", show_more=False)

# FILTER 
@app.route('/filter', methods=['POST'])
@login_required  
def movies_page_filtered():
    """ Handles the filter options selected by the user """

    genres = []
    tags = []
    model = None
    genre = None
    movies=""
    
    # Handle exceptions 
    if not 'type' in request.form:
        return "No type of content to filter provided", 400
    
    else:       
        try:
            request_type = request.form.get('type')
            if  'genres' in request.form:
                genres = request.form.get('genres').split(",")
            if  'tags' in request.form:
                tags = request.form.get('tags').split(",")
            if  'algorithm' in request.form:
                algorithm = request.form.get('algorithm')
                model = model_dict[algorithm]
        except (ValueError, KeyError) as e:
            return "Malformed request parameters provided", 400

        show_recommendation = False
        show_search = False
        show_more = False

        # Check for request type 
        database_for_filtering = Movie.query
        if request_type == 'movies':
            if model:
                database_for_filtering, _ = get_recommendations_query(model, user_id=current_user.id, number=1000)
                movies, _ = get_recommendations(model, user_id=current_user.id, number=1000)
            else:
                database_for_filtering = Movie.query
                show_recommendation = True
                show_search = True
                show_more = True

        elif request_type == 'watchlist':
            database_for_filtering =  Movie.query.filter(Movie.id.in_(select(WatchList.movie_id)))

        elif request_type == 'rated-movies':
            ratings = MovieRating.query.filter(MovieRating.user_id==current_user.id).with_entities(MovieRating.movie_id).all()
            movie_ids = np.array(ratings).flatten()
            database_for_filtering = Movie.query.filter(Movie.id.in_(movie_ids.tolist()))

        elif request_type == 'recommendations':
            show_recommendation = True
            if not model:
                try:
                    recommender = request.form.get('recommender')
                    if recommender == "Popular":
                        model = model_popular
                    elif recommender == "Bias":
                        model = model_bias
                    elif recommender == "User":
                        model = model_user_user
                    elif recommender == "Item":
                        model = model_item_item
                    elif recommender == "mf":
                        model = model_implicit_mf
                    elif recommender == "TopGenre":
                        try:
                            genre = request.args['genre']
                        except ValueError:
                            return "Malformed request parameters provided", 400
                        if not genre in genre_list:
                            return "Malformed request parameters provided", 400
                    else:
                        return "Malformed request parameters provided", 400
                except ValueError:
                    pass
            if not model:
                return "Missing recommender/algorithm for recommendation", 400
            
            # Get recommendations
            if not genre:
                database_for_filtering, _ = get_recommendations_query(model, user_id=current_user.id, number=1000)
                movies, _ = get_recommendations(model, user_id=current_user.id, number=1000)
            else:
                movies = filter_best(tag=[], genre=[genre], number=1000, db=db, include="0", user_id=current_user.id)
                movie_ids = [m.id for m in movies]
                database_for_filtering = Movie.query.filter(Movie.id.in_(movie_ids)) 

        else:
            return "Invalid type", 400      
        
        
        # Apply genre and tag filter 
        if genres and tags:
            movies = database_for_filtering\
                .filter(Movie.genres.any(MovieGenre.genre.in_(genres))) \
                .filter(Movie.tags.any(MovieTag.tag.in_(tags))) \
                .limit(results_per_page).all()

        elif genres:
            movies = database_for_filtering.filter(Movie.genres.any(MovieGenre.genre.in_(genres))).limit(results_per_page).all()

        elif tags:
            movies = database_for_filtering.filter(Movie.tags.any(MovieTag.tag.in_(tags))).limit(results_per_page).all()

        return render_movies_template(movies, "movies_list.html", show_more=show_more, show_recommendation=show_recommendation, show_search=show_search)

# RATING 
@app.route('/rating', methods=['POST'])
@login_required  
def rate_movie():
    """Rate the movie"""

    # Handle exceptions 
    if not 'm' in request.form:
        return "No movie provided", 400
    elif not 'r' in request.form:
        return "No rating provided", 400
    else:
        try:
            user_id = current_user.id
            movie_id = int(request.form.get('m'))
            rating = int(request.form.get('r'))
        except ValueError:
            return "Malformed request parameters provided", 400
        timestamp = time.time()

        # Only one Rating possible, so delete previous rating if exisiting 
        db.session.query(MovieRating).filter(MovieRating.user_id==user_id).filter(MovieRating.movie_id==movie_id).delete()

        movie_rating = MovieRating(user_id=user_id, movie_id=movie_id, rating=rating, timestamp=timestamp)
        db.session.add(movie_rating)
        db.session.commit()
        
        # Update recommenders in the background to take this rating into account
        data = pd.read_sql("movie_ratings", con=db.get_engine().connect(), index_col=None)
        data = data.rename(columns={"user_id":"user", "movie_id":"item"})

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(adapt_recommender, algo, data): algo for algo in algos}
            for future in concurrent.futures.as_completed(future_to_url):
                algo = future_to_url[future]
                try:
                    result = future.result()
                    if type(result)==basic.Popular:
                        model_popular = result
                    elif type(result)==bias.Bias:
                        model_bias = result
                    elif type(result)==UserUser:
                        model_user_user = result
                    elif type(result)==ItemItem:
                        model_item_item = result
                    elif type(result)==als.ImplicitMF:
                        model_implicit_mf = result
                    elif type(result)==basic.Random:
                        model_random = result

                except Exception as exc:
                    print('%r generated an exception: %s' % (str(algo), exc))

    return render_template("rating.html", user_id=user_id, movie_id=movie_id, rating=rating)

@app.route('/ratings', methods=['POST'])
@login_required  
def ratings():
    """Render the ratings template according to how many stars are currently selected"""

    if not 'm' in request.form:
        return "No movie provided", 400
    elif not 'r' in request.form:
        return "No rating provided", 400
    else:
        try:
            movie_id = int(request.form.get('m'))
            rating = int(request.form.get('r'))
        except ValueError:
            return "Malformed request parameters provided", 400

    return render_template("ratings.html", movie_id=movie_id, rating=rating)

# SORT BY 
@app.route('/sort_by', methods=['POST'])
@login_required  
def get_newly_sorted_items():
    """ Sorts the displayed movie based on selected options by user """

    # Handle exeptions 
    if not 's' in request.form:
        return "No sort method provided", 400
    elif not 'type' in request.form:
        return "No type of content to sort provided", 400
    elif not 'movie_ids' in request.form:
        return "No movies to sort provided", 400
    elif not 'probabilities' in request.form:
        return "No match probabilities of movies to sort provided", 400
    
    else:
        try:
            request_type = request.form.get('type')[1:]
            sort_by = request.form.get('s')
            movies = request.form.get('movie_ids').split(',')
            print("movies to sort:", movies)
            probabilities = request.form.get('probabilities').split(',')
        except ValueError:
            return "Malformed request parameters provided", 400

        # Sort movies based on sort criterion
        q = Movie.query.filter(Movie.id.in_(movies))
        if sort_by == 'release_date':
            q = q.order_by(Movie.release_date)
        elif sort_by == 'runtime':
            q = q.order_by(Movie.runtime)
        elif sort_by == 'title':
            q = q.order_by(Movie.title)
        elif sort_by == 'mean_rating':
            averages = MovieRating.query.order_by(MovieRating.movie_id).group_by(MovieRating.movie_id).with_entities(func.avg(MovieRating.rating).label('average'))
            avg = []
            for m in movies:
                avg.append(averages.filter(MovieRating.movie_id==m).first())

            sorted_indices = np.argsort(np.array(avg).flatten())
            sorted_movies = np.array(movies)[sorted_indices]
            q = []
            for m in sorted_movies:
                m = int(m)
                movie = Movie.query.get(m)
                q.append(movie)

        elif sort_by == 'probabilities':
            sorted_indices = np.argsort(np.array(probabilities))
            sorted_movies = np.array(movies)[sorted_indices]
            sorted_probabilities = np.array(probabilities)[sorted_indices]
            probabilities = list(sorted_probabilities)
            q = []
            for m in sorted_movies:
                m = int(m)
                movie = Movie.query.get(m)
                q.append(movie)

        return render_movies_template(q, "movies_list.html", probabilities)
   
# SEARCHBAR
@app.route('/searchbar', methods=['POST'])
@login_required 
def display_searched_movies():
    """ Use a searchbar with an index to filter movies based on a certain query. The title, description, reviews and tags are used to search for a query. """

    # GET DATA & INDEX  
    search_term = request.json
    ix = index.open_dir("whoosh_index")

    # PARSE 
    with ix.searcher(weighting=scoring.BM25F()) as searcher:
        title_parser = QueryParser("title", ix.schema, group=OrGroup)
        description_parser = QueryParser("overview", ix.schema, group=OrGroup)
        review_parser = QueryParser("review", ix.schema, group=OrGroup)
        tag_parser = QueryParser("tag", ix.schema, group=OrGroup)

        # QUERY
        title_query = title_parser.parse(search_term)
        description_query = description_parser.parse(search_term)
        review_query = review_parser.parse(search_term)
        tag_query = tag_parser.parse(search_term)
        combined_query = title_query | description_query | review_query | tag_query

        # RESULTS
        final_results = searcher.search(combined_query, limit=None)
        search_results = [{"id": hit["id"], "title": hit["title"], "overview": hit["overview"], "tag" : hit["tag"], "review" : hit["review"]} for hit in final_results]
        ranked_results = sorted(search_results, key=lambda x: (x["overview"].lower().count(search_term.lower()) + x["title"].lower().count(search_term.lower())), reverse=True)
            
        # MOVIES 
        movies = Movie.query.filter(Movie.id.in_([ r['id'] for r in ranked_results])).all()

        return render_movies_template(movies, "movies_list.html")

# MOVIE TEMPLATE 
def render_movies_template(movies, template, scores=None, show_more=True, show_recommendation=False, show_search=False):
    """ This function provides all the information to render the movies template """

    movie_ids = [movie.id for movie in movies]
    avg = MovieRating.query.order_by(MovieRating.movie_id).group_by(MovieRating.movie_id).with_entities(func.avg(MovieRating.rating)).filter(MovieRating.movie_id.in_(movie_ids)).all()
    movie_ids.sort()
    sorted_indices = np.argsort(np.array(avg).flatten())
    sorted_movies = np.array(movie_ids)[sorted_indices]
    average_ratings = dict(zip(map(str, sorted_movies), np.array(avg).flatten()[sorted_indices]))

    if not scores:
        scores = model_item_item.predict_for_user(current_user.id, movie_ids)
        scores = [round((score - 0) / (6 - 0) * 100) for score in scores]
        probabilities = scores
    else:
        probabilities = scores

    all_tags = []
    ratings = []
    watchlisted = []
    average_ratings_sorted = []
    movie_ids = []
    
    for movie in movies:
        tags = np.array([t.tag for t in movie.tags])
        tags, counts = np.unique(tags, return_counts=True)
        sorted_indices = np.argsort(counts)
        sorted_indices = np.flip(sorted_indices)
        tags = tags[sorted_indices]
        all_tags.append(tags)
        rating = MovieRating.query.filter(MovieRating.user_id==current_user.id, MovieRating.movie_id==movie.id).order_by(desc(MovieRating.timestamp)).first()
        on_watchlist = WatchList.query.filter(WatchList.user_id==current_user.id, WatchList.movie_id==movie.id).first()
        watchlisted.append(on_watchlist)
        average_ratings_sorted.append('{0:.2f}'.format(average_ratings[str(movie.id)]))
        movie_ids.append(movie.id)

        try:
            ratings.append(rating.rating)
        except AttributeError:
            ratings.append(None)    

    tag_list = create_tag_list()
    genre_list = ['Action', 'Adventure', 'Animation', 'Children', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western', '(no genres listed)']
    item_list = zip([title.title for title in Movie.query.all()], [d.blurb for d in Movie.query.all()])

    return render_template(template, movies_and_tags=zip(movies, all_tags, ratings, watchlisted, average_ratings_sorted, probabilities), genres=db.session.query(MovieGenre.genre).distinct(), tags=db.session.query(MovieTag.tag).distinct(), movie_ids=movie_ids, tag_list=tag_list, genre_list=genre_list, item_list=item_list, probabilities=probabilities, show_more_enabled=show_more, show_recommendation=show_recommendation, show_search=show_search)

# START SERVER
if __name__ == '__main__':
    app.run(port=5000, debug=True)
