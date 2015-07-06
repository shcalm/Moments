from app import db

__author__ = 'songhua'
from flask import Blueprint

api = Blueprint('api',__name__)
from app.api_1_0 import posts,users,classes,comments,authentication,errors

@api.route('/initdb')
def init_db():
    db.create_all()
    return 'db is inited'