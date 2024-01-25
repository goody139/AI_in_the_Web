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
In the Project2 Folder the .py files and the sqlite data structure can be found. The templates folder contains the html files. The data folder contains the csv files. The static folder contains the style.css file and pictures that are used in our recommender. The whoosh_index folder contains files created by the whoosh library. In the instance folder there is an example database. 

### Usage 
Navigate to the Project2 Folder and run: *flask --app recommender.py run*. If you haven't initialized the database and the index yet, run this command first:  *flask --app recommender.py initdb*. **!Note : initializing the database and index can take a while!**

### Hint 
We used the lenskit library for the recommender algorithms, whoosh library for a searchbar index, sqlalchemy for a movie database and the TMDB API to access certain information about movies. Therefore an API key is required to make the code work. Create a new folder with the name *secrets* and name the file containing the API key *tmdb_api.txt*. All installation requirements can be found in the requirements.txt file. 

### Features 

   - Watchlist (Favorite Movies)
   - Prediction display how much a user likes a movie for every movie
   - Several types of recommendation algorithms (Popular, Bias, Fallback(UserUser), Fallback(ItemItem), ImplicitMF, Random)
   - A filter method for movies (Genre, Tag, searchbar(searching for: description, title, reviews, tag), Recommendation algorithm)
   - Apply a descending / ascending order based on certain values (runtime, average rating, title, match)
   - A Rating functionality
   - Display information of movies (movie-poster, links to movie, runtime, description, reviews, average rating)
   - A view for one movie in detail (youtube videos, similar movies)
   - A rated movies & recommendation overview display 

### Preview 
![website](link)
![grafik](link)


