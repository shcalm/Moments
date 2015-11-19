#coding=utf-8
import json
from flask import jsonify, g, request
from app import client, db
from app.api_1_0 import api
from app.models import Comment, Class, User, Class_User


def send_request_to_admin(id_from, id_to,classid,pushcontent):
    if pushcontent is None :
        pushcontent = 'send enroll request'
        
    return client.message_system_publish(
        from_user_id=id_from,
        to_user_id=id_to,
        object_name='RC:ContactNtf',
        content=json.dumps({"message": u"加入班级请求：" + pushcontent, "sourceUserId":id_from,"targetUserId":id_to,"operation":"add","extra":classid}),
        push_content= pushcontent,
        push_data= pushcontent)


@api.route('/class/search', methods=['POST', 'GET'])
def search_class():
    id = request.form.get('id')
    name = request.form.get('name')
    if id is not None:
        cls = Class.query.filter_by(id=id)
        if cls is not None:
            return cls.to_json()
    else:
        if name is not None:
            cls = Class.query.filter(Class.name.like("%" + name + "%")).all()
            if cls is not None:
                return jsonify({
                    'status':200,
                   'classes':[
                         c.to_json() for c in cls
                   ]
                }) 
    return jsonify({
            'status': 404
        })


@api.route('/class/<id>')
def get_class(id):
    pass


@api.route('/class/enroll/<id>', methods=['POST', 'GET'])
def enroll(id):
    cls = Class.query.filter_by(id=id).first()
    pushcontent = request.form.get('content')
    if cls is not None:
        admin = cls.create_user_id
        result = send_request_to_admin(g.current_user.id, admin,id,pushcontent)
        return jsonify({
                'status': result[u'code']

            })
    else:
        return jsonify({
            'status': 404,
            'message': 'not this class'
        })



@api.route('/class/confirm', methods=['POST', 'GET'])
def confirm_enroll():
    class_id = request.form.get('class_id')
    userid = request.form.get('user_id')
    user = User.query.filter_by(id=userid).first()
    if user is not None:
        # sel = Class_User.select(Class_User.friend_id == user.id & Class_User.class_id == class_id)
        cls_usr = Class_User.query.filter_by(friend_id=userid, class_id=class_id).first()
        if cls_usr is None:
            cls_usr = Class_User(friend_id=userid, class_id=class_id)
            db.session.add(cls_usr)
            db.session.commit()

            result = client.group_join(
                user_id_list=[userid],
                group_id=class_id,
                group_name=Class.query.filter_by(id=class_id).first().name
            )
            
            if result[u'code'] == 200: 
                cls = Class.query.filter_by(id = class_id).first()
                cls.increase_number()
                
                rel = client.message_group_publish(
                    from_user_id=g.current_user.id,
                    to_group_id=class_id,
                    object_name='RC:ContactNtf',
                    content=json.dumps({"message": user.username + u"已成功加入到班级"}),
                    push_content='confirm',
                    push_data='confirm',
                    )
                return jsonify({
                    "status":rel[u'code']
                })
            else:
                return jsonify({
                    "status": result[u'code'],
                })
        else:
            return jsonify({
                "status": 408,
                "message": "has enroll in"
            })
    else:
        return jsonify({
            "status":404
        })


@api.route('/class/create', methods=['POST', 'GET'])
def create_class():
    user = g.current_user
    # admin_id = Role.query.filter_by(name='Administrator').first().id
    # if user.role_id != admin_id:
    #     return jsonify({
    #         "status":408
    #     })
    data = request.form
    name = data.get('name')
    tmp = Class.query.filter_by(name=name).first()
    if tmp is not None:
        return jsonify({
            "status":400
        })
     
    cls = Class.from_form(data)
    db.session.add(cls)
    db.session.commit()

    cls.add_user(user.id)

    result = client.group_create(
        user_id_list=[user.id],
        group_id=cls.id,
        group_name=cls.name
    )
    if result[u'code'] == 200:
        return jsonify({
            'status': 200,
            'id': cls.id
        })
    else:
        return jsonify({
            'status': result[u'code']
        })


def find_admin():
    pass
