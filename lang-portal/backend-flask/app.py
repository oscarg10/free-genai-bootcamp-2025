from flask import Flask, g
from flask_cors import CORS
from dotenv import load_dotenv
import os

from lib.db import Db

import routes.words
import routes.groups
import routes.study_sessions
import routes.dashboard
import routes.study_activities

# Load environment variables
load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__)
    
    # Development configuration
    app.config.update(
        SECRET_KEY=os.environ['SECRET_KEY'],
        DEBUG=os.environ.get('DEBUG', 'True').lower() == 'true',
        ENV='development'
    )

    # Enable CORS for development
    CORS(app, origins=os.environ.get('ALLOWED_ORIGINS', '*'))
    
    # Initialize database
    app.db = Db(os.environ.get('DATABASE_URL', 'sqlite:///words.db'))
    
    @app.teardown_appcontext
    def close_db(exception):
        app.db.close()

    # Test config route
    @app.route('/test-config')
    def test_config():
        return {
            'environment': app.config['ENV'],
            'debug': app.config['DEBUG'],
            'has_secret_key': bool(app.config['SECRET_KEY']),
            'env_vars_loaded': bool(os.environ.get('SECRET_KEY'))
        }

    # Load routes
    routes.words.load(app)
    routes.groups.load(app)
    routes.study_sessions.load(app)
    routes.dashboard.load(app)
    routes.study_activities.load(app)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)