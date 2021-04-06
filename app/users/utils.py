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

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

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
    '''Given an user ID, return the user it is associated with.'''
    u = User.query.filter_by(id=uid).first()
    return u if u != None else None

def accesscode_to_user(acode):
    '''Given an PrimeServer access code, return the user it is associated with.'''
    u = User.query.filter_by(accesscode=acode).first()
    return u if u != None else None

def user_to_primeprofile(user):
    '''Given a user, returns a compatible PrimeServer profile packet.'''
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
    '''Given a user and a PrimeServer profile packet, update the user's info with the packet.'''
    #user.ign = post['Nickname'] # consider not changing this
    #user.countryid = post['CountryID'] # or this
    #user.gameavatar = post['Avatar'] # or this
    #user.gamelevel = int(post['Level'])
    #user.gameexp = int(post['EXP'])
    #user.gamepp = int(post['PP'])
    user.ranksingle = int(post['RankSingle'])
    user.rankdouble = int(post['RankDouble'])
    user.runningstep = int(post['RunningStep'])
    user.playcount = int(post['PlayCount'])
    user.kcal = float(post['Kcal'])
    if user.psupdate:
        user.modifiers = int(post['Modifiers']) # might want to make this an option
        user.noteskin = int(post['NoteSkinSpeed']) / 0x10000 # might want to make this an option
        user.scrollspeed = round(0.5 * round((int(post['NoteSkinSpeed']) % 0x100) / 4.0 / 0.5), 1) # might want to make this an option
        #user.rushspeed = float(post['RushSpeed'])
    db.session.commit()

def update_user_sp(u):
    '''Evaluates a user's eligible scores and updates their SP (skill points) in the database.'''
    sp = 0
    scores = Post.query.filter_by(author=u, platform='pad', status=POST_APPROVED).order_by(Post.sp.desc()).limit(150).all()
    place = 0
    for score in scores:
        sp += math.pow(0.95, place) * score.sp
        place += 1
    u.sp = sp
    db.session.commit()

def update_user_titles(u):
    '''Evaluates a user's eligible scores and updates their titles in the database.'''
    u_titles = [title for title in titles if titles[title](u)]
    role_names = set(u.roles).union(*u_titles)  # make sure there are no duplicate roles
    roles = [Role.query.filter(name=name).first() for name in role_names]

    for role in roles:
        if role is None:
            current_app.logger.info(f"WARNING: Tried to give user {u} a role that doesn't exist.")
    
    u.roles = [role for role in roles if role is not None]
    db.session.commit()

def get_user_rank(u):
    '''Gets a user's rank on the main SP leaderboard.'''
    users = User.query.order_by(User.sp.desc()).all()
    try:
        return users.index(u)+1
    except ValueError:
        return None

def add_exp(u, exp):
    '''Given a user and the amount of experience points, adds the XP to the user's account and recalculates their level.'''
    u.gameexp += exp
    u.gamelevel = max((int((5.5816187294199637E-01*(u.gameexp**5.0936826990568707E-01))-5.4169035580629679), 0))+1
    db.session.commit()

def add_pp(u, pp):
    '''Given a user and the amount of PP, adds the PP to the user's account.'''
    u.gamepp += pp
    db.session.commit()