
# Imports
from flask import Flask, render_template
from flask import url_for, request, redirect, flash, jsonify, make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import *
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import os
import random
import string
import datetime
import json
import httplib2
import requests
from functools import wraps

# Create the flask application instance.
app = Flask(__name__)

# Google gconnect details
CLIENT_FILE = 'client_secrets.json'
CLIENT_ID = "98088597641-c1efsmh1cvu2h0mq6rir6h7av6ignuu6.apps." \
            "googleusercontent.com"
OAUTH_URL = 'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
REVOKE_URL = 'https://accounts.google.com/o/oauth2/revoke?token=%s'
USER_INFO_URL = 'https://www.googleapis.com/oauth2/v1/userinfo'

# Connect to database
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

# Create a session
DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    """ Checks to see whether a user is currently logged in. """
    @wraps(f)
    def x(*args, **kwargs):
        # Make sure user is logged in, and if not redirect to the login page.
        if 'username' not in login_session:
            print ('username not in login_session')
            return redirect('/login')
        return f(*args, **kwargs)
    return x


@app.route('/login')
def show_login():
    """ Creates a anti-forgery token, and renders the login template. """

    # Create an anti-forgery state token to save off in the session state.
    ascii_characters = string.ascii_uppercase + string.digits
    state = ''.join(random.choice(ascii_characters) for x in range(32))

    # Save off the state token in the login session state.
    login_session['state'] = state

    # and render the login template.
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """ the Google connect method """

    # Validate state token
    if request.args.get('state') != login_session['state']:

        # if the state tokens do not match then, create an error message,
        # and return an error (401 - unauthorized access)
        str_error = 'Invalid state parameter.'
        response = make_response(json.dumps(str_error), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain the authorization code
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Create a Flow object from the client_secrets JSON file.
        oauth_flow = flow_from_clientsecrets(CLIENT_FILE, scope='')
        oauth_flow.redirect_uri = 'postmessage'

        #  Using the Flow object, exchange the authorization for a
        # Credentials object.
        credentials = oauth_flow.step2_exchange(code)

    except Exception:
        # If something fails at this step, create the error message,
        # and return a 401 (unauthorized access) error.
        str_error = 'Failed to upgrade the authorization code.'
        response = make_response(json.dumps(str_error), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Create the URL that will be used to verify the access token is valid.
    access_token = credentials.access_token
    url = (OAUTH_URL % access_token)

    # Submit the verification request, parse the response, and create a result.
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was any issue in the access token information, bail,
    # with a 500 error (internal server error)
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the token is used for the intended user.
    g_id = credentials.id_token['sub']
    if result['user_id'] != g_id:
        # if the unique user id doesn't match, create an error string.
        str_error = 'Tokens user ID doesnt match given user ID.'

        # and return a 401 (unauthorized access) error
        response = make_response(json.dumps(str_error), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the token is valid for this application.
    if result['issued_to'] != CLIENT_ID:
        # if there isn't a match in the client id's then create an error
        # string, and return a 401 response (unauthorized access).
        str_error = "Tokens client ID does not match apps."
        response = make_response(json.dumps(str_error), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Grab the stored access token, and the google user id.
    stored_token = login_session.get('access_token')
    stored_g_id = login_session.get('g_id')

    # if the stored token is something, and the google user id's match...
    if stored_token is not None and g_id == stored_g_id:
        # then return a success (200) message response
        str_msg = 'Current user is already connected.'
        response = make_response(json.dumps(str_msg), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the token and google user id in the session for later use.
    login_session['access_token'] = access_token
    login_session['g_id'] = g_id

    # Get user information
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(USER_INFO_URL, params=params)
    data = answer.json()

    # Save off the user name, email address, and picture.
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['picture'] = data['picture']

    # Verify that the user exists in the database.
    try:
        user = session.query(User).filter_by(email=data['email']).one()
    except Exception:
        # ... and if it doesn't then create the user in the database.
        new_user = User(name=data['name'], email=data['email'])
        session.add(new_user)
        session.commit()
        user = session.query(User).filter_by(email=data['email']).one()

    user_id = user.id

    # Save off the user information in the session.
    login_session['user_id'] = user_id

    # Create the output for the login page.
    output = '<h1>Welcome, ' + login_session['username'] + '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style="width: 300px; height: 300px; border-radius: 50px;">'

    # Display a flash message so the user knows they are logged in.
    flash("You are logged in as %s" % login_session['username'])

    # Return the built up output string.
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """ Revokes the  logged in users token, and resets login session."""

    # Grab the access token to see if it exists...
    access_token = login_session.get('access_token')
    if access_token is None:
        # ... and if not, there is nobody to disconnect.
        str_error = "Current user not connected."
        response = make_response(json.dumps(str_error), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Invoke the revoke URL to disconnect.
    url = REVOKE_URL % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    # and if it was successful (indicated by the 200 ok code), then...
    if result['status'] == '200':
        # ... reset the login session information
        for item in ['access_token', 'g_id', 'username', 'email', 'picture']:
            del login_session[item]

        # ... then redirect to the show catalog, and display a success message.
        response = redirect(url_for('show_catalog'))
        flash("You are now logged out.")
        return response
    else:
        # Otherwise return an error (bad request, 400).
        str_error = "Failed to revoke token for given user."
        response = make_response(json.dumps(str_error, 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
@app.route('/catalog/')
def show_catalog():
    """ Displays the entire catalog """

    # query out the categories (sorted by the name)
    c = session.query(Category).order_by(asc(Category.name))

    # query out the items from the database (ordering by the date descending)
    i = session.query(Item).order_by(desc(Item.date))

    # Render the entire catalog (the categories , and individual items)
    return render_template('catalog.html', categories=c, items=i)


@app.route('/catalog/<path:category_name>/item/')
def show_category(category_name):
    """ The route to show a specific category. """

    # Get all the categories,
    categories = session.query(Category).order_by(asc(Category.name))

    # and then get out the specific category from the categories.
    category = session.query(Category).filter_by(name=category_name).one()

    # and then get all the items for the category.
    items = session.query(Item) \
                   .filter_by(category=category) \
                   .order_by(asc(Item.name)) \
                   .all()

    # Grab the count of items for the category, and items for the user id.
    count = session.query(Item).filter_by(category=category).count()
    creator = session.query(User).filter_by(id=category.user_id).one()

    # if the user isn't logged in, or the creator user id doesn't match the
    # login session user id.
    if 'username' not in login_session or \
       creator.id != login_session['user_id']:
        # then render all the items to the user.
        return render_template('all_items.html',
                               category=category.name,
                               categories=categories,
                               items=items,
                               count=count)
    else:
        # otherwise query out the user, and show the items for the user.
        user = session.query(User).filter_by(id=login_session['user_id']).one()
        return render_template('show_item.html',
                               category=category.name,
                               categories=categories,
                               items=items,
                               count=count,
                               user=user)


@app.route('/catalog/<path:category_name>/<path:item_name>/')
def show_item(category_name, item_name):
    """ The route to display a specific item. """

    # Query out the specific item, creators user id, and the categories.
    item = session.query(Item).filter_by(name=item_name).one()
    creator = session.query(User).filter_by(id=item.user_id).one()
    categories = session.query(Category).order_by(asc(Category.name))

    # if the user isn't logged in or the creator, render the non-editable
    # / non-deletable item.
    if 'username' not in login_session or \
       creator.id != login_session['user_id']:
        return render_template('all_itemdetail.html',
                               item=item,
                               category=category_name,
                               categories=categories,
                               creator=creator)
    else:
        # otherwise render the editable / deletable item.
        return render_template('item_detail.html',
                               item=item,
                               category=category_name,
                               categories=categories,
                               creator=creator)


@app.route('/catalog/add', methods=['GET', 'POST'])
@login_required
def add_item():
    """ Handles the addition of an item to the catalog. """

    # Query out all the categories from the database.
    c = session.query(Category).all()

    # If its an POST request...
    if request.method == 'POST':
        # Create a new item using the form request fields.

        # Get the category name, and query out that category from the database.
        cat_name = request.form['category']
        one_cat = session.query(Category).filter_by(name=cat_name).one()

        # Create the new item using the data in the form.
        new_item = Item(name=request.form['name'],
                        description=request.form['description'],
                        picture=request.form['picture'],
                        category=one_cat,
                        date=datetime.datetime.now(),
                        user_id=login_session['user_id'])

        # Add item to the session, and then commit the item to the database.
        session.add(new_item)
        session.commit()

        # Display the success flash message.
        flash('Item Successfully Added To Catalog!')

        # and then redirect to show the catalog.
        return redirect(url_for('show_catalog'))
    else:
        # if its not post, then simply render the add_item html
        return render_template('add_item.html', categories=c)


@app.route('/catalog/<path:category_name>/<path:item_name>/edit',
           methods=['GET', 'POST'])
@login_required
def edit_item(category_name, item_name):
    """ The route to edit an existing item. """

    # Query out the specific item, and all the categories
    item = session.query(Item).filter_by(name=item_name).one()
    categories = session.query(Category).all()

    # Verify that the logged in user is the creator of the item.
    creator = session.query(User).filter_by(id=item.user_id).one()

    if creator.id != login_session['user_id']:
        # and if not display an error message, and redirect.
        flash("You cannot edit this item. This item belongs to %s" %
              creator.name)

        return redirect(url_for('show_catalog'))

    if request.method == 'POST':
        # if the name is in the request form object, then pull it.
        if request.form['name']:
            item.name = request.form['name']
        # if the description is in the request form object, then pull it.
        if request.form['description']:
            item.description = request.form['description']
        # if the picture is in the request form object, then pull it.
        if request.form['picture']:
            item.picture = request.form['picture']
        # if the category is in the request form object, then pull it.
        if request.form['category']:
            category = session.query(Category) \
                              .filter_by(name=request.form['category']).one()

            item.category = category

        # Set the edit time to the current time.
        time = datetime.datetime.now()
        item.date = time

        # Add the edited item to the session, and save it.
        session.add(item)
        session.commit()

        # Display a success message and redirect.
        flash('Item Successfully Edited!')

        return redirect(url_for('show_category',
                        category_name=item.category.name))
    else:
        # if  not the post method then simply render the template for editing.
        return render_template('edit_item.html',
                               item=item,
                               categories=categories)


@app.route('/catalog/<path:category_name>/<path:item_name>/delete',
           methods=['GET', 'POST'])
@login_required
def delete_item(category_name, item_name):
    """ The route to delete an existing item. """

    # Query out the specific item, category, and then all categories.
    item = session.query(Item).filter_by(name=item_name).one()
    category = session.query(Category).filter_by(name=category_name).one()
    categories = session.query(Category).all()

    # Verify that the user is the owner/creator of the item.
    creator = session.query(User).filter_by(id=login_session['user_id']).one()

    # and if not
    if creator.id != login_session['user_id']:
        # then display an error message, and redirect to the catalog.
        flash("You cannot delete this item. This item belongs to %s" %
              creator.name)

        return redirect(url_for('show_catalog'))

    # If its a post request method.
    if request.method == 'POST':
        # then delete the item in the session, and commit it.
        session.delete(item)
        session.commit()

        #  display a success message, and redirect.
        flash('Item Successfully Deleted: ' + item.name + '!')
        return redirect(url_for('show_category',
                                category_name=category.name))
    else:
        # if not post, simply display the basic delete item template.
        return render_template('delete_item.html', item=item)


@app.route('/catalog/JSON')
def all_items_json():
    """ Returns all items in the catalog in JSON form. """

    # Query out all the categories
    categories = session.query(Category).all()

    # Serialize each of the categories.
    cat_dict = [c.serialize for c in categories]

    # for each serialized category ...
    for c in range(len(cat_dict)):
        # Query out the items for the current category.
        query = session.query(Item).filter_by(category_id=cat_dict[c]["id"])

        # Serialize the returned items.
        items = [i.serialize for i in query.all()]

        # if we have serialized items, save them off.
        if items:
            cat_dict[c]["Item"] = items

    # and return the JSON form of the results.
    return jsonify(Category=cat_dict)


@app.route('/catalog/category/JSON')
def categories_json():
    """ Returns all the categories in the catalog in JSON form. """

    # Query out all the categories.
    categories = session.query(Category).all()

    # and return the JSON form of it.
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/catalog/item/JSON')
def items_json():
    """ Returns the JSON form of all items in the catalog. """

    # Pull all the items ...
    items = session.query(Item).all()

    # ... and return the JSON form of each item.
    return jsonify(items=[i.serialize for i in items])


@app.route('/catalog/<path:category_name>/item/JSON')
def category_items_json(category_name):
    """ Returns the JSON form of all items in specified category. """

    # Query out the specific category (should only be one).
    category = session.query(Category).filter_by(name=category_name).one()

    # Query out all of the items in the category.
    items = session.query(Item).filter_by(category=category).all()

    # ... and return the JSON form of each item.
    return jsonify(items=[i.serialize for i in items])


@app.route('/catalog/<path:category_name>/<path:item_name>/JSON')
def item_json(category_name, item_name):
    """ Returns the JSON form of a specific item. """

    # Query out the specific category (should only be one).
    c = session.query(Category).filter_by(name=category_name).one()

    # Query out the specific item.
    item = session.query(Item).filter_by(name=item_name, category=c).one()

    # ... and return the JSON form of each item.
    return jsonify(item=[item.serialize])


if __name__ == '__main__':
    # Set the secret key, allow for debugging, and start the application.
    app.secret_key = 'SECRET_KEY'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)

#
