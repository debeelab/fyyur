#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from models import db, Artist, Venue, Show
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import re
from flask_migrate import Migrate
from operator import itemgetter # for sorting lists of tuples
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.app = app
db.init_app(app)
Migrate(app, db)
# db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
#migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')
#----------------------------------------------------------------------------#
# Navigation bar for venue, artist and show.
#----------------------------------------------------------------------------#
@app.route('/venues')
def venues():
    venues = Venue.query.all()
    datalist = []   # A list of dictionaries, where city, state, and venues are dictionary keys
    # Create a set of all the cities/states combinations uniquely
    cities_states = set()
    for venue in venues:
        cities_states.add( (venue.city, venue.state) )  # Add tuple
    
    # Turn the set into an ordered list
    cities_states = list(cities_states)
    cities_states.sort(key=itemgetter(1,0))     # Sorts on second column first (state), then by city.

    now = datetime.now()    # Don't get this over and over in a loop!
 # Now iterate over the unique values to seed the data dictionary with city/state locations
    for location in cities_states:
        # For this location, see if there are any venues there, and add if so
        venues_list = []
        for venue_name in venues:
            if (venue_name.city == location[0]) and (venue_name.state == location[1]):

                # If we've got a venue to add, check how many upcoming shows it has
                venue_shows = Show.query.filter_by(venue_id=venue_name.id).all()
                num_upcoming = 0
                for show in venue_shows:
                    if show.start_time > now:
                        num_upcoming += 1

                venues_list.append({
                    "id": venue_name.id,
                    "name": venue_name.name,
                    "num_upcoming_shows": num_upcoming
                })

        # After all venues are added to the list for a given location, add it to the data dictionary
        datalist.append({
            "city": location[0],
            "state": location[1],
            "venues": venues_list
        })
    return render_template('pages/venues.html', areas=datalist)

#----------------------------------------------------------------------------#
#Create Venue
#----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  if not form.validate_on_submit():
        flash( form.errors )
        return redirect(url_for('create_venue_submission'))
  else:
    # Insert form data into DB
    try:
      # creates the new venue with all fields but not genre yet
      new_venue = Venue(
        name = form.name.data, 
        city = form.city.data, 
        state = form.state.data, 
        address = form.address.data, 
        phone = form.phone.data,
        # phone = re.sub('\D', '', phone_f),
        facebook_link = form.facebook_link.data,
        genres = form.genres.data,
        image_link = form.image_link.data, 
        website = form.website_link.data,
        seeking_talent = form.seeking_talent.data, 
        seeking_description = form.seeking_description.data, 
       
      )
      db.session.add(new_venue)
      db.session.commit()
      flash('Venue: {0} created successfully'.format(new_venue.name))
    except Exception as err:
      flash('An error occurred creating the Venue: {0}. Error: {1}'.format(new_venue.name, err))
      # print(f'Exception "{err}" in create_venue_submission()')
      return redirect(url_for('create_venue_submission'))
      db.session.rollback()
    finally:
      # Close connection
      db.session.close()
    return render_template('pages/home.html')

