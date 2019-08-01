from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from datetime import datetime
from app import models

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///app/site.db"
db = SQLAlchemy(app)

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    bio = db.Column(db.String(500), nullable=True, default="This user has no bio.")
    favsong = db.Column(db.String(50), nullable=True, default="No favourite song chosen.")
    posts = db.relationship('Post', backref='author', lazy=True)
    weeklyposts = db.relationship('WeeklyPost', backref='author', lazy=True)
    accesscode = db.Column(db.String(32), unique=True, nullable=True)
    ign = db.Column(db.String(20), unique=True, nullable=False, default='PUMPITUP')
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
    speedmod = db.Column(db.Integer, nullable=False, default=0)
    rushspeed = db.Column(db.Integer, nullable=False, default=0)

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

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}'. '{self.bio}', '{self.favsong}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    song = db.Column(db.String(50), nullable=False)
    song_id = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    exscore = db.Column(db.Integer, nullable=False)
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
    noteskin = db.Column(db.String(20), nullable=False, default="Default")
    modifiers = db.Column(db.Integer, nullable=False, default=0)
    gamemix = db.Column(db.String(20), nullable=False, default="Unknown")
    gameversion = db.Column(db.String(12), nullable=False, default="Unknown")
    gameflag = db.Column(db.Integer, nullable=False, default=0)
    ranked = db.Column(db.String(5), nullable=False)
    length = db.Column(db.String(8), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    accesscode = db.Column(db.String(32), nullable=True)
    acsubmit = db.Column(db.String(5), nullable=False)
    #tournamentid = db.Column(db.Integer, nullable=True)
    image_file = db.Column(db.String(20), nullable=False, default="None")

    def __repr__(self):
        return f"Post('{self.song}', '{self.score}', '{self.lettergrade}', '{self.type}', '{self.difficulty}', '{self.platform}', '{self.stagepass}', '{self.ranked}', '{self.length}')"

class WeeklyPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
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
        return f"Post('{self.song}', '{self.score}', '{self.lettergrade}', '{self.type}', '{self.difficulty}', '{self.platform}', '{self.stagepass}', '{self.ranked}', '{self.length}')"

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    skill_lvl = db.Column(db.String(12), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    bracketlink = db.Column(db.String(150), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="None")
    contactinfo = db.Column(db.String(150), nullable=False, default="No contact info provided")

    def __repr__(self):
        return f"Tournament('{self.name}', '{self.skill_lvl}, '{self.description}', '{self.bracketlink}', '{self.image_file}')"

class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(2), nullable=True)