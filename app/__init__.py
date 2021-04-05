from flask import Flask, current_app, logging, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_moment import Moment
from loadsongs import load_song_lists, raw_songdata
from flask_mail import Mail
from app.config import Config
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
# from flask_user import UserManager
from flaskext.markdown import Markdown
import atexit
from functools import wraps
import signal

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

genre_pairs = (
    ('ORIGINAL', 'Original'),
    ('K-POP', 'K-Pop'),
    ('WORLD MUSIC', 'World Music'),
    ('J-MUSIC', 'J-Music'),
    ('XROSS', 'Xross (Crossover)')
)

difficulties = []
coop = ["2P", "3P", "4P", "5P"]
for i in range(1, 29):
    difficulties.append(str(i))
for i in coop:
    difficulties.append(i)
difficulties = list(zip(difficulties, difficulties))

apikey_required = False  # also ip address requirement

if apikey_required:
    with open('approved_ips.txt', 'r') as f:
        approved_ips = [x.replace('\n','').strip() for x in f.readlines()]
else:
    approved_ips = []

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'success'

# Inspired by Flask-User's decoration
def roles_required(*role_names):
    def wrapper(view_function):

        @wraps(view_function)    # Tells debuggers that is is a function wrapper
        def decorator(*args, **kwargs):
            login_manager = current_app.login_manager

            # Must be logged in
            if not current_user.is_authenticated:
                # Redirect to unauthenticated page (401)
                return login_manager.unauthorized()

            # User must have the required roles
            if not current_user.has_role(*role_names):
                # Redirect to the unauthorized page (403)
                return abort(403)

            # It's OK to call the view
            return view_function(*args, **kwargs)

        return decorator

    return wrapper

mail = Mail()
scheduler = APScheduler(scheduler=BackgroundScheduler())
moment = Moment()

def safe_shutdown(signum, frame):  # To make APScheduler actually shut off
    print('Forcing shutdown...')
    scheduler.shutdown(wait=False)

signal.signal(signal.SIGINT, safe_shutdown)
signal.signal(signal.SIGTERM, safe_shutdown)

class AdminModelView(ModelView):
    form_excluded_columns = ('password')
    def is_accessible(self):
        return current_user.is_authenticated and (current_user.has_role('Admin') or current_user.username == 'admin')
class AdminView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and (current_user.has_role('Admin') or current_user.username == 'admin')

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    # mail.init_app(app)
    
    # from app.models import User
    migrate = Migrate(app, db)
    md = Markdown(app)

    moment.init_app(app)

    # user_manager = UserManager(app, db, User)
    
    from app.models import User, Post, Tournament, Match, Game, Message, APIKey, Role
    admin = Admin(app, index_view=AdminIndexView(), name='ArrowTracker', template_mode='bootstrap3')
    admin.add_view(AdminModelView(User, db.session))
    admin.add_view(AdminModelView(Post, db.session))
    admin.add_view(AdminModelView(Tournament, db.session))
    admin.add_view(AdminModelView(Match, db.session))
    admin.add_view(AdminModelView(Game, db.session))
    admin.add_view(AdminModelView(Message, db.session))
    admin.add_view(AdminModelView(APIKey, db.session))
    admin.add_view(AdminModelView(Role, db.session))

    from app.users.routes import users
    from app.scores.routes import scores
    from app.main.routes import main
    from app.tournaments.routes import tournaments
    from app.moderation.routes import moderation
    from app.errors.handlers import errors

    app.register_blueprint(users)
    app.register_blueprint(scores)
    app.register_blueprint(main)
    app.register_blueprint(tournaments)
    app.register_blueprint(moderation)
    app.register_blueprint(errors)

    scheduler.scheduler.add_jobstore(SQLAlchemyJobStore(url=app.config['SQLALCHEMY_JOBS_DATABASE_URI']), 'default')
    
    scheduler.init_app(app)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    @app.before_first_request
    def load_tasks():
        from app.scores.utils import update_scores_task

    return app