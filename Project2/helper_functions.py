from imdb import IMDb
from models import Movie, MovieGenre, Rating, Tag, Link, Image
import requests 
from scipy.stats import pearsonr

""" An api key is needed """

# Function to get movie poster link
def get_movie_poster_links(movie):
    # Dateipfad zur Textdatei
    dateipfad = 'API_key.txt'

    # Versuche die Datei zu öffnen und ihren Inhalt zu lesen
    with open(dateipfad, 'r') as datei:
        inhalt = datei.read()

    links = Link.query.filter_by(movieid=movie.id).first()
    #print(links.tmdbid)
    url = "https://api.themoviedb.org/3/movie/{0}?api_key={1}".format(links.tmdbid,inhalt)
    data = requests.get(url)
    print(data)
    data = data.json()
    #print(data)
    if 'poster_path' not in data:
        return None
    poster_path = data['poster_path']
    if poster_path == None: 
        return None
    full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    return full_path 


# get content? from API? 
def create_content(movies): 
    dateipfad = 'API_key.txt'

    # Versuche die Datei zu öffnen und ihren Inhalt zu lesen
    with open(dateipfad, 'r') as datei:
        inhalt = datei.read()
        #print(inhalt)

    content = []
    for movie in movies: 
        links = Link.query.filter_by(movieid=movie.id).first()
        #print(links.tmdbid)
        url = "https://api.themoviedb.org/3/movie/{0}?api_key={1}".format(links.tmdbid,inhalt)
        data = requests.get(url)
        data = data.json()
        #print(data)
        if 'overview' not in data:
            return None
        c = data['overview']
        content.append(c)

        if content== None: 
            return None
        #full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    return content 




def create_links(movies): 
    
    MOVIEID = []
    IMDB = []
    TMBID = []
    for movie in movies: 
        MOVIEID.append("https://movielens.org/movies/" + str(movie.id))
        links = Link.query.filter_by(movieid=movie.id).first()        
        IMDB.append("http://www.imdb.com/title/tt"+ str(links.imdbid) + "/")
        TMBID.append("https://www.themoviedb.org/movie/"+ str(links.tmdbid))

    return MOVIEID, IMDB, TMBID


def movie_poster(movies): 
    link_list = []
    for movie in movies: 
        m = Image.query.filter_by(movieid=movie.id).first()
        if m == None: 
            return None
        link_list.append(m.link)
    
    return link_list


def create_tags(movies): 
    final_list = []
    for movie in movies: 
        tags = Tag.query.filter_by(movie_id=movie.id).limit(4)
        tag_list = []
        for t in tags: 
            tag_list.append(t.tag)
        tag_list = set(tag_list)
        final_list.append(tag_list)
    print("final tag list")
    print(final_list)
        
    
    return final_list

def get_movies(movie_ids):
    movies = []
    for id in movie_ids: 
        movie = Movie.query.get(id)
        movies.append(movie)
    return movies

def get_user_ratings(user_id):
    user_ratings = Rating.query.filter_by(user_id=user_id).all()
    return {rating.movie_id: rating.rating_value for rating in user_ratings}


def pearson_similarity(user1_ratings, user2_ratings):
    common_movies = set(user1_ratings.keys()) & set(user2_ratings.keys())

    if not common_movies:
        return 0  # No common movies, similarity is 0

    user1_values = [user1_ratings[movie] for movie in common_movies]
    user2_values = [user2_ratings[movie] for movie in common_movies]

    correlation_coefficient, _ = pearsonr(user1_values, user2_values)
    return correlation_coefficient



# sowas wie genre als option? 
# wenn knopf gedrückt wird für bestimmtes genre?    
def get_recommendations(userId, genre):
    user_ratings = get_user_ratings(userId)
    all_users = Rating.query.filter(Rating.user_id != userId).limit(100)

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