from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from app import db, login_manager, roles_required
import app
import json
from flask_login import current_user, login_required, UserMixin
from time import time

TOURNAMENT_APPROVED = 0
TOURNAMENT_PENDING = 1
TOURNAMENT_HIDDEN = 2

POST_APPROVED = 0
POST_PENDING = 1
POST_HIDDEN = 2

USER_CONFIRMED = 0
USER_UNCONFIRMED = 1
USER_HIDDEN = 2
USER_BANNED = 3

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    email_confirmed_at = db.Column(db.DateTime(), nullable=True)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    active = db.Column(db.Boolean(), nullable=True)
    status = db.Column(db.Integer, nullable=False, default=USER_CONFIRMED)
    banned_until = db.Column(db.DateTime(), nullable=True)
    bio = db.Column(db.String(500), nullable=True, default="This user has no bio.")
    favsong = db.Column(db.String(50), nullable=True, default="No favorite song chosen.")
    posts = db.relationship('Post', backref='author', lazy=True)
    weeklyposts = db.relationship('WeeklyPost', backref='author', lazy=True)

    accesscode = db.Column(db.String(32), unique=True, nullable=False)
    ign = db.Column(db.String(20), nullable=False, default='PUMPITUP')
    countryid = db.Column(db.Integer, nullable=False, default=196)
    gameavatar = db.Column(db.Integer, nullable=False, default=41)
    gamelevel = db.Column(db.Integer, nullable=False, default=0)
    gameexp = db.Column(db.Integer, nullable=False, default=0)
    gamepp = db.Column(db.Integer, nullable=False, default=0)
    ranksingle = db.Column(db.Integer, nullable=False, default=0)
    rankdouble = db.Column(db.Integer, nullable=False, default=0)
    runningstep = db.Column(db.Integer, nullable=False, default=0)
    playcount = db.Column(db.Integer, nullable=False, default=0)
    kcal = db.Column(db.Integer, nullable=False, default=0)
    modifiers = db.Column(db.Integer, nullable=False, default=0)
    noteskin = db.Column(db.Integer, nullable=False, default=0)
    scrollspeed = db.Column(db.Float, nullable=False, default=0)
    autovelocity = db.Column(db.Integer, nullable=True)
    rushspeed = db.Column(db.Integer, nullable=False, default=0)
    psupdate = db.Column(db.String(5), nullable=False, default='True')

    sp = db.Column(db.Float, nullable=False, default=0)
    title = db.Column(db.String(50), nullable=False, default='Newcomer')
    weeklywins = db.Column(db.Integer, nullable=False, default=0)
    roles = db.relationship('Role', secondary='user_roles', backref='user', lazy='dynamic')
    messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)
    notifications = db.relationship('Notification', backref='user',
                                    lazy='dynamic')


    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config["SECRET_KEY"], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def has_role(self, *role):
        return all(r in self.roles for r in role)

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __repr__(self):
        return f"Role('{self.name}')"

