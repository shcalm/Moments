from flask import jsonify
from app.api_1_0 import api
from app.models import Comment


@api.route('/comments/<int:id>')
def get_class(id):
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())