
# Project 4 for the Full Stack Web Development Program

Project 4 for the Udacity Full Stack Web Developer Program.  The REST (Representational State Transfer) based catalog features any number of categories, and any number of items belonging to each category.  It also features the ability to log in as a user (using Googles OAuth2 capability), and CRUD (Create-Read-Update-Delete) functionality to add new items, and edit/delete existing items (belonging to the currently logged in user).

## Required Software

1. Python - the Flask framework (which was developed in the Python language) requires this to handle the web requests, it can be downloaded [here](https://www.python.org/downloads/).

2. Flask - is a web framework, quick web based applications can be developed.  The framework can be installed via the instructions
[here](http://flask.pocoo.org/docs/0.12/installation/#installation).

3. SQLAlchemy - is an object relational mapper (ORM) which is used to map Python objects to database entities.  The instructions to install it are located [here](http://docs.sqlalchemy.org/en/latest/intro.html#installation).

4. SASS (optional) - SASS is short for Syntactically Awesome Stylesheets.  The static/css/styles.sass is the file to run the sass program on.  The styles stylesheet (static/css/styles.css) was generated from the sass file.  It can be installed via the instructions [here](http://sass-lang.com/install).

## How to install and start

1. Clone the Project Repository:<br /><br />```https://github.com/SoftwareDevPro/P4_FSWD_Item_Catalog```

2. Change to the project directory:<br /><br />```cd P4_FSWD_Item_Catalog```

3. Execute the database setup script:<br /><br />```python database_setup.py```

4. Execute the database initialization script (optional if you want some test data):<br /><br />```python database_init_with_test_data.py```

5. Start the web application:<br /><br />```python application.py```
