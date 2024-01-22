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
import concurrent

from lenskit.algorithms.basic import UnratedItemCandidateSelector

from lenskit.algorithms import Recommender, basic, als, bias
from lenskit.algorithms.user_knn import UserUser


MKL_THREADING_LAYER = "tbb"


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
data = pd.read_sql("movie_ratings", con=db.get_engine().connect(), index_col=None)
data = data.rename(columns={"user_id":"user", "movie_id":"item"})

# user_user = UserUser(15, min_nbrs=3) 
# algo = Recommender.adapt(user_user)
# algo.fit(data)

# create models for recommending once in the beginning and then only update (concurrently) after a new rating was submitted
algo_popular = basic.Popular()
algo_bias = bias.Bias()
algo_user_user = Fallback(UserUser(100), algo_bias).fit(data)
algo_item_item = Fallback(ItemItem(100), algo_bias).fit(data)
# algo_biased_mf = als.BiasedMF(10)
algo_implicit_mf = als.ImplicitMF(10)
algo_random = basic.Random()

algos = [algo_popular, 
         algo_bias,
         algo_user_user,
         algo_item_item,
         algo_implicit_mf,
         algo_random]


model_popular = Recommender.adapt(algo_popular).fit(data)
print(model_popular)
model_bias = Recommender.adapt(algo_bias).fit(data)
print(model_bias)
model_user_user = Recommender.adapt(algo_user_user).fit(data)
print(model_user_user)
model_item_item = Recommender.adapt(algo_item_item).fit(data)
print(model_item_item)
# model_biased_mf = Recommender.adapt(algo_biased_mf).fit(data)
model_implicit_mf = Recommender.adapt(algo_implicit_mf).fit(data)
print(model_implicit_mf)
model_random = Recommender.adapt(algo_random).fit(data)
print(model_random)



print("set up recommender")

results_per_page = 10




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

    
def get_recommendations(model, user_id, number):
    recs = model.recommend(int(user_id), number)
    scores = None

    # EXTRACT MOVIE IDS 
    for i in range (0, len(recs['item'])):
        movie_ids = [int(recs['item'][i])for i in range (len(recs['item']))]
        try:
            scores = [int(recs['score'][i])for i in range (len(recs['score']))]
        except KeyError:
            pass
    
    if len(recs['item']) == 0: 
        movie_ids = []

    # NORMALIZE
    if scores:
        scores = [round((score - 0) / (6 - 0) * 100) for score in scores]

    return Movie.query.filter(Movie.id.in_(movie_ids)).all(), scores

# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
@login_required  # User must be authenticated
def movies_page():
    movies, scores = get_recommendations(model_random, user_id=current_user.id, number=results_per_page)

    return render_movies_template(movies, "movies.html")


# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/recommendations')
@login_required  # User must be authenticated
def recommendations_page():
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
            number = results_per_page

        if genre == "other": 
            filter_options[0] = "(no genres listed)"

        
        # BUILD model  
        movies, normalized_scores = build_recommender(genre=filter_options[0], tag=filter_options[1], algo=algorithm, number= int(number), include=include, db=db, user_id=int(user_id))  


    # q = []
    # for m in recs['item']:
    #     m = int(m)
    #     movie = Movie.query.get(m)
    #     q.append(movie)

    return render_movies_template(q,  "movies.html")


# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/recommendations_overview')
@login_required  # User must be authenticated
def recommendations_overview():
    # get the movies to show for the different recommendation types
    movies = []
    headings = []
    # # bias based
    # bias_movies, _ = get_recommendations(model_bias, user_id=current_user.id, number=results_per_page)

    # # # biased_mf based
    # bmf_movies, _ = get_recommendations(model_biased_mf, user_id=current_user.id, number=results_per_page)
    # # implicit mf based
    imf_movies, _ = get_recommendations(model_implicit_mf, user_id=current_user.id, number=results_per_page)
    if len(imf_movies)>2:
        movies.append(imf_movies)
        headings.append("Recommended for you")

    # # user-user based
    user_movies, _ = get_recommendations(model_user_user, user_id=current_user.id, number=results_per_page)
    if len(user_movies)>2:
        movies.append(user_movies)
        headings.append("Other users also liked")

    # # item-item based
    item_movies, _ = get_recommendations(model_item_item, user_id=current_user.id, number=results_per_page)
    if len(item_movies)>2:
        movies.append(item_movies)
        headings.append("Based on the movies you liked")

    # # popular based
    popular_movies, _ = get_recommendations(model_popular, user_id=current_user.id, number=results_per_page)
    if len(popular_movies)>2:
        movies.append(popular_movies)
        headings.append("Most popular")

    # # watch list
    movie_ids = get_watchlist_movies()
    watchlist_movies = Movie.query.filter(Movie.id.in_(movie_ids)).limit(results_per_page).all()
    if len(watchlist_movies)>2:
        movies.append(watchlist_movies)

        headings.append("From your watchlist")


    
    # top-rated in favorite genre
    # get the favorite genres [TODO]
    genre = "Animation"

    genre_movies = filter_best(tag=[], genre=[genre], number=results_per_page, db=db, include="0", user_id=current_user.id)

    if len(genre_movies)>2:
        movies.append(genre_movies)
        headings.append("Top rated movies in {}".format(genre))

    return render_template("recommendations_overview.html", movies_and_headings=zip(movies, headings))