# Define the UserRoles association table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

    def __repr__(self):
        return f"UserRoles('{self.user_id}', '{self.role_id}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=POST_APPROVED)
    approved_time = db.Column(db.DateTime(), nullable=True)
    song = db.Column(db.String(50), nullable=False)
    song_id = db.Column(db.Integer, nullable=True)
    score = db.Column(db.Integer, nullable=False)
    exscore = db.Column(db.Integer, nullable=False)
    lettergrade = db.Column(db.String(3), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    difficulty = db.Column(db.String(5), nullable=False)
    difficultynum = db.Column(db.Integer, nullable=False)
    platform = db.Column(db.String(8), nullable=False)
    stagepass = db.Column(db.String(5), nullable=True)
    perfect = db.Column(db.Integer, nullable=False)
    great = db.Column(db.Integer, nullable=False)
    good = db.Column(db.Integer, nullable=False)
    bad = db.Column(db.Integer, nullable=False)
    miss = db.Column(db.Integer, nullable=False)
    maxcombo = db.Column(db.Integer, nullable=False)
    pp = db.Column(db.Float, nullable=False, default=0.0)
    runningstep = db.Column(db.Float, nullable=False, default=0.0)
    kcal = db.Column(db.Float, nullable=False, default=0.0)
    scrollspeed = db.Column(db.Float, nullable=True, default=None)
    autovelocity = db.Column(db.Integer, nullable=True, default=None)
    noteskin = db.Column(db.Integer, nullable=False, default=-1)
    modifiers = db.Column(db.Integer, nullable=False, default=0)
    rushspeed = db.Column(db.Float, nullable=False, default=1.0)
    gamemix = db.Column(db.String(30), nullable=False, default="Unknown")
    gameversion = db.Column(db.String(12), nullable=False, default="Unknown")
    gameflag = db.Column(db.Integer, nullable=False, default=0)
    ranked = db.Column(db.String(5), nullable=False)
    length = db.Column(db.String(8), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    accesscode = db.Column(db.String(32), nullable=True, default=None)
    acsubmit = db.Column(db.String(5), nullable=False)
    sp = db.Column(db.Float, nullable=True, default=None)
    #tournamentid = db.Column(db.Integer, nullable=True)
    image_file = db.Column(db.String(20), nullable=False, default="None")

    def __repr__(self):
        return f"Post('{self.song}', '{self.score}', '{self.lettergrade}', '{self.type}', '{self.difficulty}', '{self.platform}', '{self.stagepass}', '{self.ranked}', '{self.length}')"

class WeeklyPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    approved = db.Column(db.Integer, nullable=False, default=1)
    song = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)   
    lettergrade = db.Column(db.String(3), nullable=False)
    type = db.Column(db.String(7), nullable=True, default="None")
    difficulty = db.Column(db.Integer, nullable=False)
    platform = db.Column(db.String(8), nullable=False)
    stagepass = db.Column(db.String(5), nullable=False)
    perfect = db.Column(db.Integer, nullable=False)
    great = db.Column(db.Integer, nullable=False)
    good = db.Column(db.Integer, nullable=False)
    bad = db.Column(db.Integer, nullable=False)
    miss = db.Column(db.Integer, nullable=False)
    maxcombo = db.Column(db.Integer, nullable=False)
    pp = db.Column(db.Float, nullable=False, default=0)
    runningstep = db.Column(db.Float, nullable=False, default=0)
    kcal = db.Column(db.Float, nullable=False, default=0)
    scrollspeed = db.Column(db.Float, nullable=False)
    noteskin = db.Column(db.Integer, nullable=False, default=0)
    modifiers = db.Column(db.Integer, nullable=False, default=0)
    gamemix = db.Column(db.String(20), nullable=False, default="Unknown")
    gameversion = db.Column(db.String(12), nullable=False, default="Unknown")
    ranked = db.Column(db.String(5), nullable=False)
    length = db.Column(db.String(8), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="None")

    def __repr__(self):
        return f"WeeklyPost('{self.song}', '{self.score}', '{self.lettergrade}', '{self.type}', '{self.difficulty}', '{self.platform}', '{self.stagepass}', '{self.ranked}', '{self.length}')"


class TournamentPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    approved = db.Column(db.Integer, nullable=False, default=1)
    song = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)   
    lettergrade = db.Column(db.String(3), nullable=False)
    type = db.Column(db.String(7), nullable=True, default="None")
    difficulty = db.Column(db.Integer, nullable=False)
    platform = db.Column(db.String(8), nullable=False)
    stagepass = db.Column(db.String(5), nullable=False)
    perfect = db.Column(db.Integer, nullable=False)
    great = db.Column(db.Integer, nullable=False)
    good = db.Column(db.Integer, nullable=False)
    bad = db.Column(db.Integer, nullable=False)
    miss = db.Column(db.Integer, nullable=False)
    maxcombo = db.Column(db.Integer, nullable=False)
    pp = db.Column(db.Float, nullable=False, default=0)
    runningstep = db.Column(db.Float, nullable=False, default=0)
    kcal = db.Column(db.Float, nullable=False, default=0)
    scrollspeed = db.Column(db.Float, nullable=False)
    noteskin = db.Column(db.Integer, nullable=False, default=0)
    modifiers = db.Column(db.Integer, nullable=False, default=0)
    gamemix = db.Column(db.String(20), nullable=False, default="Unknown")
    gameversion = db.Column(db.String(12), nullable=False, default="Unknown")
    ranked = db.Column(db.String(5), nullable=False)
    length = db.Column(db.String(8), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="None")
    tournamentid = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"WeeklyPost('{self.song}', '{self.score}', '{self.lettergrade}', '{self.type}', '{self.difficulty}', '{self.platform}', '{self.stagepass}', '{self.ranked}', '{self.length}')"

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=TOURNAMENT_APPROVED)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    signup_time_start = db.Column(db.DateTime, nullable=False)
    signup_time_end = db.Column(db.DateTime, nullable=False)
    skill_lvl = db.Column(db.String(12), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    # bracketlink = db.Column(db.String(150), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="None")
    contactinfo = db.Column(db.String(150), nullable=False, default="No contact info provided")
    scoretype = db.Column(db.String(10), nullable=False, default="Default")
    _participants = db.Column(db.String(10000), nullable=False, default="")
    # _teams = db.Column(db.String(10000), nullable=False, default="") # i have no clue
    rounds = db.relationship('Round', backref='tournament', lazy=True)

    @property
    def participants(self):
        return [int(x) for x in self._participants.split(',')]
    @participants.setter
    def participants(self, val):
        if type(val) == int:
            self._participants += ',' + str(val)

    def __repr__(self):
        return f"Tournament('{self.name}', '{self.skill_lvl}, '{self.description}', '{self.bracketlink}', '{self.image_file}')"

class Round(db.Model): # tournament round
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer(), db.ForeignKey('tournament.id', ondelete='CASCADE'))
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    _participants = db.Column(db.String(10000), nullable=False, default="")

    @property
    def participants(self):
        return [int(x) for x in self._participants.split(',')]
    @participants.setter
    def participants(self, val):
        if type(val) == int:
            self._participants += ',' + str(val)
    
class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(2), nullable=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject = db.Column(db.String(100))
    body = db.Column(db.String(10000))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))