import json
from flask import jsonify, g, request
from app import client, db
from app.api_1_0 import api
from app.models import Comment, Class, User, Class_User

def send_request_to_admin(id_from, id_to):
    return  client.message_system_publish(
        from_user_id=id_from,
        to_user_id=id_to,
        object_name='RC:TxtMsg',
        content=json.dumps({"content": "send request", 'id': id_from}),
        push_content='send enroll request',
        push_data='send enroll request')


@api.route('/class/search')
def search_class():
    id = request.args.get('id')
    name = request.args.get('name')
    if id is not None:
        cls = Class.query.filter_by(id=id)
    else:
        if name is not None:
            cls = Class.query.filter(Class.name.like("%"+name+"%")).first()

    user = g.current_user

    if cls is not None:
        return jsonify({
            'id': cls.id,
            'portrait': cls.portrait,
            'name': cls.name,
            'introduce': cls.introduce,
            'status': 200
        })
    else:
        return jsonify({
            'status': 401
        })




@api.route('/class/<id>')
def get_class(id):
    pass


@api.route('/class/enroll/<id>', methods=['POST', 'GET'])
def enroll(id):
    cls = Class.query.filter_by(id=id).first()
    if cls is not None:
        admin = cls.create_user_id
        result = send_request_to_admin(g.current_user.id,admin)
        if result[u'code'] == 200:
            return jsonify({
                'status':200,
                'message':'have send to admin'
            })
        else:
            return jsonify({
                'status':400,
                'message':'send failed'
            })
    else:
        return jsonify({
                'status':401,
                'message':'not this class'
            })

   # sel = post_up.select((post_up.c.post_id == id) & (post_up.c.user_id ==g.current_user.username))
   # rs = db.session.execute(sel).fetchall()
   ## rs = sel.execute()
   # if rs == []:
   #     e = post_up.insert().values(post_id=id,user_id=g.current_user.username,timestamp=time)
   #     db.session.execute(e)
   # else:
   #     e = post_up.delete().where(post_up.c.post_id==id and post_up.c.post_id==g.current_user.username)
   #     db.session.execute(e)

@api.route('/class/confirm',methods=['POST','GET'])
def confirm_enroll():
    class_id = request.get_json()['class_id']
    userid = request.get_json()['user_id']
    user = User.query.filter_by(id=userid).first()
    if user is not None:
       # sel = Class_User.select(Class_User.friend_id == user.id & Class_User.class_id == class_id)
        cls_usr = Class_User.query.filter_by(friend_id = userid , class_id = class_id).first()
        if cls_usr is None:
            cls_usr = Class_User(friend_id=userid,class_id=class_id)
            db.session.add(cls_usr)
            db.session.commit()

            result = client.group_join(
                user_id_list=[userid],
                group_id=class_id,
                group_name=Class.query.filter_by(id=class_id).first().name
            )
            if result[u'code'] == 200:
                 client.message_system_publish(
                    from_user_id=g.current_user.id,
                    to_user_id=userid,
                    object_name='RC:TxtMsg',
                    content=json.dumps({"content":"confirm"}),
                    push_content='confirm',
                    push_data='confirm')
            else:
                return jsonify({
                    "status": result[u'code'],
                })
        else:
            return jsonify({
            "status": 408,
            "message": "has enroll in"
        })

@api.route('/class/create', methods=['POST', 'GET'])
def create_class():
    data = request.json
    cls = Class.from_json(data)
    db.session.add(cls)
    db.session.commit()

    result = client.group_create(
        user_id_list=[g.current_user.id],
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
            'status':result[u'code']
        })


def find_admin():
    pass




