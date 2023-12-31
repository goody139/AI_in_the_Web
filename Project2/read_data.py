import csv
from sqlalchemy.exc import IntegrityError
from flask_sqlalchemy import SQLAlchemy
from models import Movie, MovieGenre, Rating, Tag, Link, Image
from helper_functions import get_movie_poster_links

def check_and_read_data(db):


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

    # RATINGS 
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


    # TAGS 
    if Tag.query.count() == 0:
        with open('data/tags.csv', newline='', encoding='utf8') as csvfile:
            # my code
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        userID = row[0]
                        movieID = row[1]
                        tag = row[2]
                        tags = Tag(user_id=userID, movie_id=movieID, tag=tag)
                        db.session.add(tags)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " tags read")   


    # LINKS 
    #Link.query.delete()
    #db.session.commit()
    if Link.query.count() == 0:
        with open('data/links.csv', newline='', encoding='utf8') as csvfile:
            # my code
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        movieid = row[0]
                        imdbid = str(row[1])
                        tmdbid = row[2]
                        links = Link(movieid=movieid, imdbid=imdbid, tmdbid=tmdbid)
                        db.session.add(links)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, "links read")   


    # IMAGES
    # alle movies in get poster function und dann jeden link für eine Movie ID 

    #id movieid link

    #Image.query.delete()
    #db.session.commit()

    if Image.query.count() == 0:
        print("Start")
        count = 0
        movies = Movie.query.all()
        #print(movies.id)
        #ml = {"movies": movies.id, "links": links}
        # for dictionary item in dictionary 
        handling_manually = []
        for movie in movies: 
            existing = Image.query.filter_by(movieid=movie.id).first()
            if existing == None:
                try:
                    # von movie
                    movieid = movie.id
                    link = get_movie_poster_links(movie)
                    if link == None: 
                        handling_manually.append(movie.id)
                        print("!!!!!!!!HANDLE MANUALLY!!!!!!!!!" + str(movie.id))
                    #link = links[count]
                    else: 
                        images = Image(movieid=movieid, link=link)
                        db.session.add(images)
                        db.session.commit()  # save data to database
                        #print("Commit")
                except IntegrityError:
                    print("Ignoring duplicate movie: " + title)
                    db.session.rollback()
                    pass
            count += 1
            if count % 100 == 0:
                print(count, "movie poster links saved")   
        print(handling_manually)