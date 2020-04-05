#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime
from flask_migrate import Migrate
import sys


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(250))
    shows = db.relationship('Show', backref='venue')


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(250))
    shows = db.relationship('Show', backref='artist')

class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  start_time = db.Column(db.DateTime, nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  cities = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)
  #print(cities, file=sys.stderr)

  data = []
  for c in cities:
    venues_in_city = db.session.query(Venue.id, Venue.name).filter(Venue.city == c[0]).filter(Venue.state == c[1])
    #print(venues_in_city, file=sys.stderr)
    data.append({
      "city": c[0],
      "state": c[1],
      "venues": venues_in_city
    })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  venues = db.session.query(Venue).filter(Venue.name.ilike('%' + search_term + '%')).all()
  data = []

  for venue in venues:
    num_upcoming_shows = 0
    shows = db.session.query(Show).filter(Show.venue_id == venue.id)
    for show in shows:
      if (show.start_time > datetime.now()):
        num_upcoming_shows += 1;
      
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": num_upcoming_shows
    })

  response={
    "count": len(venues),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # set lists for past shows and coming shows
  past_shows=[]
  coming_shows=[]
 # import shows for the venue and put in seperate list  
  venue_shows = db.session.query(Show).filter(Show.venue_id == venue_id)
  #print(venue_shows, file=sys.stderr)
  

  # Cycle through artist_shows and add to relevant list
  for s in venue_shows:
    artist = db.session.query(Artist.name, Artist.image_link).filter(Artist.id == s.artist_id).one()
    show_add = {
      "artist_id": s.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": s.start_time.strftime('%m/%d/%Y')
      }
      
    if (s.start_time < datetime.now()):
      past_shows.append(show_add)
    else:
      coming_shows.append(show_add)

  #import artist query
  venue = db.session.query(Venue).filter(Venue.id == venue_id).one()

  # Split the genres entry
  tmp_genres = venue.genres.split(',')

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": tmp_genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": coming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(coming_shows)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  try:
    # pull data from the form and enter the variables in the data variable
    tmp_genres = request.form.getlist('genres')
    data = Venue(name = form.name.data, 
    city = form.city.data, 
    state = form.state.data, 
    address = form.address.data, 
    phone = form.phone.data,
    #genres = form.genres.data,
    genres = ','.join(tmp_genres),
    facebook_link = form.facebook_link.data,  
    website = form.website_link.data,   
    image_link = form.image_link.data,
    seeking_talent = form.seeking_talent.data,
    seeking_description = form.seeking_description.data)
    # does the venue already exist?
    venue_exists = bool(Venue.query.filter_by(state = data.state, address = data.address, name = data.name).first())

    if venue_exists==True:
      #Venue is already in the db so flash warning
      flash('Venue ' + data.name + ' could not be listed as it is already in the system.')
    else:
      # Venue isn't in the db so can be added
      db.session.add(data)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')
    ################################################################################
    # Would expect the redirect to be to the current page for the user to try again.
    #################################################################################

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    db.session.query(Venue).filter(Venue.id == venue_id).delete()
    db.session.commit()
    flash('Venue was successfully deleted!')
  except:
    flash('An error occurred. Venue could not be deleted.')
  finally:
    db.session.close()
  return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = db.session.query(Artist.id, Artist.name)
  data=[]

  for a in artists:
    data.append({
      "id": a[0],
      "name": a[1]
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  artists = db.session.query(Artist).filter(Artist.name.ilike('%' + search_term + '%')).all()
  data = []

  for artist in artists:
    num_upcoming_shows = 0
    shows = db.session.query(Show).filter(Show.artist_id == artist.id)
    for show in shows:
      if(show.stat_time > datetime.now()):
        num_upcoming_shows += 1;
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": num_upcoming_shows
    })
  response={
    "count": len(artists),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # set lists for past shows and coming shows
  past_shows=[]
  coming_shows=[]
 # import shows for the artist and put in seperate list  
  artist_shows = db.session.query(Show).filter(Show.artist_id == artist_id)
  #print(shows, file=sys.stderr)
  

  # Cycle through artist_shows and add to relevant list
  for s in artist_shows:
    venue = db.session.query(Venue.name, Venue.image_link).filter(Venue.id == s.venue_id).one()
    
    show_add = {
      "venue_id": s.venue_id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": s.start_time.strftime('%m/%d/%Y')
      }
      
    if (s.start_time < datetime.now()):
      past_shows.append(show_add)
    else:
      coming_shows.append(show_add)

  #import artist query
  artist = db.session.query(Artist).filter(Artist.id == artist_id).one()

  # Split the genres entry
  tmp_genres = artist.genres.split(',')

  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": tmp_genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": coming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(coming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = db.session.query(Artist).filter(Artist.id == artist_id).one()

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  artist = db.session.query(Artist).filter(Artist.id == aritst_id).one()
  
  updated_aritst = {
    name: form.name.data,
    genres: form.genres.data,
    address: form.address.data,
    city: form.city.data,
    state: form.state.data,
    phone: form.phone.data,
    website: form.website.data,
    facebook_link: form.facebook_link.data,
    seeking_venue: form.seeking_venue.data,
    seeking_description: form.seeking_description.data,
    image_link: form.image_link.data,
  }

  try:
    db.session.query(Artist).filter(Artist.id == artist_id).update(updated_artist)
    db.session.commit()
    flash('Artist ' + form.name.data + ' was successfully listed!')
  except:
    flash('An error occurred. Artist ' + form.name.data + 'could not be added')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = db.session.query(Venue).filter(Venue.id == venue_id).one()
  print(venue, file=sys.stderr)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  venue = db.session.query(Venue).filter(Venue.id == venue_id).one()

  updated_venue = {
    name: form.name.data,
    genres: form.genres.data,
    address: form.address.data,
    city: form.city.data,
    state: form.state.data,
    phone: form.phone.data,
    website: form.website.data,
    facebook_link: form.facebook_link.data,
    seeking_talent: form.seeking_talent.data,
    seeking_description: form.seeking_description.data,
    image_link: form.image_link.data
  }
  
  try:
    db.session.query(Venue).filter(Venue.id == venue_id).update(updated_venue)
    db.session.commit()
    flash('Venue' + form.name.data + ' was successfully updated!')
  except:
    flash('An error occurred. Venue ' + form.name.data + ' could not be updated.')
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
  form = ArtistForm()
  try:
    # pull data from the form and enter the variables in the data variable
    tmp_genres = request.form.getlist('genres')
    data = Artist(
    name = form.name.data, 
    city = form.city.data, 
    state = form.state.data, 
    phone = form.phone.data,
    #genres = form.genres.data,
    genres = ','.join(tmp_genres),
    seeking_description = form.seeking_description.data,
    facebook_link = form.facebook_link.data,
    image_link = form.image_link.data,
    website = form.website_link.data,
    seeking_venue = form.seeking_venue.data
    )
    # does the artist already exist?

    artist_exists = bool(Artist.query.filter_by(state = data.state, city = data.city, name = data.name).first())

    if artist_exists==True:
      #Artist is already in the db so flash warning
      flash(data.name + ' could not be listed as they are already in the system.')
    else:
      # Artist isn't in the db so can be added
      db.session.add(data)
      db.session.commit()
      # on successful db insert, flash success
      flash(request.form['name'] + ' was successfully listed!')
  except:
    flash('An error occurred. The artist could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')
    ################################################################################
    # Would expect the redirect to be to the current page for the user to try again.
    #################################################################################


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  shows = db.session.query(Show.artist_id, Show.venue_id, Show.start_time).all()
  print(shows, file=sys.stderr)

  data = []

  for s in shows:
    a = db.session.query(Artist.name, Artist.image_link).filter(Artist.id == s[0]).one()
    #print(artist, file=sys.stderr)
    v = db.session.query(Venue.name).filter(Venue.id == s[1]).one()
    #print(venue, file=sys.stderr)
    data.append({
      "artist_id": s[0],
      "artist_name": a[0],
      "artist_image_link": a[1],
      "venue_id": s[1],
      "venue_name": v[0],
      "start_time": str(s[2])
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm()
  try:
    # pull data from the form and enter the variables in the data variable
    data = Show(artist_id = form.artist_id.data, 
    venue_id = form.venue_id.data, 
    start_time = form.start_time.data)
    db.session.add(data)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    flash('An error occurred. The show could not be listed.')
    db.session.rollback()
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

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
