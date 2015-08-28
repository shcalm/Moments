from . import main
from flask import render_template
from app import db
from app.models import Role
@main.route('/')
def index():
	return render_template('index.html')

@main.route('/initdb')
def init_db():
    db.create_all()
    Role.insert_roles()
    return 'db is inited'

@main.route('/deldb')
def del_post():
    engine = db.get_engine(db.get_app())
    post_up.drop(engine)

    return 'post_up is del'
