import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from sqlalchemy.sql.schema import PrimaryKeyConstraint
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# TODO IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI = 'postgresql://sa:Temiloluwa83*@localhost:5432/fyyurapp'
SQLALCHEMY_TRACK_MODIFICATIONS = False
