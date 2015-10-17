from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from app.rongcloud.rong import ApiClient
from config import config
from flask.ext.pagedown import PageDown
import logging
db = SQLAlchemy()
pagedown = PageDown()
mail = Mail()
client = ApiClient()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

def create_app(confi):
    app = Flask(__name__)
    print confi
    app.config.from_object(config[confi])
    db.init_app(app)
    pagedown.init_app(app)
    logging.error('starting kchat')
    from api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint,url_prefix='/api/v1.0')

    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint,url_prefix='/auth')

    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
