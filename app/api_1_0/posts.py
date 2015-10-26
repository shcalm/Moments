from datetime import datetime
from flask import jsonify, request, g, abort, url_for, current_app, render_template
from .. import db
from sqlalchemy import func
from ..models import Post, Permission, PostImage, post_up
from . import api
from .decorators import permission_required
from .errors import forbidden

@api.route('/')
def get_index():
    return render_template('index.html')


@api.route('/posts/')
def get_posts():
    page = request.args.get('page', 1, type=int)
    classid = request.args.get('classid',-1,type=int)
    per_page = current_app.config['FLASKY_POSTS_PER_PAGE']
    total = Post.query.count()
    if classid < 0:
        return jsonify({
            "status":400
        })

    pagination = Post.query.filter_by(class_id = classid).order_by(Post.timestamp.desc()).paginate(
        page, per_page,error_out=False)
    posts = pagination.items
    showNum = len(posts)
    #prev = None
    #if pagination.has_prev:
    #    prev = url_for('api.get_posts', page=page-1, _external=True)
    #next = None
    #if pagination.has_next:
    #    next = url_for('api.get_posts', page=page+1, _external=True)
    return jsonify({
        'friendPager':{
            'offset':(page-1)*per_page,
            'showNum':showNum,
            'total':total,
            'datas':[
                post.to_json() for post in posts
            ],
        },

    })




@api.route('/posts/<int:id>')
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())


@api.route('/posts/', methods=['POST'])
#@permission_required(Permission.WRITE_ARTICLES)
def new_post():
    post = Post.from_json(request.json)
    #post.author = g.current_user
    db.session.add(post)
    db.session.commit()

    for url in request.json.get('urls'):
        img = PostImage(post_id=post.id,img_md5=url)
        db.session.add(img)

    db.session.commit()

#    return jsonify(post.to_json()), 201, \
#        {'Location': url_for('api.get_post', id=post.id, _external=True)}
    return jsonify({
        'result':'200',
        'id':post.id
    })


@api.route('/posts/<int:id>', methods=['PUT'])
#@permission_required(Permission.WRITE_ARTICLES)
def edit_post(id):
    post = Post.query.get_or_404(id)
    if g.current_user != post.author and \
            not g.current_user.can(Permission.ADMINISTER):
        return forbidden('Insufficient permissions')
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    return jsonify(post.to_json())

@api.route('/posts/<int:id>/praise',methods=['POST'])
def post_praise(id):
    #post = Post.query.get_or_404(id)
    time = None
    if request.json != [] and request.json != None:
        time = request.json.get('timestamp')
    else:
        time = datetime.now().strftime('%Y-%m-%d %H:%M')

    sel = post_up.select((post_up.c.post_id == id) & (post_up.c.user_id ==g.current_user.id))
    rs = db.session.execute(sel).fetchall()
   # rs = sel.execute()
    if rs == []:
        e = post_up.insert().values(post_id=id,user_id=g.current_user.id,timestamp=time)
        db.session.execute(e)
    else:
        e = post_up.delete().where(post_up.c.post_id==id and post_up.c.post_id==g.current_user.id)
        db.session.execute(e)
    return jsonify({
        "status":200
    })

