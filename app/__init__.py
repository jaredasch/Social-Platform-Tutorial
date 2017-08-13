from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from .momentjs import momentjs

app = Flask(__name__)
app.config.from_object("config")
db = SQLAlchemy(app)

app.jinja_env.globals['momentjs'] = momentjs

lm = LoginManager()
lm.init_app(app)

mail = Mail(app)

from app import views, models