@app.route('/load-more-results', methods=['POST'])
@login_required  # User must be authenticated
def more_results():
    if not 'type' in request.form:
        return "No type of content to filter provided", 400

    if not 'page' in request.form:
        return "No page number provided", 400
    
    else:       
        print("t")
        try:
            request_type = request.form.get('type')[1:]
            print("t1")
            page_number = int(request.form.get('page'))+1
            print("t2, ", page_number)
            if  'genres' in request.form:
                genres = request.form.get('genres').split(",")
            if  'tags' in request. form:
                tags = request.form.get('tags').split(",")
        except ValueError:
            return "Malformed request parameters provided", 400

        # the elements to filter vary based on the request type
        movies = Movie.query
        if request_type == 'movies':
            movies, _ = get_recommendations(model_random, user_id=current_user.id, number=results_per_page*page_number)
        elif request_type == 'watchlist':
            movies =  Movie.query.filter(Movie.id.in_(select(WatchList.movie_id))).limit(results_per_page*page_number).all()
        # elif request_type == 'recommendations':
        #     # get recommendations
        #     movie_ids = get_recommendations_movies()
        #     # get query of these from the database
        #     database_for_filtering = Movie.query.filter(Movie.id.in_(movie_ids))
        else:
            return "Invalid type", 400      

        show_more = False if len(movies) < results_per_page*page_number else True
        movies = movies[results_per_page*(page_number-1):]
        

        return render_movies_template(movies, "movies_list.html", show_more=show_more)
    
# [TODO] individual movie detail page 
@app.route('/movie')
@login_required  # User must be authenticated
def movie():  

    if not 'id' in request.args:
        return "No movie id provided", 400
    else:
        try:
            movie_id = int(request.args['id'])
        except ValueError:
            return "Malformed request parameters provided", 400

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

        return render_template("movie_detail.html", m=movie, tags=tags, rating=rating, watchlisted=watchlisted, avg_rating=avg_rating, probability=probability)

@app.route('/watchlist')
@login_required  # User must be authenticated
def watchlist_page():    
    movie_ids = get_watchlist_movies()
    q = Movie.query.filter(Movie.id.in_(movie_ids))

    return render_movies_template(q, "movies.html", show_more=False)



@app.route('/filter', methods=['POST'])
@login_required  # User must be authenticated
def movies_page_filtered():
    # String-based templates
    genres = []
    tags = []
    
    if not 'type' in request.form:
        return "No type of content to filter provided", 400
    
    else:       
        try:
            request_type = request.form.get('type')[1:]
            if  'genres' in request.form:
                genres = request.form.get('genres').split(",")
            if  'tags' in request. form:
                tags = request.form.get('tags').split(",")
        except ValueError:
            return "Malformed request parameters provided", 400

        # the elements to filter vary based on the request type
        database_for_filtering = Movie.query
        if request_type == 'movies':
            database_for_filtering = Movie.query
        elif request_type == 'watchlist':
            database_for_filtering =  Movie.query.filter(Movie.id.in_(select(WatchList.movie_id)))
        elif request_type == 'recommendations':
            # get recommendations
            movie_ids = get_recommendations_movies()
            # get query of these from the database
            database_for_filtering = Movie.query.filter(Movie.id.in_(movie_ids))
        else:
            return "Invalid type", 400      
        
        movies=""

        if genres and tags:
            movies = database_for_filtering\
                .filter(Movie.genres.any(MovieGenre.genre.in_(genres))) \
                .filter(Movie.tags.any(MovieTag.tag.in_(tags))) \
                .limit(results_per_page).all()

        elif genres:
            movies = database_for_filtering.filter(Movie.genres.any(MovieGenre.genre.in_(genres))).limit(results_per_page).all()

        elif tags:
            movies = database_for_filtering.filter(Movie.tags.any(MovieTag.tag.in_(tags))).limit(results_per_page).all()

        if request_type == 'recommendations' and len(movies)==0:
            movie_ids = get_recommendations_movies(number_to_recommend=1000)
            database_for_filtering = Movie.query.filter(Movie.id.in_(movie_ids))

            if genres and tags:
                movies = database_for_filtering\
                    .filter(Movie.genres.any(MovieGenre.genre.in_(genres))) \
                    .filter(Movie.tags.any(MovieTag.tag.in_(tags))) \
                    .limit(results_per_page).all()

            elif genres:
                movies = database_for_filtering.filter(Movie.genres.any(MovieGenre.genre.in_(genres))).limit(results_per_page).all()

            elif tags:
                movies = database_for_filtering.filter(Movie.tags.any(MovieTag.tag.in_(tags))).limit(results_per_page).all()

        return render_movies_template(movies, "movies_list.html")

