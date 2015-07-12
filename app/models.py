from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach
from flask import current_app, request, url_for, g, jsonify
from flask.ext.login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager

# class User(UserMixin, db.Model):
#     __tablename__ = 'users'
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(64), unique=True, index=True)
#     username = db.Column(db.String(64), unique=True, index=True)
#     role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
#     password_hash = db.Column(db.String(128))
#     confirmed = db.Column(db.Boolean, default=False)
#     name = db.Column(db.String(64))
#     location = db.Column(db.String(64))
#     about_me = db.Column(db.Text())
#     member_since = db.Column(db.DateTime(), default=datetime.utcnow)
#     last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
#     avatar_hash = db.Column(db.String(32))
#     posts = db.relationship('Post', backref='author', lazy='dynamic')
#
#     comments = db.relationship('Comment', backref='author', lazy='dynamic')
#
#     def verify_password(self, password):
#         return check_password_hash(self.password_hash, password)
#
#     def generate_confirmation_token(self, expiration=3600):
#         s = Serializer(current_app.config['SECRET_KEY'], expiration)
#         return s.dumps({'confirm': self.id})
#
#     def confirm(self, token):
#         s = Serializer(current_app.config['SECRET_KEY'])
#         try:
#             data = s.loads(token)
#         except:
#             return False
#         if data.get('confirm') != self.id:
#             return False
#         self.confirmed = True
#         db.session.add(self)
#         return True
#
#     def generate_reset_token(self, expiration=3600):
#         s = Serializer(current_app.config['SECRET_KEY'], expiration)
#         return s.dumps({'reset': self.id})
#
#     def reset_password(self, token, new_password):
#         s = Serializer(current_app.config['SECRET_KEY'])
#         try:
#             data = s.loads(token)
#         except:
#             return False
#         if data.get('reset') != self.id:
#             return False
#         self.password = new_password
#         db.session.add(self)
#         return True
#
#     def generate_email_change_token(self, new_email, expiration=3600):
#         s = Serializer(current_app.config['SECRET_KEY'], expiration)
#         return s.dumps({'change_email': self.id, 'new_email': new_email})
#
#     def change_email(self, token):
#         s = Serializer(current_app.config['SECRET_KEY'])
#         try:
#             data = s.loads(token)
#         except:
#             return False
#         if data.get('change_email') != self.id:
#             return False
#         new_email = data.get('new_email')
#         if new_email is None:
#             return False
#         if self.query.filter_by(email=new_email).first() is not None:
#             return False
#         self.email = new_email
#         self.avatar_hash = hashlib.md5(
#             self.email.encode('utf-8')).hexdigest()
#         db.session.add(self)
#         return True
#
#
#     def generate_auth_token(self, expiration):
#         s = Serializer(current_app.config['SECRET_KEY'],
#                        expires_in=expiration)
#         return s.dumps({'id': self.id}).decode('ascii')
#
#     @staticmethod
#     def verify_auth_token(token):
#         s = Serializer(current_app.config['SECRET_KEY'])
#         try:
#             data = s.loads(token)
#         except:
#             return None
#         return User.query.get(data['id'])
#
#     def __repr__(self):
#         return '<User %r>' % self.username


# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))

# class OfUser(db.Model):
#     __tablename_ = 'OfUser'
#

class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
   # users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'ofuser'
    username = db.Column(db.String(64),primary_key = True)
    encryptedPassword = db.Column(db.String(255))

    def verify_password(self, password):
        return self.encryptedPassword == password

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    def __repr__(self):
        return '<User %r>' % self.username
    def to_json(self):
        return jsonify({
            'username':self.username,
            'usericon':None
        })

class Class(db.Model):
    __tablename__ = 'ofMucRoom'
    serviceID = db.Column(db.BIGINT,primary_key=True)
    name = db.Column(db.String(50))


post_up = db.Table('post_up',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id')),
    db.Column('user_id', db.String(64), db.ForeignKey('ofuser.username')),
    db.Column('timestamp',db.DateTime, index=True, default=datetime.now().strftime('%Y-%m-%d %H:%M'))
)


class PostImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    img_md5 = db.Column(db.VARCHAR(255))

    @staticmethod
    def from_json(json_imgs):
        urls = json_imgs.get('urls')


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now().strftime('%Y-%m-%d %H:%M'))
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.VARCHAR(64),db.ForeignKey('ofuser.username'))

    replyname = db.Column(db.VARCHAR(64),db.ForeignKey('ofuser.username'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        #json_comment = {
        #    'url': url_for('api.get_comment', id=self.id, _external=True),
        #    'post': url_for('api.get_post', id=self.post_id, _external=True),
        #    'body': self.body,
        #    'body_html': self.body_html,
        #    'timestamp': self.timestamp,
        #    'author': url_for('api.get_user', id=self.author_id,
        #                      _external=True),
        #}

        new_json_comment = {
            'replyId':self.id,
            'replyName':self.author_id,
            'isReplyName':self.replyname,
            'comment':self.body
        }
        return new_json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('comment')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        author_id = g.current_user.username
        replyname = json_comment.get('isReplyName')
        return Comment(body=body,author_id=author_id,replyname=replyname)


db.event.listen(Comment.body, 'set', Comment.on_changed_body)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    author_id = db.Column(db.String(64),db.ForeignKey(User.username))
    class_id = db.Column(db.BIGINT,db.ForeignKey(Class.serviceID))
    imgs = db.relationship('PostImage',backref='imgpost',lazy='dynamic')

    ups = db.relationship('User', secondary=post_up,
        backref=db.backref('posts', lazy='dynamic'),order_by=post_up.c.timestamp)#order_by="post_up.columns['timestamp']"

    comments = db.relationship('Comment', backref='post', lazy='dynamic',order_by=Comment.timestamp)#,order_by="comments.timestamp"

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        #json_post = {
        #    'url': url_for('api.get_post', id=self.id, _external=True),
        #    'body': self.body,
        #    'body_html': self.body_html,
        #    'timestamp': self.timestamp,
        #    'author': url_for('api.get_user', username=self.author_id,
        #                      _external=True),
        #    'class':url_for('api.get_class',id=self.class_id,
        #                    _external= True),
        #    'comments': url_for('api.get_post_comments', id=self.id,
        #                        _external=True),
        #    'comment_count': self.comments.count()
        #}
        new_josn_post={
            'id':self.id,
            'content':self.body,
            'uname':self.author_id,
            'sendtime':self.timestamp.strftime('%Y-%m-%d %H:%M'),
            'usericon': None,
            'urls':[
                img.img_md5 for img in self.imgs
            ],
            'friendcomment':[
               c.to_json() for c in self.comments
            ],
            'friendpraise':[
                up.username for up in self.ups
            ]

       }
        return new_josn_post

    @staticmethod
    def from_json(json_post):
        body = json_post.get('content')
        timestamp = json_post.get('sendtime')
        author_id = g.current_user.username
        if body is None or body == '':
            raise ValidationError('post does not have a body')

        return Post(body=body,timestamp=timestamp,author_id=author_id)


db.event.listen(Post.body, 'set', Post.on_changed_body)


