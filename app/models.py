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
TOURNAMENT_DRAFT = 2
TOURNAMENT_HIDDEN = 3
TOURNAMENT_PRIVATE = 4

tournament_status = {
    TOURNAMENT_APPROVED: "Approved",
    TOURNAMENT_PENDING: "Pending",
    TOURNAMENT_DRAFT: "Draft",
    TOURNAMENT_HIDDEN: "Hidden",
    TOURNAMENT_PRIVATE: "Private"
}

TOURNAMENT_STANDARD = 0
TOURNAMENT_TEAM = 1
TOURNAMENT_TEAM_AVG = 2  # The average of the score of a single team is used

tournament_types = {
    TOURNAMENT_STANDARD: "Standard",
    TOURNAMENT_TEAM: "Team",
    TOURNAMENT_TEAM_AVG: "Team Average"
}

SCORE_DEFAULT = 0
SCORE_EXSCORE = 1

score_types = {
    SCORE_DEFAULT: "Default",
    SCORE_EXSCORE: "EX Score"
}

PROGRESS_NOT_STARTED = 0
PROGRESS_IN_PROGRESS = 1
PROGRESS_FINISHED = 2

progress_types = {
    PROGRESS_NOT_STARTED: "Not Started",
    PROGRESS_IN_PROGRESS: "In Progress",
    PROGRESS_FINISHED: "Finished"
}

POST_APPROVED = 0  # top score
POST_PENDING = 1
POST_UNRANKED = 2
POST_DRAFT = 3
POST_HIDDEN = 4
POST_PRIVATE = 5

post_status = {
    POST_APPROVED: "Approved",
    POST_PENDING: "Pending",
    POST_UNRANKED: "Unranked",
    POST_DRAFT: "Draft",
    POST_HIDDEN: "Hidden",
    POST_PRIVATE: "Private"
}

USER_CONFIRMED = 0
USER_UNCONFIRMED = 1
USER_HIDDEN = 2
USER_PRIVATE = 3
USER_BANNED = 4

user_status = {
    USER_CONFIRMED: "Confirmed",
    USER_UNCONFIRMED: "Unconfirmed",
    USER_HIDDEN: "Hidden",
    USER_PRIVATE: "Private",
    USER_BANNED: "Banned"
}

constants = {
    "TOURNAMENT_APPROVED": TOURNAMENT_APPROVED,
    "TOURNAMENT_PENDING": TOURNAMENT_PENDING,
    "TOURNAMENT_DRAFT": TOURNAMENT_DRAFT,
    "TOURNAMENT_HIDDEN": TOURNAMENT_HIDDEN,
    "TOURNAMENT_PRIVATE": TOURNAMENT_PRIVATE,

    "TOURNAMENT_STANDARD": TOURNAMENT_STANDARD,
    "TOURNAMENT_TEAM": TOURNAMENT_TEAM,
    "TOURNAMENT_TEAM_AVG": TOURNAMENT_TEAM_AVG,

    "SCORE_DEFAULT": SCORE_DEFAULT,
    "SCORE_EXSCORE": SCORE_EXSCORE,

    "PROGRESS_NOT_STARTED": PROGRESS_NOT_STARTED,
    "PROGRESS_IN_PROGRESS": PROGRESS_IN_PROGRESS,
    "PROGRESS_FINISHED": PROGRESS_FINISHED,

    "POST_APPROVED": POST_APPROVED,
    "POST_PENDING": POST_PENDING,
    "POST_UNRANKED": POST_UNRANKED,
    "POST_DRAFT": POST_DRAFT,
    "POST_HIDDEN": POST_HIDDEN,
    "POST_PRIVATE": POST_PRIVATE,

    "USER_CONFIRMED": USER_CONFIRMED,
    "USER_UNCONFIRMED": USER_UNCONFIRMED,
    "USER_HIDDEN": USER_HIDDEN,
    "USER_PRIVATE": USER_PRIVATE,
    "USER_BANNED": USER_BANNED,
}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    email_confirmed_at = db.Column(db.DateTime, nullable=True)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    active = db.Column(db.Boolean, nullable=True)
    status = db.Column(db.Integer, nullable=False, default=USER_CONFIRMED)
    banned_until = db.Column(db.DateTime, nullable=True)
    bio = db.Column(db.String(500), nullable=True, default="This user has no bio.")
    favsong = db.Column(db.String(50), nullable=True, default="No favorite song chosen.")
    posts = db.relationship('Post', backref='author', lazy=True)

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
    psupdate = db.Column(db.Boolean, nullable=False, default=True)

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

    def has_any_role(self, *role):
        return any(r in self.roles for r in role)

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
    perms = db.Column(db.Integer, nullable=False, default=0)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        elif isinstance(other, str):
            return self.name == other
        else:
            return False

    def __repr__(self):
        return f"Role('{self.name}')"

