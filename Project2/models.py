from flask_sqlalchemy import SQLAlchemy
from flask_user import UserMixin

db = SQLAlchemy()

# Define the User data-model.
# NB: Make sure to add flask_user UserMixin as this adds additional fields and properties required by Flask-User
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    username = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    email_confirmed_at = db.Column(db.DateTime())

    # User information
    first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')


class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
    poster_path = db.Column(db.String(255), nullable=False, server_default='')
    blurb = db.Column(db.String(1024), nullable=False, server_default='')
    release_date = db.Column(db.Date, index=True)
    runtime = db.Column(db.Integer)
    genres = db.relationship('MovieGenre', backref='movie', lazy=True)
    links = db.relationship('MovieLinks', backref='movie', lazy=True)
    tags = db.relationship('MovieTag', backref='movie', lazy=True)
    reviews = db.relationship('MovieReview', backref='movie', lazy=True)
    video_links = db.relationship('VideoLink', backref='movie', lazy=True)
   
class MovieGenre(db.Model):
    __tablename__ = 'movie_genres'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    genre = db.Column(db.String(255), nullable=False, server_default='')

class MovieLinks(db.Model):
    __tablename__ = 'movie_links'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    imdb_id = db.Column(db.String(255), nullable=False)  # make this a string to avoid leading 0s getting stripped
    tmdb_id = db.Column(db.Integer, nullable=False)

class MovieTag(db.Model):
    __tablename__ = 'movie_tags'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tag = db.Column(db.String(255), nullable=False, server_default='')
    timestamp = db.Column(db.Integer, nullable=False)

class MovieRating(db.Model):
    __tablename__ = 'movie_ratings'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.Integer, nullable=False)


class WatchList(db.Model):
    __tablename__ = 'wachlist'
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, primary_key=True)
    timestamp = db.Column(db.Integer, nullable=False)


class MovieReview(db.Model):
    __tablename__ = 'movie_reviews'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    review = db.Column(db.String(2048), nullable=False, server_default='')


class VideoLink(db.Model):
    __tablename__ = 'video_links'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    link = db.Column(db.String(255), nullable=False, server_default='')

class SimilarMovie(db.Model):
    __tablename__ = 'similar_movies'
    id = db.Column(db.Integer, primary_key=True)
    query_tmdb_id = db.Column(db.Integer, nullable=False)
    sim_movie_tmdb_id = db.Column(db.Integer, nullable=False)
