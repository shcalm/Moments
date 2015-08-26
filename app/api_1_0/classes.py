import json
from flask import jsonify, g
from app import client
from app.api_1_0 import api
from app.models import Comment, Class


@api.route('/comments/<int:id>')
def get_class(id):
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())

@api.route('/class/search/<id>')
def search_class(id):
    cls = Class.query.filter_by(id = id)
    user = g.current_user

    if cls is not None:
        return jsonify({
            'id':cls.id,
            'status':200
        })
    else:
        return jsonify({
            'status':401
        })

def send_request_to_admin():
    client.message_system_publish(
            from_user_id='test-userid1',
            to_user_id='test-userid2',
            object_name='RC:TxtMsg',
            content=json.dumps({"content":"hello"}),
            push_content='thisisapush',
            push_data='aa')
