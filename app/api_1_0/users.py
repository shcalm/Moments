import json
from flask import jsonify, request, current_app, url_for, g
from . import api
from app import db, client
from ..models import User, Post,Class


def send_request_to_peer(id_from, id_to):
    return client.message_system_publish(
        from_user_id=id_from,
        to_user_id=id_to,
        object_name='RC:ContactNtf',
        content=json.dumps({"content": "send request", 'id': id_from}),
        push_content='send add request',
        push_data='send add request')


@api.route('/users/<id>')
def get_user(username):
    user = User.query.filter_by(id=id).first()
    if user is not None:
        return jsonify(user.to_json())
    else:
        return jsonify({
            "status": 404
        })


@api.route('/users/<username>/posts/')
def get_user_posts(username):
    user = User.query.get_or_404(username)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', page=page + 1, _external=True)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/users/getmyfriends')
def get_user_friends():
    
    user = g.current_user
    if user is not None:
        return jsonify({
            'status': 200,
            'friend': [
                f.id for f in user.friendlist
                ]
        })
    else:
        return jsonify({
            'status': 404
        })


@api.route('/users/getmygroups')
def get_user_groups():
    user = g.current_user
    if user is not None:
        return jsonify({
            'status': 200,
            'groups': [
                Class.query.filter_by(id = c.class_id).first().to_json() for c in user.classlist
                ]
        })
    else:
        return jsonify({
            'status': 404
        })


@api.route('/users/search', methods=['POST', 'GET'])
def search_user():
    id = request.form.get('id')
    name = request.form.get('name')
    if id is not None:
        user = User.query.filter_by(id=id).first()
    else:
        if name is not None:
            user = User.query.filter(User.name.like("%" + name + "%")).first()
            if user is not None:
                return user.to_json()
    return jsonify({
        'status': 404
    })


@api.route('/users/addfriend', methods=['POST', 'GET'])
def add_friend():
    id = request.form.get('id')
    user = User.query.filter_by(id=id).first()
    if user is not None:
        result = send_request_to_peer(g.current_user.id, id)
        if result[u'code'] == 200:
            return jsonify({
                'status': 200,
                'message': 'have send to peer'
            })
        else:
            return jsonify({
                'status': 400,
                'message': 'send failed'
            })
    else:
        return jsonify({
            'status': 401,
            'message': 'not this class'
        })

# class_id = request.form.get('class_id')
#     userid = request.form.get('user_id')
#     user = User.query.filter_by(id=userid).first()
#     if user is not None:
#         # sel = Class_User.select(Class_User.friend_id == user.id & Class_User.class_id == class_id)
#         cls_usr = Class_User.query.filter_by(friend_id=userid, class_id=class_id).first()
#         if cls_usr is None:
#             cls_usr = Class_User(friend_id=userid, class_id=class_id)
#             db.session.add(cls_usr)
#             db.session.commit()

#             result = client.group_join(
#                 user_id_list=[userid],
#                 group_id=class_id,
#                 group_name=Class.query.filter_by(id=class_id).first().name
#             )
#             if result[u'code'] == 200: 
#                 client.message_system_publish(
#                     from_user_id=g.current_user.id,
#                     to_group_id=class_id,
#                     object_name='RC:ContactNtf',
#                     content=json.dumps({"message": "confirm"}),
#                     push_content='confirm',
#                     push_data='confirm',
#                     extra=class_id)
#             else:
#                 return jsonify({
#                     "status": result[u'code'],
#                 })
#         else:
#             return jsonify({
#                 "status": 408,
#                 "message": "has enroll in"
#             })

@api.route('/user/confirm',methods=['POST','GET'])
def confirm_friend():
    userid = request.form.get('id')
    user = User.query.filter_by(id=userid).first()
    if user is not None:
        pass
    
    

@api.route('/users/<int:id>/timeline/')
def get_user_followed_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', page=page + 1, _external=True)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })
