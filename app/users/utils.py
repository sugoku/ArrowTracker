import os
import secrets
import math
from PIL import Image
from flask import url_for, current_app
from flask_mail import Message
from app import mail, db
from app.models import User, Post
import json
from app.config import Config
from app.scores.utils import *
from sqlalchemy import desc, or_

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    if f_ext != '.gif':
        f_ext = '.jpg'
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    if i.size[0] > 1200 or i.size[1] > 1200:
        pass
    i.thumbnail(output_size)
    if f_ext != '.gif':
        i.save(picture_path, format='jpeg')
    else:
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

def id_to_user(uid):
    u = User.query.filter_by(id=uid).first()
    return u if u != None else None

def accesscode_to_user(acode):
    u = User.query.filter_by(accesscode=acode).first()
    return u if u != None else None

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
        'NoteSkinSpeed': int(user.noteskin * 0x10000 + user.scrollspeed * 4.0) if user.noteskin != None and user.scrollspeed != None else 0,
        'RushSpeed': float(user.rushspeed),
        'Scores': posts_to_uscore(user.posts)
    }

def update_user_with_primeprofile(user, post):
    user.ign = post['Nickname'] # consider not changing this
    user.countryid = post['CountryID'] # or this
    #user.gameavatar = post['Avatar'] # or this
    user.gamelevel = int(post['Level'])
    user.gameexp = int(post['EXP'])
    user.gamepp = int(post['PP'])
    user.ranksingle = int(post['RankSingle'])
    user.rankdouble = int(post['RankDouble'])
    user.runningstep = int(post['RunningStep'])
    user.playcount = int(post['PlayCount'])
    user.kcal = float(post['Kcal'])
    if user.psupdate == "True":
        user.modifiers = int(post['Modifiers']) # might want to make this an option
        user.noteskin = int(post['NoteSkinSpeed']) / 0x10000 # might want to make this an option
        user.scrollspeed = (int(post['NoteSkinSpeed']) % 0x100) / 4.0 # might want to make this an option
        #user.rushspeed = float(post['RushSpeed'])

def update_user_sp(u):
    sp = 0
    scores = Post.query.filter_by(author=u, platform='pad').filter(or_(Post.image_file != "None", Post.acsubmit == "True")).order_by(Post.sp.desc()).limit(150).all()
    place = 0
    for score in scores:
        sp += math.pow(0.95, place) * score.sp
        place += 1
    u.sp = sp
    db.session.commit()

def get_user_rank(u):
    users = User.query.order_by(User.sp.desc()).all()
    try:
        return users.index(u)+1
    except ValueError:
        return None

def add_exp(u, exp):
    u.gameexp += exp
    u.gamelevel = max((int((5.5816187294199637E-01*(u.gameexp**5.0936826990568707E-01))-5.4169035580629679), 0))+1
    db.session.commit()

def add_pp(u, pp):
    u.gamepp += pp
    db.session.commit()