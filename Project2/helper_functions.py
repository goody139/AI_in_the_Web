from imdb import IMDb
from models import Movie, MovieGenre, Rating, Tag, Link, Image
import requests 

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
    print(final_list)
        
    
    return final_list


        