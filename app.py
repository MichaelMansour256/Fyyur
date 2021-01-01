# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for ,abort,jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
#from FlaskForm import Form
from forms import *
from flask_migrate import Migrate
import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
import re
import sys
from datetime import date

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# TODO(done): connect to a local postgresql database

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship('Show', backref="Venue", lazy=True)

    # TODO(done): implement any missing fields, as a database migration using Flask-Migrate
    def __repr__(self):
        return "<Venue {}>".format(self.name)


class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship('Show', backref="Artist", lazy=True)

    # TODO(done): implement any missing fields, as a database migration using Flask-Migrate
    def __repr__(self):
        return "<Artist {}>".format(self.name)


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return "<Show {}{}>".format(self.artist_id, self.venue_id)


# TODO(done) Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO(done): replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    venues = Venue.query.order_by('city').all()
    places = set()
    for venue in venues:
      places.add((venue.city, venue.state))

    for place in places:
        data.append({
            "city": place[0],
            "state": place[1],
            "venues": []
        })

    for venue in venues:
        num_upcoming_shows = 0
        shows = Show.query.filter_by(venue_id=venue.id).all()

        current_date = datetime.datetime.now()
        for show in shows:
            if show.start_time > current_date:
                num_upcoming_shows += 1

        for venue_place in data:
            if venue.state == venue_place['state'] and venue.city == venue_place['city']:
                venue_place['venues'].append({
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": num_upcoming_shows
                })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO(done): implement search on artists with partial string search. Ensure it is case-insensitive.

    search_term = request.form.get('search_term', '')
    results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
    for r in results:
        data = [{
            'id': r.id,
            'name': r.name,
            "num_upcoming_shows": len([show for show in r.shows if show.show_time > datetime.now()])

        }]
    response = {
        "count": len(results),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO(done): replace with real venue data from the venues table, using venue_id
    past_shows = []
    upcoming_shows = []
    data=[]
    current_time = datetime.datetime.now()
    shows = Show.query.filter_by(venue_id=venue_id).all()
    venue = Venue.query().get(venue_id)
    for show in shows:
      data = {
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": format_datetime(str(show.start_time))
      }
      # To determine if the show is in the future or in the past
      if show.start_time > current_time:
        upcoming_shows.append(data)

      else:
        past_shows.append(data)

      data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
      }

    #data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    print('555555555555555')
    # TODO(done): insert form data as a new Venue record in the db, instead
    form = VenueForm(request.form)
    # TODO(done): modify data to be the data object returned from db insertion
    if form.validate():
      try:
        newVenue = Venue(
          name=request.form['name'],
          city=request.form['city'],
          state=request.form['state'],
          address=request.form['address'],
          phone=request.form['phone'],
          facebook_link=request.form['facebook_link']
        )
        db.session.add(newVenue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
      except:
        print('An error occurred. Venue ' + request.form['name']+ ' could not be listed.')
        flash('An error occurred. Venue ' + request.form['name']+ ' could not be listed.')
      finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO(done): Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    venue = Venue.query.get(venue_id)
    if not venue:
      return redirect(url_for('index'))
    else:
      error=False
      try:
        db.session.delete(venue)
        db.session.commit()
      except:
        error = True
        db.session.rollback()
      finally:
        db.session.close()
      if error:
        flash(f'An error occurred deleting venue.')

        abort(500)
      else:
        return jsonify({
          'deleted': True,
          'url': url_for('venues')
        })

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO(done): replace with real data returned from querying the database
    data = []
    artists=Artist.query.all()
    for artist in artists:
      data.append({
        'id':artist.id,
        'name':artist.name
      })
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO(done): implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '').strip()
    artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()
    artist_data=[]
    for artist in artists:
      artist_data.append({
        'id':artist.id,
        'name':artist.name
      })
    response = {
        "count": len(artist_data),
        "data": artist_data
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO (done): replace with real venue data from the venues table, using venue_id
    past_shows = []
    upcoming_shows = []
    data = []
    current_time = datetime.datetime.now()
    shows = Show.query.filter_by(artist_id=artist_id).all()
    artist = Artist.query().get(artist_id)
    for show in shows:
      if show.start_time > current_time:
        upcoming_shows.append(data)

      else:
        past_shows.append(data)

      data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "facebook_link": artist.facebook_link,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
      }

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query().get(artist_id)
    artist = {
        "id": artist_id,
        "name": artist.name,
        "genres": ["Rock n Roll"],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "facebook_link": artist.facebook_link,
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": artist.image_link
    }
    # TODO(done): populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO(done): take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm()
    name = form.name.data.strip()
    city = form.city.data.strip()
    state = form.state.data
    phone = form.phone.data
    image_link = form.image_link.data.strip()
    website = form.website.data.strip()
    facebook_link = form.facebook_link.data.strip()
    if not form.validate():
      flash(form.errors)
      return redirect(url_for('edit_artist_submission', artist_id=artist_id))
    else:
      try:
        artist = Artist.query.get(artist_id)
        artist.name = name
        artist.city = city
        artist.state = state
        artist.phone = phone
        artist.image_link = image_link
        artist.website = website
        artist.facebook_link = facebook_link
        db.session.commit()
      except:
        db.session.rollback()
      finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue=Venue.query().get(venue_id)
    venue = {
        "id": venue_id,
        "name": venue.name,
        "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": True,
        "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
        "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    }
    # TODO(done): populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO(done): take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    try:
      form = VenueForm()
      venue = Venue.query.get(venue_id)
      name = form.name.data
      venue.name = name
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.facebook_link = form.facebook_link.data
      venue.website = form.website.data
      venue.image_link = form.image_link.data
      db.session.commit()
      flash('Venue ' + name + ' has been updated')
    except:
      db.session.rollback()
      flash('error occured on trying to update Venue')

    finally:
      db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO(done): insert form data as a new Venue record in the db, instead
    form = ArtistForm(request.form)
    # TODO(done): modify data to be the data object returned from db insertion
    if form.validate():
      try:
        newArtist=Artist(name=request.form['name'],city=request.form['city'],state=request.form['state'],phone=request.form['phone'],image_link=request.form['image_link'],facebook_link=request.form['facebook_link'])
        db.session.add(newArtist)
        db.session.commit()
        flash('Show  was successfully listed!')
      except:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        # TODO(done): on unsuccessful db insert, flash an error instead.
      finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO(done): replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    shows=db.session.query(Show).all()
    data=[]
    for show in shows:
      venue=Venue().query.get(show.venue_id)
      artist=Artist().query.get(show.artist_id)
      data.append({
         "venue_id": show.venue_id,
        "venue_name": venue.name,
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
        "start_time": show.start_time
      })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO(done): insert form data as a new Show record in the db, instead
    form = ShowForm(request.form)
    if form.validate():
      try:
        newShow=Show(artist_id=request.form['artist_id'],venue_id=request.form['venue_id'],start_time=request.form['start_time'])
        db.session.add(newShow)
        db.session.commit()
        flash('Show  was successfully listed!')
      except:
        # TODO(done): on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Show could not be listed.')
      finally:
        db.session.close()
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
