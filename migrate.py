from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from flask_user import UserMixin
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

