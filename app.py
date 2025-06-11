import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure the PostgreSQL database (falls back to SQLite if DATABASE_URL is not set)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///business_reports.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Maximum content length for file uploads (20MB)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to register them with SQLAlchemy
    import models  # noqa: F401
    
    # Create all tables in the database
    db.create_all()

# Import and register routes
from routes import register_routes
register_routes(app)
