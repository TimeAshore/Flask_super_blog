#encoding: utf-8
from . import db
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,AnonymousUserMixin
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app,request
from datetime import datetime
import hashlib
from markdown import markdown
import bleach

#权限类型
class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80

#关注关联表模型
class Follow(db.Model):
    __tablename__ = 'follows'
    #用户本身id
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),primary_key=True)
    #用户已关注id
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),primary_key=True)
    #关注时间
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#用户对应角色
class Role(UserMixin,db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)

    # 一对多
    users = db.relationship('User', backref='role', lazy='dynamic')

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

#用户资料
class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64),unique=True,index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    phone = db.Column(db.String(15),unique=True, index=True ) # 绑定的手机号
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id')) # 一对多，“此为多的一方”
    password_hash = db.Column(db.String(128))   #创建一列用来存储密码的散列值
    confirmed = db.Column(db.Boolean,default=False)   #保存每个注册账户状态，默认False是尚未用过验证
    #用户资料页面内容
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(),default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(),default=datetime.utcnow)

    #头像哈希值
    avatar_hash = db.Column(db.String(32))

    #用户提交的文章
    posts = db.relationship('Post',backref='author',lazy='dynamic')

    # fjsdkl lksdjlkjfsldkjflk !!!!!!!!!!!!!!!!!!!
    confessions = db.relationship('Confess',backref='author',lazy='dynamic')

    # 用户提交的告白墙
    # confessions = db.relationship('Confess', backref='username', lazy='dynamic')

    #已关注
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    #关注者
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        # 设置关注自己
        self.followed.append(Follow(followed=self))



    #刷新用户最后访问时间
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)


    def generate_confirmation_token(self,expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'confirm':self.id})

    def confirm(self,token):
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

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

    # 重置密码前先验证了token,防止非法私自构造连接修改密码！
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
       #更新email地址
        self.email = new_email
        #email更新后更新eamil的哈希值
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True
    #用户头像
    def gravatar(self,size=100,default='identicon',rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url, hash=hash, size=size, default=default, rating=rating)

    #关注
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    #取消关注
    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    #判断是否已关注
    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    #判断是否被关注
    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py
        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


    # 获取所关注用户的文章
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == self.id)

    # 添加一个方法，设置所有用户可以关注自己
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()


    # 忘记密码
    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})
    # 同上
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
        return True

    def __repr__(self):
        return '<User %r>' % self.username

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

#文章
class Post(db.Model):
    __tablename__='posts'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow())
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    body_html = db.Column(db.Text)

    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
        p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),timestamp=forgery_py.date.date(True),author=u)
        db.session.add(p)
        db.session.commit()

    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        # 允许的html标签，插入图片需添加img标签
        allowed_tags = ['a','abbr','acronym','b','blockquote','code','em','i','li','ol','pre','strong','ul','h1','h2',\
                        'h3','p','br','img']
        attrs = {
            '*': ['class'],
            'a': ['href', 'rel'],
            'img': ['src', 'alt'],
        }
        target.body_html = bleach.linkify(bleach.clean(markdown(value,output_format='html'),tags=allowed_tags,attributes=attrs,strip=True))
db.event.listen(Post.body,'set',Post.on_changed_body)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        # 允许在markdown中使用的标签，（解决写文章不换行问题，敲两下空格+回车）
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i','strong','br']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))
db.event.listen(Comment.body, 'set', Comment.on_changed_body)



# 告白墙
class Confess(db.Model):
    __tablename__ = 'confess'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    content = db.Column(db.Text())
    time = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<confess %r>' % self.name