def adapt_recommender(algo, data):
    return Recommender.adapt(algo).fit(data)

@app.route('/rating', methods=['POST'])
@login_required  # User must be authenticated
def rate_movie():
    """Rate the movie"""
    if not 'm' in request.form:
        return "No movie provided", 400
    elif not 'r' in request. form:
        return "No rating provided", 400
    else:
        try:
            user_id = current_user.id
            movie_id = int(request.form.get('m'))
            rating = int(request.form.get('r'))
        except ValueError:
            return "Malformed request parameters provided", 400
        timestamp = time.time()

        # there can be only one rating for a movie, so delete the previous one if one exists
        db.session.query(MovieRating).filter(MovieRating.user_id==user_id).filter(MovieRating.movie_id==movie_id).delete()

        movie_rating = MovieRating(user_id=user_id, movie_id=movie_id, rating=rating, timestamp=timestamp)
        db.session.add(movie_rating)
        db.session.commit()
        
        # now update the recommenders in the background to take this rating into account
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
@login_required  # User must be authenticated
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

@app.route('/watchlist_change', methods=['POST'])
@login_required  # User must be authenticated
def toggle_watchlist():
    if not 'm' in request.form:
        return "No movie provided", 400
    else:
        try:
            movie_id = int(request.form.get('m'))
        except ValueError:
            return "Malformed request parameters provided", 400

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
    # first results_per_page movies
    movies = Movie.query.limit(results_per_page).all()
    movie_ids = [movie.id for movie in movies]
    return movie_ids

def get_watchlist_movies():
    watchlist = WatchList.query.filter(WatchList.user_id==current_user.id).all()
    movie_ids = [watchlist_item.movie_id  for watchlist_item in watchlist]
    return movie_ids

def get_recommendations_movies(number_to_recommend=results_per_page):
    query = MovieRating.query.filter(MovieRating.user_id==current_user.id, MovieRating.timestamp>timestamp_of_last_model_fit)

    if query.all():
        new_ratings = pd.read_sql(query.statement, con=db.get_engine().connect(), index_col=None)
        new_ratings = new_ratings.rename(columns={"user_id":"user", "movie_id":"item"})
        new_ratings = new_ratings.set_index('item')['rating']
        recs = algo.recommend(user=current_user.id, n=number_to_recommend, ratings=new_ratings)
    else:
        recs = algo.recommend(user=current_user.id, n=number_to_recommend)

    movie_ids = [movie_id for movie_id in recs['item']]
    return movie_ids

def render_movies_template(movies, template, scores=None, show_more=True):
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
    
    # probabilities = [i for i in range(len(watchlisted))]
    print("movies render", movies)

    return render_template(template, movies_and_tags=zip(movies, all_tags, ratings, watchlisted, average_ratings_sorted, probabilities), genres=db.session.query(MovieGenre.genre).distinct(), tags=db.session.query(MovieTag.tag).distinct(), movie_ids=movie_ids, tag_list=tag_list, genre_list=genre_list, item_list=item_list, probabilities=probabilities, show_more_enabled=show_more)



@app.route('/sort_by', methods=['POST'])
@login_required  # User must be authenticated
def get_newly_sorted_items():
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

        print("sorted", q.all())

        return render_movies_template(q, "movies_list.html", probabilities)
   

# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)
