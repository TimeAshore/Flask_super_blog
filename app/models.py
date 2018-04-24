#encoding: utf-8
from . import db
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,AnonymousUserMixin
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app,request,url_for
from app.exceptions import ValidationError
from datetime import datetime
import hashlib
from markdown import markdown
import bleach       # 清理HTML

#权限类型
class Permission:
    '''一个用户可拥有以下多个权限'''
    FOLLOW = 0x01                       # 十进制1
    COMMENT = 0x02                      # 十进制2
    WRITE_ARTICLES = 0x04               # 十进制4
    MODERATE_COMMENTS = 0x08            # 十进制8
    ADMINISTER = 0x80                   # 十进制128

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
    default = db.Column(db.Boolean, default=False, index=True)          # 普通用户默认True,管理员为False
    permissions = db.Column(db.Integer)

    # 一对多
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        '''在数据库中创建角色'''
        roles = {
            # 对‘User’拥有的权限进行‘或’操作，结果是：7
            'User': (Permission.FOLLOW|Permission.COMMENT|Permission.WRITE_ARTICLES, True),
            # 对‘Moderator’拥有的权限进行‘或’操作，结果是：15
            'Moderator': (Permission.FOLLOW|Permission.COMMENT|Permission.WRITE_ARTICLES|Permission.MODERATE_COMMENTS, False),
            # Administrator直接设置权限为：255
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

    # 告白墙
    confessions = db.relationship('Confess',backref='author',lazy='dynamic')

    # 评论
    comments = db.relationship('Comment', backref='author', lazy='dynamic')


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



    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            # 初始化用户头像的散列值，存到avatar_hash属性中。 注：散列值通过用户email生成，不会改变，除非用户eamil改变。
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        # 设置关注自己
        self.followed.append(Follow(followed=self))



    #刷新用户最后访问时间
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def can(self, permissions):
        # print self.role.permissions,permissions,self.role.permissions&permissions
        # 拿当前用户的权限和写文章的权限进行'&'运算，例如普通用户是 7&4  = 4，具有写文章权限。
        # （补充：‘&’，同位是1为1，否则为0）
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        # 管理员权限，User.role.permissions=255,Permission.ADMINSTER=128，255&128  =128，刚刚好！
        return self.can(Permission.ADMINISTER)


    def generate_confirmation_token(self,expiration=3600):
        '''用户验证，生成确认令牌'''
        s = Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'confirm':self.id})

    def confirm(self,token):
        '''用户验证，核对确认令牌'''
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
        '''改变邮箱地址，该功能已在前端页面禁用！'''
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
        #email更新后更新由eamil的生成的头像散列值
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

    # 产生虚拟数据
    # @staticmethod
    # def generate_fake(count=100):
    #     from sqlalchemy.exc import IntegrityError
    #     from random import seed
    #     import forgery_py
    #     seed()
    #     for i in range(count):
    #         u = User(email=forgery_py.internet.email_address(),
    #                  username=forgery_py.internet.user_name(True),
    #                  password=forgery_py.lorem_ipsum.word(),
    #                  confirmed=True,
    #                  name=forgery_py.name.full_name(),
    #                  location=forgery_py.address.city(),
    #                  about_me=forgery_py.lorem_ipsum.sentence(),
    #                  member_since=forgery_py.date.date(True))
    #     db.session.add(u)
    #     try:
    #         db.session.commit()
    #     except IntegrityError:
    #         db.session.rollback()


    # 获取所关注用户的文章、

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

    def generate_auth_token(self, expiration):
        '''rest web api。使用令牌验证，生成token'''
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id':self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        '''rest web api。验证token'''
        s = Serializer(current_app.config['SECURE_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def to_json(self):
        '''
            API返回用户，返回一个dict类型
            posts_url  ： 用户文章列表
            avatar_url  ： 用户头像
            comments_url  ： 用户评论列表
            post_count ： 用户发表文章数量
            followed_posts_url ：用户关注的文章列表（关注的用户的文章）地址
        '''
        json_user = {
            'url':url_for('api.get_user', id=self.id, _external=True),
            'avatar_url':"http://www.gravatar.com/avatar/"+self.avatar_hash+"?s=512&d=identicon",
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts_url': url_for('api.get_user_posts', id=self.id, _external=True),
            'comments_url': url_for('api.get_user_comments', id=self.id, _external=True),
            'confessions_url': url_for('api.get_user_confessions', id=self.id, _external=True),
            'followed_articles': url_for('api.get_user_followed_posts',id=self.id, _external=True),
            'post_count': self.posts.count()
        }
        return json_user

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
    # body里存放文章文本内容，body_html存放用文本的html形式（经过bleach,linkify清理），
    # 但加了TinyMCE后，body直接存放了html标签，貌似有点不安全。。。body_html存放清理过的body。。。
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    body_html = db.Column(db.Text)

    # lazy='dynamic'禁止自动执行查询，这样可以在查询中间添加过滤器。
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    def to_json(self):
        '''api,返回某post的详细信息'''
        json_post = {
            'url': url_for('api.get_post', id=self.id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id, _external=True),
            'comments_url': url_for('api.get_post_comments', id=self.id, _external=True),
            'comment_count': self.comments.count()
        }
        return json_post
    @staticmethod
    def from_json(json_post):
        '''通过API提交一篇文章，返回封装好的文章对象（只封装了body字段）'''
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)

    @staticmethod
    def generate_fake(count=100):
        '''用于生成虚拟文章'''
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
                        'h3','p','br','img','&nbsp','span','table','tbody','tr','td','style']
        attrs = {
            # 设置允许使用的HTML标签及对应属性
            # 标签：属性列表
            '*': allowed_tags,
            'a':['href'],
            'img': ['src', 'alt','align','width','margin','text-align'],
        }
        # 设置允许使用的CSS属性，还有问题的话去看bleach官方文档。
        sty = ['text-align','src','alt','href','color','background','background-image','background-repeat','background-attachment','text-indent','text-transform','text-decoration','white-space','line-height','font-family','font-style','font-weight','font-size','font-variant','list-style-type','border-collapse','border','width','height','text-align','vertical-align','padding','background-color','outline']
        # clean()用来清理标签，linkify()用来把文本中URL转换为<a>链接。
        target.body_html = bleach.linkify(bleach.clean(markdown(value,output_format='html'),tags=allowed_tags,attributes=attrs,styles=sty,strip=True))
db.event.listen(Post.body,'set',Post.on_changed_body) # 注册到body属性上，知道body变了就执行on_changed_body方法，修改body_html

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)   #disabled属性是用来给Moderator管理评论用的，某条评论的disables为True则显示，反之。已弃用Moderator权限，加入了Administartor删除评论功能。
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    def to_json(self):
        '''
            API返回评论
            post_url  ： 所属文章
            url ：       某评论
            author_url ：评论者信息
            
            _external = True，返回绝对地址
        '''
        json_comment = {
            'url': url_for('api.get_comment', id=self.id, _external=True),
            'post_url': url_for('api.get_post', id=self.post_id, _external=True),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id, _external=True),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        '''通过API提交一条评论，返回封装好的评论对象（只封装了body字段）'''
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        # 允许在markdown中使用的标签，（解决写文章不换行问题，敲两下空格+回车）
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i','strong','br','h']
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

    def to_json(self):
        '''一条告白的内容'''
        json_comment = {
            'content': self.content,
            'time': self.time,
            'author_url': url_for('api.get_user', id=self.author_id, _external=True),
            'confess_url': url_for('api.getconfession', id=self.id, _external=True),
        }
        return json_comment



    def __repr__(self):
        return '<confess %r>' % self.name