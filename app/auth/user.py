from flask import request, jsonify, g
from app import db, client
from app.auth import auth
from app.models import User

__author__ = 'songhua'

@auth.route('/reg',methods=['POST','GET'])
def register_user():
    user = User.from_json(request.json)
    db.session.add(user)
    db.session.commit()

    db.session.commit()

    return jsonify({
        'result':'200',
        'id':user.id
    })


@auth.route('/email_login', methods=['POST', 'GET'])
def email_login():
    email = request.json.get('email')
    password = request.json.get('password')

    user = User.query.filter_by(email = email).first()
    if user:
        if user.verify_password(password):
            g.current_user = user
            return jsonify({
                'result': '200',
                'id': user.id
            })

    return jsonify({
                'result': '401',
            })


@auth.route('/token')
def get_token():
    user = g.current_user
    result = client.user_get_token(user_id=user.id,name=user.username)
    if result[u'code'] == 200 and result[u'userId'] == user.id:
        return result[u'token']
    else:
        return '-1'


@auth.route('/logoutuser')
def userlogout():
    g.current_user = None