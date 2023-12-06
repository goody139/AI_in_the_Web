import csv
from sqlalchemy.exc import IntegrityError
from flask_sqlalchemy import SQLAlchemy
from models import Movie, MovieGenre, Rating

def check_and_read_data(db):
    # check if we have movies in the database
    # read data if database is empty
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


    if Rating.query.count() == 0:
        with open('data/ratings.csv', newline='', encoding='utf8') as csvfile:
            # my code
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    # userId,movieId,rating,timestamp
                    # UserID, movieID, ratingValue
                    try:
                        userID = row[0]
                        movieID = row[1]
                        ratingValue = row[2]
                        ratings = Rating(user_id=userID, movie_id=movieID, rating_value=ratingValue)
                        db.session.add(ratings)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " ratings read")