#-----------------search for a venue with the venue name --------------
@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '').strip()
     # Use filter, not filter_by when doing LIKE search (i=insensitive to case)
    venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()   # Wildcards search before and after
    print(venues)
    venue_list = []
    now = datetime.now()
    for venue in venues:
        venue_shows = Show.query.filter_by(venue_id=venue.id).all()
        num_upcoming = 0
        for show in venue_shows:
            if show.start_time > now:
                num_upcoming += 1

        venue_list.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming  # FYI, template does nothing with this
        })

    response = {
        "count": len(venues),
        "data": venue_list
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>', methods=['GET', 'POST'])
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # Get all the data from the DB and populate the data dictionary (context)
  venue = Venue.query.get(venue_id)              # Returns object by primary key, or None
  print(venue)
  if not venue:
    # Didn't return one, user must've hand-typed a link into the browser that doesn't exist
    # Redirect home
    return redirect(url_for('index'))
  else:     
    # Get a list of shows, and count the ones in the past and future
    past_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
    upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
    past_shows = []
    upcoming_shows = []
    past_shows_count = 0
    upcoming_shows_count = 0
    
    for show in upcoming_shows_query:
      upcoming_shows_count += 1
      upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": format_datetime(str(show.start_time))
      })
    for show in past_shows_query:
        past_shows_count += 1
        past_shows.append({
          "artist_id": show.artist_id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": format_datetime(str(show.start_time))
        })

    data = {
      "id": venue_id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      # Put the dashes back into phone number
      "phone": (venue.phone[:3] + '-' + venue.phone[3:6] + '-' + venue.phone[6:]),
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "past_shows_count": past_shows_count,
      "upcoming_shows": upcoming_shows,
      "upcoming_shows_count": upcoming_shows_count,
      
      # "past_shows_count": len(past_shows),
      # "upcoming_shows_count": len (upcoming_shows)
      
    }

  return render_template('pages/show_venue.html', venue=data)

#--------------------------------------------------
#-----------Edit and Update Venue------------------  
#--------------------------------------------------          
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # TODO: populate form with values from venue with ID <venue_id>
  # Get the existing venue from the database
  venue = Venue.query.get(venue_id)               # Returns object based on primary key, or None.  Guessing get is faster than filter_by
  if not venue:
    # User typed in a URL that doesn't exist, redirect home
        return redirect(url_for('index'))
  else:
    # Otherwise, valid venue.  We can prepopulate the form with existing data like this:
    form = VenueForm(obj=venue)
    # Prepopulate the form with the current values.  This is only used by template rendering!
    venue = {
      "id": venue_id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      # Put the dashes back into phone number
      "phone": (venue.phone[:3] + '-' + venue.phone[3:6] + '-' + venue.phone[6:]),
      "genres": venue.genres,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link
    }
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
    form = VenueForm(request.form)
    
    # Redirect back to form if errors in form validation
    if not form.validate():
        flash( form.errors )
        return redirect(url_for('edit_venue_submission', venue_id=venue_id))

    else:
        error_in_update = False

        # Insert form data into DB
        try:
            # First get the existing venue object
            venue = Venue.query.get(venue_id)
            # Update fields
            venue.name = form.name.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.address = form.address.data
            venue.phone = form.phone.data
            venue.genres =  form.genres.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data
            venue.image_link = form.image_link.data
            venue.website = form.website_link.data
            venue.facebook_link = form.facebook_link.data
            
            db.session.commit()
        except Exception as e:
            error_in_update = True
            print(f'Exception "{e}" in edit_venue_submission()')
            db.session.rollback()
        finally:
            db.session.close()

        if not error_in_update:
            # on successful db update, flash success
            flash('Venue ' + request.form['name'] + ' was successfully updated!')
            return redirect(url_for('show_venue', venue_id=venue_id))
        else:
            flash('An error occurred. Venue ' + name + ' could not be updated.')
            print("Error in edit_venue_submission()")
            abort(500)
    
    return redirect(url_for('show_venue', venue_id=venue_id))

@app.route('/venues/<int:venue_id>/delete')
def delete_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
    error_in_update = False
    try:
      venue = Venue.query.filter_by(id=venue_id).one()
      db.session.delete(venue)
      db.session.commit()
    except Exception as e:
      error_in_update = True
      print(f'Exception "{e}" in delete_venue_submission()')
      db.session.rollback()
    finally:
      db.session.close()

    if not error_in_update:
      # on successful db update, flash success
      flash('Venue  was successfully deleted!')
      return redirect(url_for('index'))
    else:
      flash('An error occurred. Venue could not be deleted.')
      print("Error in delete_venue_submission()")
      abort(500)

#-----------------------------------------------------
#----------------------Artist Nav bar-----------------
#-----------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  data = []
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      })
  return render_template('pages/artists.html', artists=data)

