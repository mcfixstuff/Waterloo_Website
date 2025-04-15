import os
from flask import Flask
from config import dev_config
from .extensions.db import db
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

#TODO: Change the servername later on
#Add the config loads
def create_app(config_class = dev_config):
    app = Flask(__name__, template_folder=os.path.abspath("app/templates"),
                static_folder=os.path.abspath("app/static"))
    app.config.from_object(config_class)

    # Initialize the database
    db.init_app(app)

    # Initialize Flask-Migrate (optional)
    Migrate(app, db)

    # Set a secret key for session management
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    
    # Set server name to use localhost for redirect URIs
    app.config['SERVER_NAME'] = 'localhost:7070'
    app.config["APP_ROOT"] = os.path.dirname(os.path.abspath(__file__))

    # Import and register Blueprints
    from app.routes.main import main
    from app.routes.auth import auth
    from app.routes.admin import admin
    from app.routes.dashboard import dashboard
    from app.routes.approval import approval_bp
    from app.routes.api import api  # Import the new API blueprint
    
    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(approval_bp, url_prefix="/approval")
    app.register_blueprint(api)  # Register the API blueprint

    return app
