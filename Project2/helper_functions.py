#-------------------------- IMPORT ---------------------------------#
# Own files 
from models import *

# Python 
import pandas as pd
from scipy.special import expit

# Lenskit 
from lenskit import *
from lenskit.algorithms.item_knn import ItemItem
from lenskit.algorithms.user_knn import UserUser
from lenskit.algorithms.basic import Fallback
from lenskit.algorithms import Recommender, als, basic, bias 

# Flask & SQL
from sqlalchemy import or_, and_
from flask_user import current_user
#-------------------------------------------------------------------#

""" This file contains several helper functions"""

# FIT MODELS 
def fit_models(): 
    """ This function is fitting several models and returning them """

    data = pd.read_sql("movie_ratings", con=db.get_engine().connect(), index_col=None)
    data = data.rename(columns={"user_id":"user", "movie_id":"item"})

    # create models for recommending once in the beginning and then only update (concurrently) after a new rating was submitted
    algo_popular = basic.Popular()
    algo_bias = bias.Bias()
    algo_user_user = Fallback(UserUser(100), algo_bias)
    algo_item_item = Fallback(ItemItem(100), algo_bias)
    algo_implicit_mf = als.ImplicitMF(10)
    algo_random = basic.Random()

    algos = [algo_popular, 
            algo_bias,
            algo_user_user,
            algo_item_item,
            algo_implicit_mf,
            algo_random]


    model_popular = Recommender.adapt(algo_popular).fit(data)
    model_bias = Recommender.adapt(algo_bias).fit(data)
    model_user_user = Recommender.adapt(algo_user_user).fit(data)
    model_item_item = Recommender.adapt(algo_item_item).fit(data)
    model_implicit_mf = Recommender.adapt(algo_implicit_mf).fit(data)
    model_random = Recommender.adapt(algo_random).fit(data)

    return model_popular, model_bias, model_user_user, model_item_item, model_implicit_mf, model_random, algos

# FILTER 
def exclude_user_ratings(user_id, db): 

    # EXCLUDE RATINGS FOR ONE USER 
    subquery = (
        db.session.query(MovieRating.movie_id)
        .filter(MovieRating.user_id == user_id)
        .subquery()
    )

    movies_to_exclude = (
        db.session.query(Movie.id)
        .join(subquery, Movie.id == subquery.c.movie_id, isouter=True)
        .filter(subquery.c.movie_id.isnot(None))
        .all()
    )

    return movies_to_exclude

def filter_best(tag, genre, number, db, include, user_id): 

    # INITIALIZE 
    genres_filter = or_(*[MovieGenre.genre == g for g in genre]) if genre else None
    tags_filter = or_(*[MovieTag.tag == t for t in tag]) if tag else None
    
    # DEFAULT VALUE 
    if (genre == []) and (tag == []): 
        default_value = True
    else : 
        default_value = False

    # FILTER
    if include == "on": 
        movies = Movie.query.join(MovieGenre).join(MovieTag).join(MovieRating).filter(
            tags_filter if tags_filter is not None else True,
            genres_filter if genres_filter is not None else True, 
            ).group_by(Movie.id).order_by(db.func.avg(MovieRating.rating).desc()).all()
                            
    else: 
        movies = Movie.query.join(MovieGenre).join(MovieTag).join(MovieRating).filter(and_(
            or_(tags_filter if tags_filter is not None else default_value,
            genres_filter if genres_filter is not None else default_value), 
            ~Movie.id.in_([movie.id for movie in exclude_user_ratings(user_id, db)])
            )).group_by(Movie.id).order_by(db.func.avg(MovieRating.rating).desc()).all()

    return movies[:number] 

# RECOMMENDER 
def adapt_recommender(algo, data):
    return Recommender.adapt(algo).fit(data)

def get_recommendations(model, user_id, number):
    q, s = get_recommendations_query(model, user_id, number)
    return q.all(), s

def get_recommendations_query(model, user_id, number):
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

    return Movie.query.filter(Movie.id.in_(movie_ids)), scores

# GET 
def get_watchlist_movies():
    watchlist = WatchList.query.filter(WatchList.user_id==current_user.id).all()
    movie_ids = [watchlist_item.movie_id  for watchlist_item in watchlist]
    return movie_ids

def create_tag_list(): 
    # provide tags from database
    tags = MovieTag.query.all()
    tags = [tag.tag for tag in tags]
    tags = set(tags)
    tags = [tag for tag in tags]

    return tags
