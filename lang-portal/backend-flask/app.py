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
import routes.word_groups

# Load environment variables
load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__)
    
    # Configure CORS to allow requests from frontend
    CORS(app, resources={
        r"/*": {
            "origins": [
                "http://localhost:5173",  # Vite dev server
                "http://localhost:3000",  # Alternative React port
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Development configuration
    app.config.update(
        SECRET_KEY=os.environ['SECRET_KEY'],
        DEBUG=os.environ.get('DEBUG', 'True').lower() == 'true',
        ENV='development'
    )

    # Initialize database with absolute path
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'lang_portal.db')
    app.db = Db(f'sqlite:///{db_path}')
    
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
    # Try different ports if the default one is in use
    for port in range(5100, 5110):  # Try ports 5100-5109
        try:
            app.run(host='0.0.0.0', debug=True, port=port)  # Listen on all interfaces
            print(f"\nFlask app running at: http://localhost:{port}")
            break
        except OSError:
            if port == 5109:  # Last port to try
                raise
            continue