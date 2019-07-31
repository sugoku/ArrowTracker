import os
import secrets
from PIL import Image
from flask import url_for, current_app
from flask_mail import Message
from app import mail
from app.models import User
import json
from app.config import Config

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Arrow Tracker: Password Reset Request', sender=Config.MAIL_USERNAME, recipients=[user.email])
    msg.body = f'''To reset your password, please visit:
{url_for('users.reset_token', token=token, _external=True)}

If you didn't request this reset, please ignore this email - the unique token used for the reset will expire in 30 minutes.
No changes will be made without using the above link.
'''
    mail.send(msg)

def accesscode_to_user(acode):
    u = User.query.filter_by(accesscode=acode).first()
    return u.id if u != None else None

def user_to_primeprofile(user):
    return {
        'PlayerID': user.id,     # figure out which is which (player and profile ID)
        'AccessCode': user.accesscode,
        'Nickname': user.ign,
        'ProfileID': user.id,
        'CountryID': user.countryid,
        'Avatar': user.gameavatar,
        'Level': user.gamelevel,
        'EXP': user.gameexp,
        'PP': user.gamepp,
        'RankSingle': user.ranksingle,
        'RankDouble': user.rankdouble,
        'RunningStep': user.runningstep,
        'PlayCount': user.playcount,
        'Kcal': user.kcal,
        'Modifiers': user.modifiers,
        'SpeedMod': user.noteskin + user.speedmod,
        'RushSpeed': user.rushspeed,
        'Scores': posts_to_uscore(u.posts)
    }

def update_user_with_primeprofile(user, post):
    user.ign = post['Nickname'] # consider not changing this
    user.countryid = post['CountryID'] # or this
    user.gameavatar = post['Avatar'] # or this
    user.gamelevel = int(post['Level'])
    user.gameexp = int(post['EXP'])
    user.gamepp = int(post['PP'])
    user.ranksingle = int(post['RankSingle'])
    user.rankdouble = int(post['RankDouble'])
    user.runningstep = int(post['RunningStep'])
    user.playcount = int(post['PlayCount'])
    user.kcal = float(post['Kcal'])
    user.modifiers = int(post['Modifiers'])
    user.noteskin = int(post['SpeedMod']) % 100
    user.speedmod = int(post['SpeedMod']) - (int(post['SpeedMod']) % 100)
    user.rushspeed = float(post['RushSpeed'])