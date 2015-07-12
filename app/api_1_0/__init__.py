from app import db
from app.models import post_up
from manage import app

__author__ = 'songhua'
from flask import Blueprint

api = Blueprint('api',__name__)
from app.api_1_0 import posts,users,classes,comments,authentication,errors

@api.route('/initdb')
def init_db():
    db.create_all()
    return 'db is inited'

@api.route('/deldb')
def del_post():
    engine = db.get_engine(app)
    post_up.drop(engine)

    return 'post_up is del'


