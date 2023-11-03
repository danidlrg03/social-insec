"""Provides the app package for the Social Insecurity application. The package contains the Flask app and all of the extensions and routes."""

from pathlib import Path
from typing import cast

from flask import Flask

from app.config import Config
from app.database import SQLite3
from app.models import User

from flask_login import LoginManager, UserMixin

from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

# Instantiate and configure the app
app = Flask(__name__)
app.config.from_object(Config)

# Instantiate the sqlite database extension
sqlite = SQLite3(app, schema="schema.sql")

# Handle login management better, maybe with flask_login?
login = LoginManager(app)
login.init_app(app)
login.login_view = "index"
login.login_message_category = "info"
from app.models import User

# ...

@login.user_loader
def load_user(user_id):
    get_user = f"""SELECT * FROM USERS WHERE id = '{user_id}' ;"""
    user = sqlite.query(get_user, one=True)
    if user is not None:
        return User(*user)
    return None


# The passwords are stored in plaintext, this is not secure at all. I should probably use bcrypt or something
bcrypt = Bcrypt(app)


# The CSRF protection is not working, I should probably fix that
csrf = CSRFProtect(app)
csrf.init_app(app)

# Create the instance and upload folder if they do not exist
with app.app_context():
    instance_path = Path(app.instance_path)
    if not instance_path.exists():
        instance_path.mkdir(parents=True, exist_ok=True)
    upload_path = instance_path / cast(str, app.config["UPLOADS_FOLDER_PATH"])
    if not upload_path.exists():
        upload_path.mkdir(parents=True, exist_ok=True)

# Import the routes after the app is configured
from app import routes  # noqa: E402,F401