# Define the UserRoles association table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'))

    def __repr__(self):
        return f"UserRoles('{self.user_id}', '{self.role_id}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=POST_APPROVED)
    approved_time = db.Column(db.DateTime, nullable=True)
    song_id = db.Column(db.Integer, nullable=False)  # uses key in pump database now
    score = db.Column(db.Integer, nullable=False)
    exscore = db.Column(db.Integer, nullable=False)
    lettergrade = db.Column(db.String(3), nullable=False)
    chart_id = db.Column(db.Integer, nullable=False)  # uses key in pump database now
    platform = db.Column(db.String(8), nullable=False)
    stagepass = db.Column(db.Boolean, nullable=True)
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
    noteskin = db.Column(db.Integer, nullable=True)
    modifiers = db.Column(db.Integer, nullable=False, default=0)
    rushspeed = db.Column(db.Float, nullable=False, default=1.0)
    gamemix_id = db.Column(db.Integer, nullable=True)  # uses key in pump database now
    version_id = db.Column(db.Integer, nullable=True)  # uses key in pump database now
    gameflag = db.Column(db.Integer, nullable=True)
    ranked = db.Column(db.Boolean, nullable=False, default=False)  # string to boolean change, make sure it is accounted for
    length_id = db.Column(db.Integer, nullable=False)  # uses key in pump database now
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    accesscode = db.Column(db.String(32), nullable=True, default=None)
    acsubmit = db.Column(db.Boolean, nullable=False, default=False)  # string to boolean change, make sure it is accounted for
    sp = db.Column(db.Float, nullable=True, default=None)
    #tournamentid = db.Column(db.Integer, nullable=True)
    image_file = db.Column(db.String(20), nullable=False, default="None")

    def __repr__(self):
        return f"Post('{self.song}', '{self.score}', '{self.lettergrade}', '{self.type}', '{self.difficulty}', '{self.platform}', '{self.stagepass}', '{self.ranked}', '{self.length}')"

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=TOURNAMENT_APPROVED)
    progress = db.Column(db.Integer, nullable=False, default=PROGRESS_NOT_STARTED)
    tournament_type = db.Column(db.Integer, nullable=False, default=TOURNAMENT_STANDARD)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    _organizers = db.Column(db.String(10000), nullable=False, default="")
    signup_start_time = db.Column(db.DateTime, nullable=False)
    signup_end_time = db.Column(db.DateTime, nullable=False)
    skill_lvl = db.Column(db.String(12), nullable=False)
    titles_required = db.Column(db.String(1000), nullable=False, default="")
    description = db.Column(db.String(200), nullable=False)
    # bracketlink = db.Column(db.String(150), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="None")
    contact_info = db.Column(db.String(150), nullable=False, default="No contact info provided")
    score_type = db.Column(db.Integer, nullable=False, default=SCORE_DEFAULT)
    _participants = db.Column(db.String(10000), nullable=False, default="")
    _remaining_participants = db.Column(db.String(10000), nullable=False, default="")
    # if team tournament, _participants becomes a list of teams
    depth = db.Column(db.Integer, nullable=False, default=0)  # the current depth of the binary tree of matches (the round we are on)
    max_depth = db.Column(db.Integer, nullable=False, default=0)  # the max depth of the binary tree of matches (the number representing the first round)
    matches = db.relationship('Match', backref='tournament', lazy=True)

    @property
    def participants(self):  # list of user IDs or team IDs if it's a team tournament
        return [int(x) for x in self._participants.split(',')]
    @participants.setter
    def participants(self, val):
        if type(val) == int:
            self._participants += ',' + str(val)
        elif type(val) == list:
            self._participants = ','.join(val)
    @property
    def remaining_participants(self):  # list of user IDs or team IDs if it's a team tournament
        return [int(x) for x in self._remaining_participants.split(',')]
    @participants.setter
    def remaining_participants(self, val):
        if type(val) == int:
            self._remaining_participants += ',' + str(val)
        elif type(val) == list:
            self._remaining_participants = ','.join(val)
    @property
    def organizers(self):  # list of user IDs
        return [int(x) for x in self._organizers.split(',')]
    @organizers.setter
    def organizers(self, val):
        if type(val) == int:
            self._organizers += ',' + str(val)
        elif type(val) == list:
            self._organizers = ','.join(val)

    def __repr__(self):
        return f"Tournament('{self.name}', '{self.skill_lvl}, '{self.description}', '{self.bracketlink}', '{self.image_file}')"

class Match(db.Model): # tournament match
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id', ondelete='CASCADE'))
    progress = db.Column(db.Integer, nullable=False, default=PROGRESS_NOT_STARTED)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    depth = db.Column(db.Integer, nullable=False, default=0)  # the depth of this match in the binary tree of matches (0 is the final match)
    games = db.relationship('Game', backref='match', lazy=True)
    _participants = db.Column(db.String(10000), nullable=False, default="")
    _winners = db.Column(db.String(10000), nullable=False, default="")

    @property
    def participants(self):
        return [int(x) for x in self._participants.split(',')]
    @participants.setter
    def participants(self, val):
        if type(val) == int:
            self._participants += ',' + str(val)
        elif type(val) == list:
            self._participants = ','.join(val)
    @property
    def winners(self):
        return [int(x) for x in self._winners.split(',')]
    @participants.setter
    def winners(self, val):
        if type(val) == int:
            self._winners += ',' + str(val)
        elif type(val) == list:
            self._winners = ','.join(val)

class Game(db.Model): # tournament games (matches have games)
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id', ondelete='CASCADE'))
    match_id = db.Column(db.Integer, db.ForeignKey('match.id', ondelete='CASCADE'))
    progress = db.Column(db.Integer, nullable=False, default=PROGRESS_NOT_STARTED)
    # participants based on match
    chart_id = db.Column(db.Integer, nullable=False)
    # Winners are not necessary to store for games because they can be calculated at match end instead of game end
    # _winners = db.Column(db.String(10000), nullable=False, default="")

    # @property
    # def winners(self):
    #     return [int(x) for x in self._winners.split(',')]
    # @participants.setter
    # def winners(self, val):
    #     if type(val) == int:
    #         self._winners += ',' + str(val)
    #     elif type(val) == list:
    #         self._winners = ','.join(val)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    _members = db.Column(db.String(10000), nullable=False, default="")

    @property
    def members(self):  # list of user IDs
        return [int(x) for x in self._members.split(',')]
    @members.setter
    def members(self, val):
        if type(val) == int:
            self._members += ',' + str(val)
        elif type(val) == list:
            self._members = ','.join(val)
    
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