from . import main
from flask import render_template
from app import db

@main.route('/')
def index():
	return render_template('index.html')

@main.route('/initdb')
def init_db():
    db.create_all()
    return 'db is inited'

@main.route('/deldb')
def del_post():
    engine = db.get_engine(db.get_app())
    post_up.drop(engine)

    return 'post_up is del'
