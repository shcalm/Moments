#coding=utf-8
import json
from flask import jsonify, request, current_app, url_for, g
from . import api
from app import db, client
from ..models import User, Post,Class, Friend_List
import logging

def send_request_to_peer(id_from, id_to, pushcontent):
    return client.message_system_publish(
        from_user_id=id_from,
        to_user_id=id_to,
        object_name='RC:ContactNtf',
        content=json.dumps({"message": u"好友请求：" + pushcontent, "sourceUserId":id_from,"targetUserId":id_to}),
        push_content='send add friend request',
        push_data='send add friend request')


@api.route('/users/<id>')
def get_user(id):
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



#I divide the friendlist 2 pars 1 is own add friend,the other is user group list
@api.route('/users/getmyfriends')
def get_user_friends():
    
    user = g.current_user
    groupfriend = user.getallmyfriend()

    if user is not None:
        return jsonify({
            'status': 200,
            'friend': [
                User.query.filter_by(id=f_id).first().to_json() for f_id in groupfriend
                ]
        })
    else:
        return jsonify({
            'status': 404
        })

@api.route('/users/getdefaultgroup')
def get_user_default_group():
    user = g.current_user
    if user is not None:
        return jsonify({
            "status":200,
            "defaultclass":user.default_cls
            })
    else:
        return jsonify({
            "status":400
        })
@api.route('/users/setdefaultgroup',methods=['POST'])
def set_user_default_group():
    default = request.form.get('defaultclass')
    user = g.current_user
    if user is not None and default > 0:
        user.default_cls = default
        db.session.add(user)
        db.session.commit()

        return jsonify({
            "status": 200
        })
    else:
        return jsonify({
            "status": 400
        })
@api.route('/users/changeportrait',methods=['POST'])
def chanage_portrait():
    new_portrait = request.form.get('portrait')
    user = g.current_user
    if user is not None :
        #user.portrait = new_portrait
        user.change_portrait(new_portrait)
        return jsonify({
            "status":200
        })
    return jsonify({
        "status":400
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
        if user is not None:
            return user.to_json()
    else:
        if name is not None:
            user = User.query.filter(User.username.like("%" + name + "%")).all()
            if user is not None:
                #return user.to_json()
                 return jsonify({
                     'status':200,
                     'users':
                     [
                         u.to_json() for u in user
                     ]
                     }                  
                 )

    return jsonify({
        'status': 404
    })


@api.route('/users/addfriend', methods=['POST', 'GET'])
def add_friend():
    id = request.form.get('id')
    pushcontent = request.form.get('content',default=u'')
    user = User.query.filter_by(id=id).first()
    logging.error(user)
    if user is not None:
        isfriend = g.current_user.is_friend(user)
        if isfriend == False:
            result = send_request_to_peer(g.current_user.id, id, pushcontent)
            return jsonify({
                'status': result[u'code']
            })
        else:
            return jsonify({
                "status":408
            })

    else:
        return jsonify({
            'status': 404

        })

@api.route('/user/confirm',methods=['POST','GET'])
def confirm_friend():
    userid = request.form.get('id')
    user = User.query.filter_by(id=userid).first()
    if user is not None:
        # if not in the friendlist
        if g.current_user.add_friend(user):

            result = client.message_system_publish(
                    from_user_id=g.current_user.id,
                    to_user_id=userid,
                    object_name='RC:ContactNtf',
                    content=json.dumps({"message": u"已成功添加为好友", "sourceUserId":g.current_user.id,"targetUserId":userid}),
                    push_content='confirm',
                    push_data='confirm'
                    )
            return jsonify({
                    'status':result[u'code']
                })
        else:
            return jsonify({
                    'status':408,
                })
    else:
        return jsonify({
                    'status':404
                })
    
    

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
