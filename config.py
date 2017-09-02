import os
basedir = os.path.abspath(os.path.dirname(__file__))

MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = "falcon.arista@gmail.com"
MAIL_PASSWORD = "arista1718"
ADMINS = ["jasch@stuy.edu", "izhang1@stuy.edu"]

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
WHOOSH_BASE = os.path.join(basedir, 'search.db')

SECURITY_RECOVERABLE = True

MAX_SEARCH_RESULTS = 50

UPLOAD_FOLDER = 'app/data/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpeg', 'jpg'}


WTF_CSRF_ENABLED = True
SECRET_KEY = 'webdev-blog'

POSTS_PER_PAGE = 10
DOMAIN = "localhost:5000"