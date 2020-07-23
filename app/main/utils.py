from PIL import Image
import os
import secrets
import uuid
from flask import current_app
from app.models import APIKey, User

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
    '''Determine if a file is a valid type.'''
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_picture(form_picture):
    '''Given a score picture, resize and save the image.'''
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/tournament_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

def valid_api_key(apikey):
    '''Determine if an APIKey string is associated with a user.'''
    u = APIKey.query.filter_by(key=apikey).first()
    return u != None

def get_api_key(apikey):
    '''Given an APIKey string, return the APIKey object in the database.'''
    return APIKey.query.filter_by(key=apikey).first()

def generate_unique_key():
    '''Generate a unique 32-character API key.'''
    key = secrets.token_urlsafe(32)
    while valid_api_key(key):
        key = secrets.token_urlsafe(32)
    return key

def valid_accesscode(accesscode):
    '''Determine if a PrimeServer access code is associated with a user.'''
    u = User.query.filter_by(accesscode=accesscode).first()
    return u != None

def generate_unique_accesscode():
    '''Generate a unique 32-character access code.'''
    key = uuid.uuid4()
    while len(key.hex) == 32:
        key = uuid.uuid4()
    return key.hex
