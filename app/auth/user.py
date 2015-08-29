import json
from flask import request, jsonify, g
from flask_httpauth import HTTPBasicAuth
from .. import db, client
from . import auth
from ..models import User, Class

basicauth = HTTPBasicAuth()

@auth.route('/reg',methods=['POST','GET'])
def register_user():
    user = User.from_form(request.form)
    db.session.add(user)
    db.session.commit()
    return jsonify({
        'result':'200',
        'id':user.id
    })


@auth.route('/email_login', methods=['POST', 'GET'])
def email_login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email = email).first()
    if user is not None:
        if user.verify_password(password):
            g.current_user = user
            clslist = user.classlist
            clsmap = {}
            for cls in clslist:
                clsmap[cls.class_id] = Class.query.filter_by(id=cls.class_id).first().name
            if clsmap != {}:
                result = client.group_sync(
                    user_id=user.id,
                    groups=clsmap
                )
            return jsonify({
                'result': '200',
                'id': user.id
            })

    return jsonify({
                'result': '401',
            })

@basicauth.verify_password
def verify_password(username_or_token, password):
    if username_or_token == '':
        return False
    if password == '':
        g.current_user = User.verify_auth_token(username_or_token)

        return g.current_user is not None

    user = User.query.filter_by(username=username_or_token).first()

    if not user:
        return False
    g.current_user = user

    return user.verify_password(password)

@basicauth.error_handler
def auth_error():
    response = jsonify({'error': 'unauthorized', 'message': 'Invalid credentials'})
    response.status_code = 401
    return response

@auth.route('/token')
@basicauth.login_required
def get_token():
    user = g.current_user
    result = client.user_get_token(user_id=user.id,name=user.username,portrait_uri= user.portrait)
    if result[u'code'] == 200 and result[u'userId'] == str(user.id):
        return result[u'token']
    else:
        return '-1'


@auth.route('/logoutuser')
def userlogout():
    g.current_user = None