from PIL import Image
import os
import secrets
import uuid
import datetime
from flask import current_app
from app.models import APIKey, User

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
    '''Determine if a file is a valid type.'''
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

pic_directories = {
    'score': 'static/score_screenshots',
    'tournament': 'static/tournament_pics',
    'profile': 'static/profile_pics'
}

pic_output_size = {
    'score': (1200, 1200),
    'tournament': (256, 256),
    'profile': (256, 256)
}

def save_picture(form_picture, pic_type='score'):
    '''Given a picture, resize and save the image. The default type is a score picture.'''
    _, f_ext = os.path.splitext(form_picture.filename)
    f_ext = '.jpg' if f_ext != '.gif' or pic_type != 'profile' else '.gif'

    # generate random filenames until it is not an existing file
    picture_path = os.path.join(current_app.root_path, pic_directories[pic_type], f"{secrets.token_hex(8)}{f_ext}")
    while os.path.exists(picture_path):
        picture_path = os.path.join(current_app.root_path, pic_directories[pic_type], f"{secrets.token_hex(8)}{f_ext}")

    i = Image.open(form_picture)
    w, h = pic_output_size[pic_type]
    if i.width >= w and i.height >= h:
        i.thumbnail((w, h))
    if f_ext == '.gif' and pic_type == 'profile':
        i.save(picture_path, format="gif")
    else:
        i.save(picture_path, format="jpeg")
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
