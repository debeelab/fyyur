from sqlalchemy import Column, String, Integer, Boolean, ARRAY, DateTime, create_engine, ForeignKey
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from sqlalchemy.sql.schema import PrimaryKeyConstraint


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

db = SQLAlchemy()

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(String()), nullable=False)
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=True, nullable=True)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', cascade='all, delete, delete-orphan', backref='venue', lazy=True)    # Can reference show.venue (as well as venue.shows)
    def __repr__(self):
      return f'<Venue {self.id} {self.name} {self.city} {self.state} {self.genres}>'

class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(String()), nullable=False)
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False, nullable=True)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', cascade='all, delete, delete-orphan', backref='artist', lazy=True)   
    def __repr__(self):
      return f'<Artist {self.id} {self.name} {self.city} {self.state} {self.genres}>'
   

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)    # Start time required field
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)   # Foreign key is the tablename.pk
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)

    # artist = db.relationship("Artist", foreign_keys=[artist_id])
    # venue = db.relationship("Venue", foreign_keys=[venue_id])
    def __repr__(self):
      return f'<Show {self.id} {self.start_time} artist_id={artist_id} venue_id={venue_id}>'

