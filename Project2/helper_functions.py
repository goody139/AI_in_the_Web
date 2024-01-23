from models import *
import requests 
from scipy.stats import pearsonr
from lenskit import *
from lenskit.algorithms.item_knn import ItemItem
from lenskit.algorithms.user_knn import UserUser
from lenskit.batch import predict
from lenskit.algorithms.basic import Bias, Fallback
from lenskit.metrics.predict import rmse
from lenskit.crossfold import partition_users
from lenskit.algorithms import Recommender, als
from lenskit import crossfold as xf
import pandas as pd
from requests.exceptions import HTTPError
from sqlalchemy import or_, and_
import random
from scipy.special import expit


""" This file contains several helper functions"""

def get_user_ratings(user_id):
    ratings = MovieRating.query.filter_by(user_id=user_id).all()
    #{rating.movie_id: rating.rating for rating in user_ratings}
    data = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating) for rating in ratings],
                        columns=['user', 'item', 'rating'])
    
    return data

def create_reviews(movies): 
    dateipfad = 'API_key.txt'

    # Versuche die Datei zu öffnen und ihren Inhalt zu lesen
    with open(dateipfad, 'r') as datei:
        inhalt = datei.read()
        #print(inhalt)

    reviews = []
    for movie in movies: 
            links = MovieLinks.query.filter_by(movieid=movie.id).first()
            #print(links.tmdbid)
            try: 
                url = "https://api.themoviedb.org/3/movie/{0}/reviews?api_key={1}".format(links.tmdbid, inhalt)
                response = requests.get(url)
                response = requests.get(url)

                response.raise_for_status()
                data = response.json()
                review = data.get('results', [])
                if review == []: 
                    reviews.append(review) 

                else: 
                    review = review[0].get('content', [])
                    reviews.append(review.split('\r\n\r\n') )

            except HTTPError:
                reviews.append([])
                


    return reviews 

def create_tag_list(): 
    # provide tags from database
    tags = MovieTag.query.all()
    tags = [tag.tag for tag in tags]
    tags = set(tags)
    tags = [tag for tag in tags]

    return tags

