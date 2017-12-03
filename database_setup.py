
# Imports
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

# Construct the base class for class definitions.
Base = declarative_base()

# CREATE TABLE user (
#   id INTEGER NOT NULL,
#   name VARCHAR(250) NOT NULL,
#   email VARCHAR(250) NOT NULL,
#   PRIMARY KEY (id) )
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    email = Column(String(250), nullable = False)

# CREATE TABLE category (
#   id INTEGER NOT NULL,
#   name VARCHAR(255) NOT NULL,
#   user_id INTEGER,
#   PRIMARY KEY (id), FOREIGN KEY(user_id) REFERENCES user (id) )
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key = True)
    name = Column(String(255), nullable = False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="category")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return { 'name' : self.name, 'id': self.id }

# CREATE TABLE item (
#   id INTEGER NOT NULL,
#   name VARCHAR(250) NOT NULL,
#   date DATETIME NOT NULL,
#   description VARCHAR(250),
#   picture VARCHAR(250),
#   category_id INTEGER,
#   user_id INTEGER,
#   PRIMARY KEY (id),
#   FOREIGN KEY(category_id) REFERENCES category (id),
#   FOREIGN KEY(user_id) REFERENCES user (id) )
class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(String(250))
    picture = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category, backref=backref('item', cascade='all, delete'))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, backref="items")

    @property
    def serialize(self):
        """Return the object data in a serializeable format."""
        return {
            'name'          : self.name,
            'id'            : self.id,
            'description'   : self.description,
            'picture'       : self.picture,
            'category'      : self.category.name
        }

# Create the database engine
engine = create_engine('sqlite:///catalog.db')

# ... and use the engine to create the tables.
Base.metadata.create_all(engine)

#
