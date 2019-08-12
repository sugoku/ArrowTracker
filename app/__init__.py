from flask import Flask, current_app, logging
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from loadsongs import load_song_lists, raw_songdata
from flask_mail import Mail
from app.config import Config
from flask_apscheduler import APScheduler
import atexit

songlist_pairs, lengthtype_pairs = load_song_lists()

gamemix_pairs = (
    ('1st', 'The 1st Dance Floor'),
    ('2nd', '2nd Ultimate Remix'),
    ('3rd', '3rd O.B.G'),
    ('obg', 'The O.B.G / Season Evolution'),
    ('collection', 'The Collection'),
    ('perfect', 'The Perfect Collection'),
    ('extra', 'Extra'),
    ('premiere', 'The Premiere'),
    ('prex', 'The Prex'),
    ('rebirth', 'The Rebirth'),
    ('premiere2', 'The Premiere 2'),
    ('prex2', 'The Prex 2'),
    ('premiere3', 'The Premiere 3'),
    ('prex3', 'The Prex 3'),
    ('exceed', 'Exceed'),
    ('exceed2', 'Exceed 2'),
    ('zero', 'Zero'),
    ('nx', 'NX / New Xenesis'),
    ('nx2', 'NX2 / Next Xenesis'),
    ('nxa', 'NX Absolute'),
    ('fiesta', 'Fiesta'),
    ('fiestaex', 'Fiesta EX'),
    ('fiesta2', 'Fiesta 2'),
    ('infinity', 'Infinity'),
    ('prime', 'Prime'),
    ('primeje', 'Prime JE'),
    ('prime2', 'Prime 2'),
    ('xx', 'XX'),
    ('jump', 'Jump'),
    ('pro', 'Pro'),
    ('pro2', 'Pro 2'),
    ('prox', 'Pro-X'),
    ('stepmania', 'StepMania'),
    ('stepf2', 'StepF2'),
    ('other', 'Other')
)

judgement_pairs = (
    ('nj', 'Normal Judgement'),
    ('hj', 'Hard Judgement'),
    ('vj', 'Very Hard Judgement')
)

difficulties = []
coop = ["2P", "3P", "4P", "5P"]
for i in range(1, 29):
    difficulties.append(str(i))
for i in coop:
    difficulties.append(i)
difficulties = list(zip(difficulties, difficulties))

apikey_required = False # also ip address requirement

with open('approved_ips.txt', 'r') as f:
    approved_ips = [x.replace('\n','').strip() for x in f.readlines()]

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'success'

mail = Mail()

scheduler = APScheduler()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from app.users.routes import users
    from app.scores.routes import scores
    from app.main.routes import main
    from app.errors.handlers import errors

    app.register_blueprint(users)
    app.register_blueprint(scores)
    app.register_blueprint(main)
    app.register_blueprint(errors)

    scheduler.init_app(app)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    @app.before_first_request
    def load_tasks():
        from app.scores.utils import update_scores_task

    return app