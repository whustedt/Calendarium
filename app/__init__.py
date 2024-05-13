from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)

    with app.app_context():
        
        from .models import Entry
        db.create_all()

        from .routes import init_app as init_routes
        init_routes(app)
    
    return app
