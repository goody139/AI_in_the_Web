# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

from flask import Flask, render_template, request
from flask_user import login_required, UserManager, current_user
from sqlalchemy import func, desc, delete, select
from models import *
from helper_functions import *
from read_data import check_and_read_data, get_tmdb_data_for_movie
import time
import numpy as np
from lenskit.datasets import ML100K
import pandas as pd
import random
from jinja_markdown2 import MarkdownExtension

from lenskit.algorithms.basic import UnratedItemCandidateSelector

from lenskit.algorithms import Recommender
from lenskit.algorithms.user_knn import UserUser

# Class-based application configuration
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

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = UserManager(app, db, User)  # initialize Flask-User management

# timestamp_of_last_model_fit = time.time()
# data = pd.read_sql("movie_ratings", con=db.get_engine().connect(), index_col=None)
# data = data.rename(columns={"user_id":"user", "movie_id":"item"})
# print(data)

# user_user = UserUser(15, min_nbrs=3) 
# algo = Recommender.adapt(user_user)
# algo.fit(data)
# print("set up recommender")



app.jinja_env.add_extension(MarkdownExtension)

@app.cli.command('initdb')
def initdb_command():
    global db
    """Creates the database tables."""
    check_and_read_data(db)
    print('Initialized the database.')

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

    # first 10 movies
    movies = Movie.query.limit(10).all()
    
    # only Romance movies
    # movies = Movie.query.filter(Movie.genres.any(MovieGenre.genre == 'Romance')).limit(10).all()

    # only Romance AND Horror movies
    # movies = Movie.query\
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Romance')) \
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Horror')) \
    #     .limit(10).all()
    
    # DEFAULT -- 10 best rated movies with random genre 
    genre_list = genre_list = ['Action', 'Adventure', 'Animation', 'Children', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western', 'Other']
    #movies = filter_best([], random.choice(genre_list), 10, db, include=False, user_id=current_user.id)
    print("BUILD MODEL")
    movies, scores = build_recommender(genre=[random.choice(genre_list)], tag=None, algo="Best rated movies", number=10, user_id="off", include="", db=db)
    print("prepare")


    return render_movies_template(movies, "movies.html", scores=scores)


# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/recommendations')
@login_required  # User must be authenticated
def recommendations_page():

    # query = MovieRating.query.filter(MovieRating.user_id==current_user.id, MovieRating.timestamp>timestamp_of_last_model_fit)

    # if query.all():
    #     print(query.all())
    #     new_ratings = pd.read_sql(query.statement, con=db.get_engine().connect(), index_col=None)
    #     new_ratings = new_ratings.rename(columns={"user_id":"user", "movie_id":"item"})
    #     print(new_ratings)
    #     print("after \n")
    #     new_ratings = new_ratings.set_index('item')['rating']
    #     print(new_ratings)

    #     recs = algo.recommend(user=current_user.id, n=10, ratings=new_ratings)
    # else:
    #     print("!!! No new ratings !!!")
    #     recs = algo.recommend(user=current_user.id, n=10)
    # print("recommendations:", recs)

    """ Recommendation functionality """

    if request.method == 'POST':
        
        # GET filter options 
        user_id = request.form.get('user_id')
        tag = request.form.get('tag')
        genre = request.form.get('genre')
        number = request.form.get('number')
        algorithm = request.form.get('algorithm')
        include = request.form.get('include')
        title = request.form.get('title')

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


    # q = []
    # for m in recs['item']:
    #     m = int(m)
    #     movie = Movie.query.get(m)
    #     q.append(movie)

    return render_movies_template(q,  "movies.html", scores=normalized_scores)

    


@app.route('/watchlist')
@login_required  # User must be authenticated
def watchlist_page():    
    movie_ids = get_watchlist_movies()
    q = Movie.query.filter(Movie.id.in_(movie_ids))

    return render_movies_template(q, "movies.html")



@app.route('/filter', methods=['POST'])
@login_required  # User must be authenticated
def movies_page_filtered():
    # String-based templates
    print(request.form)
    genres = []
    tags = []
    
    if not 'type' in request.form:
        return render_template("return_to_start.html", title='No search term', error_cause='No search term provided')
    
    else:       
        request_type = request.form.get('type')[1:]
        if  'genres' in request.form:
            genres = request.form.get('genres').split(",")
        if  'tags' in request. form:
            tags = request.form.get('tags').split(",")
        print("looking for both")
        print()

        # the elements to filter vary based on the request type
        database_for_filtering = Movie.query
        if request_type == 'movies':
            database_for_filtering = Movie.query
        elif request_type == 'watchlist':
            database_for_filtering =  Movie.query.filter(Movie.id.in_(select(WatchList.movie_id)))
            print(database_for_filtering)
        elif request_type == 'recommendations':
            # get recommendations
            movie_ids = get_recommendations_movies()
            # get query of these from the database
            database_for_filtering = Movie.query.filter(Movie.id.in_(movie_ids))
        else:
            return "Invalid type", 400      

        
        

        print(genres, tags)

        
        movies=""

        if genres and tags:
            print("looking for both", genres, tags)
            movies = database_for_filtering\
                .filter(Movie.genres.any(MovieGenre.genre.in_(genres))) \
                .filter(Movie.tags.any(MovieTag.tag.in_(tags))) \
                .limit(10).all()

        elif genres:
            print("looking for genres", genres)
            movies = database_for_filtering.filter(Movie.genres.any(MovieGenre.genre.in_(genres))).limit(10).all()

        elif tags:
            print("looking for tags", tags)
            movies = database_for_filtering.filter(Movie.tags.any(MovieTag.tag.in_(tags))).limit(10).all()

        print("r",movies)
        if request_type == 'recommendations' and len(movies)==0:
            movie_ids = get_recommendations_movies(number_to_recommend=1000)
            database_for_filtering = Movie.query.filter(Movie.id.in_(movie_ids))

            if genres and tags:
                print("looking for both", genres, tags)
                movies = database_for_filtering\
                    .filter(Movie.genres.any(MovieGenre.genre.in_(genres))) \
                    .filter(Movie.tags.any(MovieTag.tag.in_(tags))) \
                    .limit(10).all()

            elif genres:
                print("looking for genres", genres)
                movies = database_for_filtering.filter(Movie.genres.any(MovieGenre.genre.in_(genres))).limit(10).all()

            elif tags:
                print("looking for tags", tags)
                movies = database_for_filtering.filter(Movie.tags.any(MovieTag.tag.in_(tags))).limit(10).all()

            print("r2",movies)


        return render_movies_template(movies, "movies_list.html")



@app.route('/rating', methods=['POST'])
@login_required  # User must be authenticated
def rate_movie():
    """Rate the movie"""
    if not 'm' in request.form:
        return render_template("return_to_start.html", title='No search term', error_cause='No search term provided')
    elif not 'r' in request. form:
        return render_template("return_to_start.html", title='No search term', error_cause='No search term provided')
    else:
        user_id = current_user.id
        movie_id = int(request.form.get('m'))
        rating = int(request.form.get('r'))
        timestamp = time.time()
        movie_rating = MovieRating(user_id=user_id, movie_id=movie_id, rating=rating, timestamp=timestamp)
        db.session.add(movie_rating)
        db.session.commit()
        print("movie id:", movie_id)
    return render_template("rating.html", user_id=user_id, movie_id=movie_id, rating=rating)

@app.route('/ratings', methods=['POST'])
@login_required  # User must be authenticated
def ratings():
    """Render the ratings template according to how many stars are currently selected"""
    if not 'm' in request.form:
        return render_template("return_to_start.html", title='No search term', error_cause='No search term provided')
    elif not 'r' in request. form:
        return render_template("return_to_start.html", title='No search term', error_cause='No search term provided')
    else:
        movie_id = int(request.form.get('m'))
        rating = int(request.form.get('r'))
        print("movie id:", movie_id)

    return render_template("ratings.html", movie_id=movie_id, rating=rating)

@app.route('/watchlist_change', methods=['POST'])
@login_required  # User must be authenticated
def toggle_watchlist():
    if not 'm' in request.form:
        return render_template("return_to_start.html", title='No search term', error_cause='No search term provided')
    else:
        movie_id = int(request.form.get('m'))

        # check whether the movie is already on the watchlist
        result = WatchList.query.filter(WatchList.user_id==current_user.id, WatchList.movie_id==movie_id).first()
        added = None
        
        if result:
            # remove from watch list
            WatchList.query.filter(WatchList.user_id==current_user.id, WatchList.movie_id==movie_id).delete()
            db.session.commit()
        else:
            # add to watch list
            watchlist_item = WatchList(user_id=current_user.id, movie_id=movie_id, timestamp=time.time())
            db.session.add(watchlist_item)
            db.session.commit()
            added = True

    return render_template("watchlist_toggle.html", added=added, movie_id=movie_id)


def get_movies():
    # first 10 movies
    movies = Movie.query.limit(10).all()
    movie_ids = [movie.id for movie in movies]
    return movie_ids

def get_watchlist_movies():
    watchlist = WatchList.query.filter(WatchList.user_id==current_user.id).all()
    movie_ids = [watchlist_item.movie_id  for watchlist_item in watchlist]
    return movie_ids

def get_recommendations_movies(number_to_recommend=10):
    query = MovieRating.query.filter(MovieRating.user_id==current_user.id, MovieRating.timestamp>timestamp_of_last_model_fit)

    if query.all():
        new_ratings = pd.read_sql(query.statement, con=db.get_engine().connect(), index_col=None)
        new_ratings = new_ratings.rename(columns={"user_id":"user", "movie_id":"item"})
        new_ratings = new_ratings.set_index('item')['rating']
        recs = algo.recommend(user=current_user.id, n=number_to_recommend, ratings=new_ratings)
    else:
        recs = algo.recommend(user=current_user.id, n=number_to_recommend)

    print("recommendations:", recs)

    movie_ids = [movie_id for movie_id in recs['item']]
    return movie_ids

def render_movies_template(movies, template, scores=None):
    movie_ids = [movie.id for movie in movies]
    avg = MovieRating.query.order_by(MovieRating.movie_id).group_by(MovieRating.movie_id).with_entities(func.avg(MovieRating.rating)).filter(MovieRating.movie_id.in_(movie_ids)).all()
    movie_ids.sort()
    sorted_indices = np.argsort(np.array(avg).flatten())
    sorted_movies = np.array(movie_ids)[sorted_indices]
    average_ratings = dict(zip(map(str, sorted_movies), np.array(avg).flatten()[sorted_indices]))

    if not scores:
        print("move ids", movie_ids, "user id", current_user.id)
        ratings = filter_ratings([], [])
        data = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating, rating.timestamp) for rating in ratings],
                            columns=['user', 'item', 'rating', 'timestamp'])

        print("rec data", data)
        probabilities = predict_rating(movie_ids, current_user.id, data)
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
    genre_list = ['Action', 'Adventure', 'Animation', 'Children', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western', 'Other']
    item_list = zip([title.title for title in Movie.query.all()], [d.blurb for d in Movie.query.all()])
    
    # probabilities = [i for i in range(len(watchlisted))]

    return render_template(template, movies_and_tags=zip(movies, all_tags, ratings, watchlisted, average_ratings_sorted, probabilities), genres=db.session.query(MovieGenre.genre).distinct(), tags=db.session.query(MovieTag.tag).distinct(), movie_ids=movie_ids, tag_list=tag_list, genre_list=genre_list, item_list=item_list, probabilities=probabilities)



@app.route('/sort_by', methods=['POST'])
@login_required  # User must be authenticated
def get_newly_sorted_items():
    print("request form:", request.form)
    if not 's' in request.form:
        return render_template("return_to_start.html", title='No search term', error_cause='No search term provided')
    elif not 'type' in request.form:
        return render_template("return_to_start.html", title='No search term', error_cause='No search term provided')
    elif not 'movie_ids' in request.form:
        return render_template("return_to_start.html", title='No search term', error_cause='No search term provided')
    elif not 'probabilities' in request.form:
        return render_template("return_to_start.html", title='No search term', error_cause='No search term provided')
    
    else:
        request_type = request.form.get('type')[1:]
        sort_by = request.form.get('s')
        movies = request.form.get('movie_ids').split(',')
        probabilities = request.form.get('probabilities').split(',')
        print("sort ", request_type, " by ", sort_by, " movies:", movies)


        # if request_type == 'movies':
        #     movies = get_movies()
        # elif request_type == 'watchlist':
        #     movies = get_watchlist_movies()
        # elif request_type == 'recommendations':
        #     movies = get_recommendations_movies()
        # else:
        #     return "Invalid type", 400        
    
        # sort the movies according to the sort criterion
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
                print(averages.filter(MovieRating.movie_id==m).first(), m)
                avg.append(averages.filter(MovieRating.movie_id==m).first())
            # avg = db.session.query(func.avg(MovieRating.rating)).group_by(MovieRating.movie_id).filter(MovieRating.movie_id.in_(movies)).all()

            print(MovieRating.query.group_by(MovieRating.movie_id).with_entities(func.avg(MovieRating.rating).label('average')).filter(MovieRating.movie_id.in_(movies)).first())
            print(MovieRating.query.filter(MovieRating.movie_id.in_(movies)).first())


            print("avg", avg)
            sorted_indices = np.argsort(np.array(avg).flatten())
            sorted_movies = np.array(movies)[sorted_indices]
            q = []
            for m in sorted_movies:
                m = int(m)
                movie = Movie.query.get(m)
                q.append(movie)

        return render_movies_template(q, "movies_list.html", probabilities)
   

# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)
