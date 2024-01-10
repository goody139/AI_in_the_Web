import csv
from sqlalchemy.exc import IntegrityError
from models import *
import requests
from time import sleep
from datetime import date

def get_tmdb_data_for_movie(tmdb_id, apikey_path="secrets/tmdb_api.txt"):
    # read in the api key
    api_key = ""
    with open(apikey_path, "r") as file:
        api_key = file.read()
    # request data for the movie
    response = requests.get("https://api.themoviedb.org/3/movie/{}?api_key={}&append_to_response=videos,reviews".format(tmdb_id, api_key))
    while response.status_code == 429:
        sleep(1)
        response = requests.get("https://api.themoviedb.org/3/movie/{}?api_key={}&append_to_response=videos,reviews".format(tmdb_id, api_key))
    return response


def check_and_read_data(db):
    # check if we have movies in the database
    # read data if database is empty
    
    # MOVIES 
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

    # LINKS
    # check if we have links in the database
    # read data if database is empty
    if MovieLinks.query.count() == 0:
        # read movies from csv
        with open('data/links.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        movie_id = row[0]
                        imdb_id = row[1]
                        tmdb_id = row[2]
                        movie_links = MovieLinks(movie_id=movie_id, imdb_id=imdb_id, tmdb_id=tmdb_id)

                        movie_object = Movie.query.filter(Movie.id==movie_id)
                        r = get_tmdb_data_for_movie(tmdb_id)

                        try:
                            if r.json()['poster_path']:
                                poster_path = "https://image.tmdb.org/t/p/w500" + r.json()['poster_path']
                                movie_object.update({'poster_path': poster_path})
                        except KeyError:
                            pass
                        
                        try:
                            if r.json()['overview']:
                                movie_object.update({'blurb': r.json()['overview']})
                        except KeyError:
                            pass

                        try:
                            if r.json()['release_date']:
                                movie_object.update({'release_date': date.fromisoformat(r.json()['release_date'])})
                        except KeyError:
                            pass

                        try:
                            if r.json()['runtime']:
                                movie_object.update({'runtime': r.json()['runtime']})
                        except KeyError:
                            pass

                        # [TODO] create rating objects and add them to the database
                        # try:
                        #     if r.json()['reviews']:
                        #         data = response.json()
                        #         review = data.get('results', [])
                        #         reviews = []
                        #         if review == []: 
                        #             reviews.append(review) 

                        #         else: 
                        #             review = review[0].get('content', [])
                        #             reviews.append(review.split('\r\n\r\n') )

                        # except KeyError:
                        #     pass

                        db.session.add(movie_links)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie with id: " + movie_id)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movie links read")


    # TAGS
    # check if we have tags in the database
    # read data if database is empty
    if MovieTag.query.count() == 0:
        # read tags from csv
        with open('data/tags.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    user_id = row[0]
                    movie_id = row[1]
                    tag = row[2]
                    timestamp = row[3]
                    movie_tag = MovieTag(user_id=user_id, movie_id=movie_id, tag=tag, timestamp=timestamp)
                    db.session.add(movie_tag)
                    db.session.commit()  # save data to database
                count += 1
                if count % 100 == 0:
                    print(count, " tags read")

    # RATINGS
    # check if we have ratings in the database
    # read data if database is empty
    if MovieRating.query.count() == 0:
        # read tags from csv
        with open('data/ratings.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    user_id = row[0]
                    movie_id = row[1]
                    rating = row[2]
                    timestamp = row[3]
                    movie_rating = MovieRating(user_id=user_id, movie_id=movie_id, rating=rating, timestamp=timestamp)
                    db.session.add(movie_rating)
                    db.session.commit()  # save data to database
                count += 1
                if count % 100 == 0:
                    print(count, " ratings read")

