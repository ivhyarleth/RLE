from flask import Flask

from .webhook import webhook_routes
from .utils import *

def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(webhook_routes)
    
    return app