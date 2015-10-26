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

post_up = db.Table('post_up',
                   db.Column('post_id', db.Integer, db.ForeignKey('posts.id')),
                   db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                   db.Column('timestamp', db.DateTime, index=True, default=datetime.now().strftime('%Y-%m-%d %H:%M'))
                   )


# class_user = db.Table('class_user',
#    db.Column('id',db.Integer,primary_key=True),
#    db.Column('class_id', db.Integer, db.ForeignKey('class_table.id')),
#    db.Column('friend_id', db.Integer, db.ForeignKey('users.id')),
#    db.Column('role',db.Integer),
#    db.Column('timestamp',db.DateTime, index=True, default=datetime.now().strftime('%Y-%m-%d %H:%M'))
# )
class Class_User(db.Model):
    __tablename__ = 'classuser'
    id = db.Column('id', db.Integer, primary_key=True)
    class_id = db.Column('class_id', db.Integer, db.ForeignKey('class_table.id'))
    friend_id = db.Column('friend_id', db.Integer, db.ForeignKey('users.id'))
    role = db.Column('role', db.Integer)
    timestamp = db.Column('timestamp', db.DateTime, index=True, default=datetime.now().strftime('%Y-%m-%d %H:%M'))


class Friend_List(db.Model):
    __tablename__ = 'friend'
    id = db.Column('id', db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('users.id'))
    friend_id = db.Column('friend_id', db.Integer, db.ForeignKey('users.id'))
    status = db.Column('status', db.Integer)
    timestamp = db.Column('timestamp', db.DateTime, index=True, default=datetime.now().strftime('%Y-%m-%d %H:%M'))


