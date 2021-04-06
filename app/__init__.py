from flask import Flask, current_app, logging, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_moment import Moment
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

score_learner = None

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

    @app.context_processor
    def inject_model_constants():
        return dict(constants=app.models.constants)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    # mail.init_app(app)
    
    # from app.models import User
    migrate = Migrate(app, db)
    md = Markdown(app)

    moment.init_app(app)

    songlist_pairs = [(song.id, song.name) for song in Song.query.all()]
    chart_pairs = [(chart.id, f"{chart.song.name} - {chart.rerate_name}") for chart in Chart.query.all()]
    lengthtype_pairs = [(length.id, length.name) for length in Length.query.all()]

    gamemix_pairs = [(mix.id, mix.name) for mix in GameMix.query.order_by(GameMix.sort_order.desc()).all()]

    judgement_pairs = (
        ('nj', 'Normal Judgement'),
        ('hj', 'Hard Judgement'),
        ('vj', 'Very Hard Judgement')
    )

    category_pairs = [(category.id, category.name) for category in Category.query.all()]

    charts = {chart.id: chart for chart in Chart.query.all()}
    gamemixes = {gamemix.id: gamemix for gamemix in GameMix.query.all()}
    lengths = {length.id: length for length in Length.query.all()}
    languages = {language.id: language for language in Language.query.all()}
    songid_to_songtitle = {languages[lid].code: {songtitle.song.id: songtitle for songtitle in SongTitle.query.filter_by(language_id=lid).all()} for lid in languages}
    modes = {mode.id: mode for mode in Mode.query.all()}

    @app.context_processor
    def inject_charts():
        return dict(charts=charts)
    @app.context_processor
    def inject_gamemixes():
        return dict(gamemixes=gamemixes)
    @app.context_processor
    def inject_lengths():
        return dict(lengths=lengths)
    @app.context_processor
    def inject_languages():
        return dict(languages=languages)
    @app.context_processor
    def inject_songid_to_songtitle():
        return dict(songid_to_songtitle=songid_to_songtitle)
    @app.context_processor
    def inject_modes():
        return dict(modes=modes)

    apikey_required = app.config['ENABLE_API_KEY']  # also ip address requirement

    approved_ips = []
    if apikey_required:
        try:
            with open('approved_ips.txt', 'r') as f:
                approved_ips = [x.replace('\n','').strip() for x in f.readlines()]
        except:
            app.logger.info("WARNING: API key requirement enabled but no whitelisted IP addresses could be read. No one will be able to use API functionality even with an API key.")

    if app.config['ENABLE_FASTAI_SCORE_DETECTION']:
        from fastai import load_learner
        score_learner = load_learner(Path('../fastai_ml/model-s2.pkl'))

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