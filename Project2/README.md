# AI_in_the_Web
Tobias Thelen 
University Osnabrück
Winter term 2023 

## Project 2: Build a movie Recommender system 
This repository is meant to provide our solution for project 2. 
The project is deployed on one of the servers provided for the course and reachable [through this link from within the university network](http://vm150.rz.uni-osnabrueck.de/user098/madvisor.wsgi)


### Authors 
Hannah Köster & Lisa Golla 

### Task 
Build a personalized recommender system with these components:

   - User management, including account creation, login, and logout
   - A database component for storing and retrieving movie details and ratings
   - A rating function where users can rate movies
   - A recommender function that recommends movies according to the user's previous ratings

### File Structure 
In the Project2 Folder the .py files and the sqlite data structure can be found. The templates folder contains the html files. The data folder contains the csv files. The static folder contains the style.css file and pictures that are used in our recommender.

### Usage 
Navigate to the Project2 Folder and run: flask --app recommender.py run. If you haven't initialized the database and the index yet, run this command first:  flask --app recommender.py initdb. !Note : initializing the database and index can take a while!

### Features 

    - Watchlist (Favorite Movies)
    - Prediction dispaly how much a user likes a movie for every movie
    - Several types of recommendation algorithms 
    - A filter method for movies (Genre, Tag, Searchbar(searching through: description, title, reviews, tag), Recommendation algorithm)
    - Apply a descending / ascending order based on certain values (runtime, average rating, title, match)
    - A Rating functionality 
    - Display information of movies (movie-poster, links to movie, runtime, description, reviews, average rating)
    - A detailed view for one single movie (youtube videos, similar movies)
    - A rated movies & recommendation overview display 

### Preview 
![website](link)
![grafik](link)