# friend_list = db.Table('friend',
#    db.Column('id',db.Integer,primary_key=True),
#    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
#    db.Column('friend_id', db.Integer, db.ForeignKey('users.id')),
#    db.Column('status',db.Integer),
#    db.Column('timestamp',db.DateTime, index=True, default=datetime.now().strftime('%Y-%m-%d %H:%M'))
# )

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    mobile = db.Column(db.String(64), unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    createdTime = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    portrait = db.Column(db.String(128))
    default_cls = db.Column(db.Integer,default=0)
    
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    # comments = db.relationship('Comment', backref='author', lazy='dynamic')

    friendlist = db.relationship('Friend_List', foreign_keys=[Friend_List.user_id],
                                 backref=db.backref('befriend', lazy='joined'), lazy='dynamic',
                                 cascade='all,delete-orphan')  # order_by="post_up.columns['timestamp']"

    classlist = db.relationship('Class_User', foreign_keys=[Class_User.friend_id],
                                backref=db.backref('beuser', lazy='joined'), lazy='dynamic',
                                cascade='all,delete-orphan')  # order_by="post_up.columns['timestamp']"

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.portrait = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        db.session.commit()
        return True

    def gravatar(self, size=100, default='identicon', rating='g'):
        pass
        
    def change_portrait(self,new_portrait):
        self.portrait = new_portrait
        db.session.add(self)
        db.session.commit()
        return True
        
    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    def add_friend(self, user):
        if not self.is_friend(user):
            f = Friend_List(user_id=self.id, friend_id=user.id)
            db.session.add(f)

            f2 =  Friend_List(friend_id=self.id, user_id=user.id)
            db.session.add(f2)
            
            db.session.commit()
            return True
        else:
            return False


    def is_friend(self, user):
        return user.id in self.getallmyfriend()

    def getallmyfriend(self):
        groupfriend = []
        for c in self.classlist:
            cls = Class.query.filter_by(id=c.class_id).first()
            if cls is not None:
                for d in cls.classusers:
                    groupfriend.append(d.friend_id)

        for f in self.friendlist:
            groupfriend.append(f.friend_id)

        return groupfriend


    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    @staticmethod
    def from_json(data):
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        mobile = data.get('mobile')
        role = data.get("role")
        if role is None:
            role_id = Role.query.filter_by(name='User').first().id
        else:
            role_id = Role.query.filter_by(name=role).first().id

        avatar = data.get("avatar")
        if avatar is None:
            avatar = "https://avatars2.githubusercontent.com/u/1171281?v=3&s=460"
        return User(email=email, username=username, password=password, mobile=mobile, role_id=role_id, portrait=avatar)

    @staticmethod
    def from_form(form):
        email = form.get('email')
        username = form.get('username')
        password = form.get('password')
        mobile = form.get('mobile')
        name = form.get('name',default=username)
        role = form.get("role", default='User')
        if role is None:
            role_id = Role.query.filter_by(name='User').first().id
        else:
            role_id = Role.query.filter_by(name=role).first().id

        avatar = form.get("avatar", default='https://avatars2.githubusercontent.com/u/1171281?v=3&s=460')

        return User(email=email, username=username, password=password, mobile=mobile, role_id=role_id, portrait=avatar,name=name)

    def to_json(self):
        json_user = {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "name": self.name,
            "portrait": self.portrait,
            "default_cls":self.default_cls
        }
        return json_user

    def __repr__(self):
        return '<User %r>' % self.username


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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


class Class(db.Model):
    __tablename__ = 'class_table'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    portrait = db.Column(db.VARCHAR(128))
    introduce = db.Column(db.VARCHAR(256))
    number = db.Column(db.Integer, default=1)
    max_number = db.Column(db.Integer, default=100)
    create_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creat_datetime = db.Column(db.DateTime, default=datetime.now().strftime('%Y-%m-%d %H:%M'))
    # classusers = db.relationship('User', secondary=class_user,
    #    backref=db.backref('classes', lazy='dynamic'),order_by=class_user.c.timestamp)#order_by="post_up.columns['timestamp']"
    classusers = db.relationship('Class_User', foreign_keys=[Class_User.class_id],
                                 backref=db.backref('beclass', lazy='joined'), lazy='dynamic',
                                 cascade='all,delete-orphan')  # order_by="post_up.columns['timestamp']"

    def increase_number(self):
        self.number = self.number + 1
        db.session.add(self)
        db.session.commit()
        
        
    @staticmethod
    def from_json(json_data):
        name = json_data.get('name')
        portrait = json_data.get('portrait')
        # number = json_data.get('number')
        create_user_id = g.current_user.id
        creat_datetime = json_data.get('datetime')
        if creat_datetime is None:
            creat_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')
        introduce = json_data.get('introduce')
        return Class(name=name, portrait=portrait, create_user_id=create_user_id, creat_datetime=creat_datetime,
                     introduce=introduce)

    @staticmethod
    def from_form(form):
        name = form.get('name')
        portrait = form.get('portrait')
        # number = json_data.get('number')
        create_user_id = g.current_user.id
        creat_datetime = form.get('datetime', datetime.now().strftime('%Y-%m-%d %H:%M'))
        introduce = form.get('introduce')
        return Class(name=name, portrait=portrait, create_user_id=create_user_id, creat_datetime=creat_datetime,
                     introduce=introduce)

    def to_json(self):
        cls_json = {
            'id': self.id,
            'portrait': self.portrait,
            'name': self.name,
            'introduce': self.introduce,
            'number':self.number,
            'max_number':self.max_number
        }
        return cls_json

    def add_user(self,id):
        cls_usr = Class_User(friend_id=id, class_id=self.id)
        db.session.add(cls_usr)
        db.session.commit()


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
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    replyname = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        # json_comment = {
        #    'url': url_for('api.get_comment', id=self.id, _external=True),
        #    'post': url_for('api.get_post', id=self.post_id, _external=True),
        #    'body': self.body,
        #    'body_html': self.body_html,
        #    'timestamp': self.timestamp,
        #    'author': url_for('api.get_user', id=self.author_id,
        #                      _external=True),
        # }
        author = User.query.filter_by(id=self.author_id).first()
        if author is not None:
            reply_name = author.username
        replyname = User.query.filter_by(id = self.replyname).first()
        isreplyname = None
        if replyname is not None:
            isreplyname = replyname.username

        new_json_comment = {
            'replyId': self.id,
            'replyName': reply_name,
            'isReplyName': isreplyname,
            'comment': self.body
        }
        return new_json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('comment')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        author_id = g.current_user.id
        replyname = json_comment.get('isReplyName')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return Comment(body=body, author_id=author_id, replyname=replyname,timestamp= timestamp)


db.event.listen(Comment.body, 'set', Comment.on_changed_body)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    author_id = db.Column(db.Integer, db.ForeignKey(User.id))
    class_id = db.Column(db.Integer, db.ForeignKey(Class.id))
    imgs = db.relationship('PostImage', backref='imgpost', lazy='dynamic')

    ups = db.relationship('User', secondary=post_up,
                          backref=db.backref('post', lazy='dynamic'),
                          order_by=post_up.c.timestamp)  # order_by="post_up.columns['timestamp']"

    comments = db.relationship('Comment', backref='post', lazy='dynamic',
                               order_by=Comment.timestamp)  # ,order_by="comments.timestamp"

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        # json_post = {
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
        # }
        user = User.query.filter_by(id=self.author_id).first()
        if user is not None:
            new_json_post = {
                'id': self.id,
                'content': self.body,
                'uname': user.username,
                'sendtime': self.timestamp.strftime('%Y-%m-%d %H:%M'),
                'usericon': user.portrait,
                'urls': [
                    img.img_md5 for img in self.imgs
                    ],
                'friendcomment': [
                    c.to_json() for c in self.comments
                    ],
                'friendpraise': [
                    up.id for up in self.ups
                    ]
    
            }
            return new_json_post

    @staticmethod
    def from_json(json_post):
        body = json_post.get('content')
        timestamp = json_post.get('sendtime')
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        classid = json_post.get('class_id')
        author_id = g.current_user.id
        if body is None or body == '':
            raise ValidationError('post does not have a body')

        return Post(body=body, timestamp=timestamp, author_id=author_id,class_id=classid)


db.event.listen(Post.body, 'set', Post.on_changed_body)
