
# Imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from database_setup import *

# Create the database engine using the SQLLite Provider, and catalog database.
engine = create_engine('sqlite:///catalog.db')

# Bind the engine to the metadata of the Base class.
Base.metadata.bind = engine

# Create the DBSession instance.
DBSession = sessionmaker(bind=engine)
session = DBSession()

def empty_database(session):
    """ Empties out each of the tables in the database. """
    print ("Emptying out database...")
    # Delete all the categories, items, users (if any exist).
    for table in [ Category, Item, User ]:
        session.query(table).delete()

def add_user(session, **kwargs):
    """ Adds the specified user to the database. """
    name, email = kwargs['name'], kwargs['email']
    print ("Adding user [{},{}] to database...".format(name, email))
    user = User(name=name, email=email)
    session.add(user)
    session.commit()

def add_category(session, **kwargs):
    """ Adds the specified category to the database. """
    category, user_id = kwargs['name'], kwargs['user_id']
    print ("Adding category [{},{}] to database...".format(category, user_id))
    category = Category(name=category, user_id=user_id)
    session.add(category)
    session.commit()

def add_item(session, **kwargs):
    """ Adds the specified item to the database. """
    name = kwargs['name']
    date = kwargs['date']
    desc = kwargs['desc']
    pic_url = kwargs['url']
    category_id = kwargs['cid']
    user_id = kwargs['uid']
    print ("Adding item [{},{}] to database...".format(name, desc))
    item = Item(name=name,
                date=date,
                description=desc,
                picture=pic_url,
                category_id=category_id,
                user_id=user_id)
    session.add(item)
    session.commit()

def add_test_data(session):

    # Add test users
    add_user(session, name="Chris Adamson", email="software.pro.08@gmail.com")

    # Add test categories
    add_category(session, name="Cars", user_id=1)
    add_category(session, name="Music", user_id=1)
    add_category(session, name="Electronics", user_id=1)
    add_category(session, name="Books", user_id=1)
    add_category(session, name="Toys", user_id=1)

    # Add test items
    add_item(session,
             name="Hyundai Veloster",
             date=datetime.datetime.now(),
             desc="Hyundai Veloster",
             url="https://tinyurl.com/y9vzru5f",
             cid=1,
             uid=1)

    add_item(session,
             name="Mitsubishi Outlander",
             date=datetime.datetime.now(),
             desc="Mitsubishi Outlander",
             url="https://tinyurl.com/ybbuyzkc",
             cid=1,
             uid=1)

    add_item(session,
             name="Puddle of Mudd",
             date=datetime.datetime.now(),
             desc="Puddle of Mudd - Come Clean",
             url="https://tinyurl.com/ycadkqe8c",
             cid=2,
             uid=1)

    add_item(session,
             name="Ozzy Osbourne",
             date=datetime.datetime.now(),
             desc="Ozzy Osbourne - Scream",
             url="https://tinyurl.com/y7vl2nul",
             cid=2,
             uid=1)

    add_item(session,
             name="Samsung",
             date=datetime.datetime.now(),
             desc="Samsung - S8+",
             url="https://tinyurl.com/y88jzdod",
             cid=3,
             uid=1)

    add_item(session,
             name="Garmin",
             date=datetime.datetime.now(),
             desc="Garmin - GPS",
             url="https://tinyurl.com/y7quxplq",
             cid=3,
             uid=1)

    add_item(session,
             name="1984",
             date=datetime.datetime.now(),
             desc="1984 - George Orwell",
             url="https://tinyurl.com/y8o9s9pw",
             cid=4,
             uid=1)

    add_item(session,
             name="Nikki Sixx",
             date=datetime.datetime.now(),
             desc="Nikki Sixx - Heroin Diaries",
             url="https://tinyurl.com/y7quxplq",
             cid=4,
             uid=1)

    add_item(session,
             name="Harry Potter",
             date=datetime.datetime.now(),
             desc="Harry Potter - Funko Pop",
             url="https://tinyurl.com/y944lp26",
             cid=5,
             uid=1)

    add_item(session,
             name="Strawberry Shortcake",
             date=datetime.datetime.now(),
             desc="Strawberry Shortcake - Funko Pop",
             url="https://tinyurl.com/yb25ex43",
             cid=5,
             uid=1)

if __name__ == '__main__':

    # Empty the database
    empty_database(session)

    # Add the test data
    add_test_data(session)

    print "Finished... the database has been populated with test data."

#