def prepare_movie_template(movies, user_id, prob): 

    # COLLECT ALL INFOS 
    MOVIEID, IMDB, TMBID = create_links(movies)  
    poster_links = movie_poster(movies) 
    tags = create_tags(movies) 
    contents = create_content(movies) 
    ratings = get_ratings(user_id, movies) 
    faves= get_fav_movies(user_id) 
    reviews = create_reviews(movies)
    probabilities = prob
    tag_list = create_tag_list()
    genre_list = ['Action', 'Adventure', 'Animation', 'Children', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western', 'Other']
    result_list = zip(movies, MOVIEID, IMDB, TMBID, poster_links, tags, contents, ratings, reviews, probabilities)
    item_list = zip([title.title for title in Movie.query.all()], [d.content for d in Movie.query.all()])
    print("READY with preparation")
    return [faves, tag_list, genre_list, result_list, item_list]

def movie_poster(movies): 
    link_list = []
    for movie in movies: 
        #print(movie.id)
        m = Image.query.filter_by(movieid=movie.id).first()

        if m == None: 
            link_list.append([])

        else: 
            link_list.append(m.link)
    
    return link_list

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

def filter_ratings(tag, genre): 

    # INITIALIZE 
    genres_filter = or_(*[MovieGenre.genre == g for g in genre]) if genre else None
    tags_filter = or_(*[MovieTag.tag == t for t in tag]) if tag else None

    # FILTER
    ratings = MovieRating.query.join(Movie).join(MovieGenre).join(MovieTag).filter(
        tags_filter if tags_filter is not None else True,
        genres_filter if genres_filter is not None else True,  
    ).all()

    return ratings

def filter_movies(tag, genre, number, include, user_id, db): 

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
        movies = Movie.query.join(MovieGenre).join(MovieTag).filter(
            tags_filter if tags_filter is not None else True,
            genres_filter if genres_filter is not None else True
        ).all()

    else: 
        movies = Movie.query.join(MovieGenre).join(MovieTag).filter(and_(
            or_(tags_filter if tags_filter is not None else default_value,
            genres_filter if genres_filter is not None else default_value), 
            ~Movie.id.in_([movie.id for movie in exclude_user_ratings(user_id, db)])
        )).all()    

    # SHUFFLE RESULTS
    random.shuffle(movies)

    return movies[:number]

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
def build_recommender(genre=[], tag=[], algo="0", number=10, user_id="", include="0", db=""):
    
    # APPLY filter 
    ratings = filter_ratings(tag, genre)
    data = pd.DataFrame([(rating.user_id, rating.movie_id, rating.rating, rating.timestamp) for rating in ratings],
                        columns=['user', 'item', 'rating', 'timestamp'])

    print("rec data", data)
    
    # DEFINE type of algorithm 
    if algo == "Similar to other movies you've watched":
        movies, scores = apply_model(ItemItem(1000), data, user_id, number)

    elif algo == "Other Users also liked": 
        movies, scores = apply_model(UserUser(1000), data, user_id, number)

    elif algo == "Best rated movies":
        movies = filter_best(tag, genre, number, db, include, user_id)
        scores = predict_rating([movie.id for movie in movies], user_id, data)
        
    elif algo == "0": 
        movies = filter_movies(tag, genre, number, include, user_id, db)
        scores = predict_rating([movie.id for movie in movies], user_id, data)

    return movies, scores


def apply_model(algo, data, user_id, number): 

    # APPLY MODEL
    model = Recommender.adapt(algo).fit(data)
    recs = model.recommend(int(user_id), number)

    # EXTRACT MOVIE IDS 
    for i in range (0, len(recs['item'])):
        movie_ids = [int(recs['item'][i])for i in range (len(recs['item']))]
        scores = [int(recs['score'][i])for i in range (len(recs['score']))]
    
    if len(recs['item']) == 0: 
        movie_ids = []

    # NORMALIZE
    scores = [round((score - 0) / (6 - 0) * 100) for score in scores]

    print(scores)

    return Movie.query.filter(Movie.id.in_(movie_ids)).all(), scores



def predict_rating(movie_id, user_id, data):
    print("predict print", movie_id, user_id, data)
    model =  Fallback(ItemItem(10), Bias()).fit(data)
    scores = model.predict_for_user(user_id, movie_id)
    #print(scores)
    # NORMALIZE
    scores = [round((score - 0) / (6 - 0) * 100) for score in scores]

    return scores


# -------------------------OLD VERSION RECOMMENDER -----------------------------
def pearson_similarity(user1_ratings, user2_ratings):
    common_movies = set(user1_ratings.keys()) & set(user2_ratings.keys())

    if not common_movies:
        return 0  # No common movies, similarity is 0

    user1_values = [user1_ratings[movie] for movie in common_movies]
    user2_values = [user2_ratings[movie] for movie in common_movies]

    correlation_coefficient, _ = pearsonr(user1_values, user2_values)
    return correlation_coefficient

def get_recommendations(userId, genre):
    user_ratings = get_user_ratings(userId)
    all_users = MovieRating.query.filter(MovieRating.user_id != userId).limit(100)

    print("calculating similarities")
    similarities = []
    for other_user in all_users:
        other_user_ratings = get_user_ratings(other_user.user_id)
        similarity = pearson_similarity(user_ratings, other_user_ratings)
        similarities.append((other_user.user_id, similarity))

    similarities.sort(key=lambda x: x[1], reverse=True)

    print("selecting recommended movies")
    recommended_movies = set()
    for other_user_id, similarity in similarities:
        other_user_ratings = get_user_ratings(other_user_id)
        for movie_id, rating in other_user_ratings.items():
            if movie_id not in user_ratings and genre != None:
                movie = MovieGenre.query.filter(MovieGenre.movie_id == movie_id).all()
                g = False
                for m in movie: 
                    if m.genre == genre: 
                        g = True
                if movie and g == True:
                    recommended_movies.add((movie_id, rating * similarity))

            elif movie_id not in user_ratings and genre == None: 
                print("should not be entered")
                recommended_movies.add((movie_id, rating * similarity))

    recommended_movies = list(recommended_movies)
    recommended_movies.sort(key=lambda x: x[1], reverse=True)

    movie_id_list = []
    for movie in recommended_movies: 
        if movie[0] not in movie_id_list:
            movie_id_list.append(movie[0])

    return movie_id_list[:10]