#----------------------------------------------------------------------------#
#Create Artist
#----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  form = ArtistForm()

  # Redirect back to form if errors in form validation
  if not form.validate_on_submit():
        flash(form.errors )
        return redirect(url_for('create_artist_submission'))
  else:
    # Insert form data into DB
    try:
      # creates the new venue with all fields
      new_artist = Artist(
        name = form.name.data, 
        city = form.city.data, 
        state = form.state.data, 
        phone = form.phone.data,
        genres = form.genres.data,
        facebook_link = form.facebook_link.data,
        image_link = form.image_link.data, 
        website = form.website_link.data,
        seeking_venue = form.seeking_venue.data, 
        seeking_description = form.seeking_description.data, 
        )
      db.session.add(new_artist)
      db.session.commit()
      
      #on successful db insert, flash success
      flash('Venue: {0} created successfully'.format(new_artist.name))
    
    except Exception as err:
      db.session.rollback()
      #on unsuccessful db insert, flash unable to insert into the database 
      flash('An error occurred creating the Venue: {0}. Error: {1}'.format(new_artist.name, err))
      return redirect(url_for('create_artist_submission'))
      
    finally:
      # Close connection
      db.session.close()
    return render_template('pages/home.html')


@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  # Most of code is from search_venues()
    search_term = request.form.get('search_term', '').strip()

    # Use filter, not filter_by when doing LIKE search (i=insensitive to case)
    artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()   # Wildcards search before and after
    #print(artists)
    artist_list = []
    now = datetime.now()
    for artist in artists:
        artist_shows = Show.query.filter_by(artist_id=artist.id).all()
        num_upcoming = 0
        for show in artist_shows:
            if show.start_time > now:
                num_upcoming += 1

        artist_list.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming  # FYI, template does nothing with this
        })

    response = {
        "count": len(artists),
        "data": artist_list
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>', methods=['GET', 'POST'])
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  # Displays the artist page with the given artist_id.  Much of this copied from show_venue

  # Get all the data from the DB and populate the data dictionary (context)
    artist = Artist.query.get(artist_id)   # Returns object by primary key, or None
    print(artist)
    if not artist:
        # Didn't return one, user must've hand-typed a link into the browser that doesn't exist
        # Redirect home
        return redirect(url_for('index'))
    else:
      past_shows_query = db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()
      upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
      past_shows = []
      upcoming_shows = []
      past_shows_count = 0
      upcoming_shows_count =0
      for show in upcoming_shows_query:
        upcoming_shows_count += 1
        upcoming_shows.append({
          "venue_id": show.venue_id,
          "venue_name": show.venue.name,
          "venue_image_link": show.venue.image_link,
          "start_time": format_datetime(str(show.start_time))
        })
      for show in past_shows_query:
        past_shows_count += 1
        past_shows.append({
          "venue_id": show.venue_id,
          "venue_name": show.venue.name,
          "venue_image_link": show.venue.image_link,
          "start_time": format_datetime(str(show.start_time))
        })

      data = {
        "id": artist_id,
        "name": artist.name,
        "city": artist.city,
        "state": artist.state,
        # Put the dashes back into phone number
        "phone": (artist.phone[:3] + '-' + artist.phone[3:6] + '-' + artist.phone[6:]),
        "genres":artist.genres,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "past_shows_count": past_shows_count,
        "upcoming_shows": upcoming_shows,
        "upcoming_shows_count": upcoming_shows_count,
        # "upcoming_shows_count": len(upcoming_shows)
        # "past_shows_count": len(past_shows),
      }
    return render_template('pages/show_artist.html', artist=data)

#-----------------------------------------------------------------
#  Edit and Update artist page
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    # Taken mostly from edit_venue()
    # Get the existing artist from the database
    artist = Artist.query.get(artist_id)  # Returns object based on primary key, or None.  Guessing get is faster than filter_by
    if not artist:
        # User typed in a URL that doesn't exist, redirect home
        return redirect(url_for('index'))
    else:
      
      # Otherwise, valid artist.  We can prepopulate the form with existing data like this.
      # Prepopulate the form with the current values.  This is only used by template rendering!
        
      form = ArtistForm(obj=artist)
      artist = {
        "id": artist_id,
        "name": artist.name,
        "city": artist.city,
        "state": artist.state,
        # Put the dashes back into phone number
        "phone": (artist.phone[:3] + '-' + artist.phone[3:6] + '-' + artist.phone[6:]),
        "genres": artist.genres,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link
      }
  # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
    # Much of this code from edit_venue_submission()
    form = ArtistForm()
    # Redirect back to form if errors in form validation
    if not form.validate():
        flash( form.errors )
        return redirect(url_for('edit_artist_submission', artist_id=artist_id))

    else:
        error_in_update = False

        # Insert form data into DB
        try:
            # First get the existing artist object
            artist = Artist.query.get(artist_id)
            # artist = Artist.query.filter_by(id=artist_id).one_or_none()

            # Update fields
            artist.name = form.name.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.genres = form.genres.data
            artist.facebook_link = form.facebook_link.data
            artist.image_link = form.image_link.data
            artist.website = form.website_link.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data

            db.session.commit()
            #on successful db insert, flash success
            flash('Artist: {0} updated successfully'.format(artist.name))
    
        except Exception as err:
          db.session.rollback()
          #on unsuccessful db insert, flash unable to insert into the database 
          flash('An error occurred updating the Artist: {0}. Error: {1}'.format(artist.name, err))
          return redirect(url_for('edit_artist_submission'))
        finally:
          # Close connection
          db.session.close()
    return render_template('pages/home.html')

@app.route('/artists/<int:artist_id>/delete')
def delete_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
    error_in_update = False
    try:
      artist = Artist.query.filter_by(id=artist_id).one()
      db.session.delete(artist)
      db.session.commit()
    except Exception as e:
      error_in_update = True
      print(f'Exception "{e}" in delete_artist_submission()')
      db.session.rollback()
    finally:
      db.session.close()

    if not error_in_update:
      # on successful db update, flash success
      flash('Artist  was successfully deleted!')
      return redirect(url_for('index'))
    else:
      flash('An error occurred. Artist could not be deleted.')
      print("Error in delete_artist_submission()")
      abort(500)

#--------------------END OF ARTIST----------------------


#---------------------------------------------------      
#---------------Show Nav bar------------------------
@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  # displays list of shows at /shows
  # shows = Show.query.all()
  shows = Show.query.order_by(db.desc(Show.start_time))
  data = []
  for show in shows:
    # Can reference show.artist, show.venue
    data.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))
    })
  return render_template('pages/shows.html', shows=data)


#----------------------------------------------------------------------------#
#Create Shows
#----------------------------------------------------------------

@app.route('/shows/create', methods=['GET'])
def create_show_form():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  form = ShowForm(request.form)
  # start_time = form.start_time.data
  # artist_id = form.artist_id.data.strip()
  # venue_id = form.venue_id.data.strip()

  if not form.validate_on_submit():
        flash( form.errors )
        return redirect(url_for('create_show_submission'))
  else:
    error = False
    # Insert form data into DB
    try:
      # creates the new venue with all fields
      new_show = Show(
        start_time = form.start_time.data, 
        artist_id = form.artist_id.data, 
        venue_id= form.venue_id.data, 
      )
      db.session.add(new_show)
      db.session.commit()
      
      #on successful db insert, flash success
      flash('Show: {0} created successfully'.format(new_show.artist_id))
    except Exception as e:
      db.session.rollback()
      flash('An error occurred creating the Show: {0}. Error: {1}'.format(new_show.artist_id, err))
      return redirect(url_for('create_show_submission'))      
    finally:
      db.session.close()
    return render_template('pages/home.html')
#-----------------END OF SHOW-----------------------

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
