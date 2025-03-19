from app import app
from lib.db import db

with app.app_context():
    db.setup_tables(db.cursor())
