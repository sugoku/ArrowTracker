from app import db, create_app
from app.models import *
app = create_app()
app.app_context().push()
db.create_all()