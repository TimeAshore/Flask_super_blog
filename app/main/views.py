#encoding: utf-8
from flask import render_template,flash,abort,make_response,current_app,Response
from .. import db
from ..models import User,Role,Post,Permission,Comment,Confess
from ..email import send_email
from . import main          # 导入蓝本
from .forms import EditProfileForm,EditProfileAdminForm,PostForm,CommentForm,Send_Email_To_Admin,Confession
from flask_login import login_required,current_user
from ..decorators import admin_required,permission_required    # 自定义装饰器，用于检查指定权限
import os
from config import ALLOWED_EXTENSIONS
from flask import request, redirect, url_for
from werkzeug import secure_filename
from flask import send_from_directory
import requests,re
import time,hashlib,random,json
from flask_sqlalchemy import get_debug_queries

# 检测数据库性能，超过阀值打印警告信息
@main.after_app_request
def after_request(response):
    # get_debug_queries()函数返回一个列表，元素是请求中执行的查询
    for query in get_debug_queries():
        if query.duration:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %f\nContext: %s\n'
                % (query.statement,query.parameters,query.duration,query.context)
            )
    return response

# 首页
@main.route('/', methods=['GET', 'POST'])
def index():
    # 写文章的位置搬迁啦
    # form = PostForm()
    # if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
    #     post = Post(body=form.body.data,author=current_user._get_current_object())
    #     db.session.add(post)
    #     return redirect(url_for('.index'))

    # posts = Post.query.order_by(Post.timestamp.desc()).all()    # 当前所有用户提交的所有文章

    # 添加分页导航
    page = request.args.get('page', 1, type=int)
    # pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out = False)

    show_followed = False
    # 用户是否登陆
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    # 返回已关注用户的文章
    if show_followed:
        query = current_user.followed_posts    # followed_posts是User模型用@property定义的一个属性，调用无需加括号
    # 返回所有文章
    else:
        query = Post.query
    # 分页
    pagination = query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts = pagination.items
    return render_template('index.html', posts=posts,show_followed=show_followed,pagination=pagination)

# 写文章，使用TinyMCE文章编辑器，具体允许实用的标签和属性在model模型中设置。
@main.route('/make',methods=['GET', 'POST'])
@login_required
def make():
    if current_user.can(Permission.WRITE_ARTICLES) and request.method == 'POST':
        if request.form['content'] != '':
            # print 'sdf',request.form['content']
            post = Post(body=request.form['content'], author=current_user._get_current_object())
            db.session.add(post)
            flash(u"新文章发布成功")
        else:
            flash(u'文章没有内容，发布失败')
        return redirect(url_for('.index'))
    return render_template('editor.html')


# 限制上传格式
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

# 上传
@main.route('/homepage_2',methods=['GET','Post'])
@login_required
def homepage_2():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            flash(u'上传成功！')
            # 图片在线预览
            if filename.split('.')[-1] in ['png', 'jpg', 'jpeg', 'gif']:
                return redirect(url_for('main.uploaded_file',filename=filename))
    return render_template('homepage_2.html')


# 下载文件
@main.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    # 在设置好的目录下找到相应文件
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],filename)


# 个人资料页面
@main.route('/user/<username>')
@login_required
def user(username):
    # 先找到用户名为username的User模型
    user = User.query.filter_by(username=username).first_or_404()
    # 添加分页导航
    page = request.args.get('page', 1, type=int)
    # 通过这个用户的模型查找所有的文章posts
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    # posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user,posts=posts,pagination=pagination)

@main.route('/edit_profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.username = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)    #添加到数据库
        flash('Your profile has been updated.')
        return redirect(url_for('.user',username=current_user.username))
    #默认填充的值
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    # username = current_user.name
    return render_template('edit_profile.html',form=form)


@main.route('/edit_profile_admin/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user',username=user.username))
    form.email.data = user.email
    # form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return  render_template('edit_profile.html',form=form,user=user)



#查看文章/添加评论
@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    # 根据主键id查找，如果没有返回404错误
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,post=post,author=current_user._get_current_object())
        db.session.add(comment)
        flash(u'评论成功')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    # comments = pagination.items
    return render_template('posts.html', author=post.author, posts=[post], form=form, pagination=pagination)


#编辑文章
@main.route('/edit/<int:id>',methods=['GET','POST'])
@login_required
def edit(id):
    '''编辑文章，没实现把内容传到TineyMCE里，还使用的是markdown编辑，所以原来body里的img等标签就没有了'''
    # SQLAlchemy数据库中做数据的修改操作
    # 1. 修改数据库中文章的内容，需要先个根据文章id查找到这篇文章
    # 2. 把这条数据，需要修改的地方进行修改
    # 3. 做事务的提交

    # 1.查找到文章
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        # 2.对需要修改的地方进行修改
        post.body = form.body.data
        # 3.做事务的提交
        db.session.add(post)
        flash(u'文章已更新')
        return redirect(url_for('.post',id=post.id))
    # 因为从数据库中拿出来的是带有html的标签文本，这里需要去html，只留下文本传递给编辑文章页面。
    temp = re.sub(r'<[^>]+>','\n',post.body)
    temp = re.sub(r'&nbsp','',temp)
    temp = re.sub(r';','',temp)
    form.body.data = temp.strip('\n')
    return render_template('edit_post.html',form=form)


#删除评论
@main.route('/comment_delete',methods=['GET','POST'])
@login_required
def comment_delete():
    # http://127.0.0.1:5000/comment_delete?id=x&pid=y
    id = request.args['id']
    pid = request.args['pid']
    if True:
        # 在_comments.html中按照角色显示删除按钮，下方验证不合法构造删除url
        post = Post.query.get_or_404(pid)
        comment = Comment.query.get_or_404(id)
        # 不是评论者、不是文章作者、不是管理员，则拒绝删除
        if current_user != comment.author and current_user != post.author and not current_user.can(Permission.ADMINISTER) :
            print u"没有权限删除！"
            return '<p>请求不合法,不具备删除权限</p>'
        # SQLAlchemy数据库中做数据的删除操作
        # 1. 需要先个根据id查找到这条评论
        # 2. 把这条数据删除
        # 3. 做事务的提交

        # 根据评论的id号查找到一条评论并删除，提交数据库
        # id是评论id，pid是当前文章id
        db.session.delete(Comment.query.filter_by(id=id).first())
        db.session.commit()
        flash(u'评论已删除')
        # 重定向到当前文章
        return redirect(url_for('.post', id=pid))
    else:
        return "comment_delete/<int:id>有异常"


#删除文章
@main.route('/delete/<int:id>',methods=['GET','POST'])
@login_required
def delete(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    db.session.delete(Post.query.filter_by(id=id).first())
    db.session.commit()
    flash(u'文章删除成功')
    return redirect(url_for('.index'))


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


#粉丝
@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title=u"的粉丝",endpoint='.followers', pagination=pagination,
                           follows=follows)

#已关注的人
@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title=u"关注的人",endpoint='.followed_by', pagination=pagination,
                           follows=follows)


# 设置cookie，显示所有文章set_cookie=""
@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)   # max_age是cookie有效期
    return resp

# 设置cookie，仅仅显示已关注用户的文章set_cookie="1"
@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)  # max_age是cookie有效期
    return resp

# 联系管理员
@main.route('/send_email_to_admin',methods=['GET','POST'])
@login_required
def send_email_to_admin():
    form = Send_Email_To_Admin()
    if form.validate_on_submit():
        # 收件人，标题，引用的模板文件位置，需要传递的参数（注：参数是在模版文件.html和.txt中使用的，可有可无）。
        send_email(current_app.config['FLASKY_ADMIN'], 'Send_to_admin', 'mail/send_to_admin', email=current_user.email,username=current_user.username,content=form.content.data)
        flash('Send succeed.')
        #重定向到发送邮件的页面，这样就消除了原来文本框里的内容，form还是要传进去的，因为要渲染表单
        return redirect(url_for('.send_email_to_admin',form=form))
    return render_template('send_email_to_admin.html',form=form)


# 告白墙
@main.route('/confession',methods=['GET','POST'])
@login_required
def confession():
    form = Confession()
    # 添加分页
    page = request.args.get('page', 1, type=int)
    pagination = Confess.query.order_by(Confess.time.desc()).paginate(page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    confessions = pagination.items
    # if request.method == 'POST' and current_user.is_authenticated():
    # current_user.is_authenticated() 在html文件中用。判断用户是否登陆，是返回True,否则返回False
    # request.method 是当前请求方式
    if form.validate_on_submit():
        fess = Confess(content=form.confession.data,author=current_user._get_current_object())
        # fess.content = form.confession.data
        db.session.add(fess)
        return redirect(url_for('.confession',form=form,pagination=pagination,confessions=confessions))
    return render_template('confession.html',form=form,confessions=confessions,pagination=pagination)

# 管理员删除告白墙信息
@main.route('/confession_delete/<int:id>',methods=['GET','POST'])
@login_required
def confession_delete(id):
    if True:
        # 根据评论的id号查找到一条评论并删除，提交数据库
        db.session.delete(Confess.query.filter_by(id=id).first())
        db.session.commit()
        flash(u'一条告白已被删除')
        return redirect(url_for('.confession'))
    else:
        return "confession_delete/<int:id>有异常"

# 搜索告白墙信息
@main.route('/search_confession',methods=['GET','POST'])
@login_required
def search_confession():
    form = Confession()
    search = request.form['search']
    q_str = u'%{}%'.format(search)
    # 在数据库中查找符合条件的告白信息。
    fess = Confess.query.filter(Confess.content.like(q_str)).order_by(Confess.time.desc()).all()
    return render_template('confession.html', form=form, confessions=fess)

# 搜索文章
@main.route('/search_article',methods=['GET','POST'])
def search_article():
    search = request.form['search']
    q_str = u'%{}%'.format(search)
    posts = Post.query.filter(Post.body_html.like(q_str)).order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)




# 在线翻译助手
@main.route('/translate',methods=['GET','POST'])
def translate():
    if request.method == 'POST':
        try:
            content = request.form['input_content']
            timestamp = int(time.time() * 1000 + random.randint(0, 10))

            ss = "fanyideskweb"
            o = content
            a = str(timestamp)
            t = "rY0D^0'nM0}g5Mm1z%1G4"
            salt = hashlib.md5((ss + o + a + t).encode('utf-8')).hexdigest()

            headr = {
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "zh-CN,zh;q=0.8",
                "Connection": "keep-alive",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Cookie": "OUTFOX_SEARCH_USER_ID=265267138@10.169.0.76; _ntes_nnid=9032b6b2118151f7f5785ab024282450,1502937415678; OUTFOX_SEARCH_USER_ID_NCOO=1638353389.154072; JSESSIONID=aaahPkkH_mlU45qa55t8v; DICT_UGC=be3af0da19b5c5e6aa4e17bd8d90b28a|; JSESSIONID=abcATkvSOol-GgDUoGy8v; ___rl__test__cookies=1507951060507",
                "Host": "fanyi.youdao.com",
                "Origin": "http://fanyi.youdao.com",
                "Referer": "http://fanyi.youdao.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest"
            }
            data = {
                "i": content,
                "from": "AUTO",
                "to": "AUTO",
                "smartresult": "dict",
                "client": "fanyideskweb",
                "salt": timestamp,
                "sign": salt,
                "doctype": "json",
                "version": "2.1",
                "keyfrom": "fanyi.web",
                "action": "FY_BY_REALTIME",
                "typoResult": "true"
            }

            result = requests.post('http://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule', data=data,headers=headr)
            result_dict = json.loads(result.text.encode('utf-8'))
            r = ""
            for x in range(len(result_dict['translateResult'])):
                for y in range(len(result_dict['translateResult'][x])):
                    if result_dict['translateResult'][x][y]['tgt'] == "":
                        result_dict['translateResult'][x][y]['tgt'] = '\n'
                    r = r + result_dict['translateResult'][x][y]['tgt'] + '\n'
            return json.dumps({"answer":r})
        except Exception,e:
            print e
            # 如果用户输入的内容不符合要求，翻译不出来，抛出500异常。比如用户输入图片
            abort(500)
    return render_template('translate.html')



# 管理用户
@main.route('/management_users', methods=['GET', 'POST'])
@login_required
def management_users():
    if current_user.is_administrator():     # 要求是管理员，否则禁止访问，并记录IP。
        users = User.query.all()
        page = request.args.get('page', 1, type=int)
        pagination = User.query.paginate(page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],error_out=False)
    else:
        flash(u'没有访问权限，已记录你的IP')
        return redirect(url_for('.index'))
    return render_template('management_users.html',users=users,endpoint='.management_users', pagination=pagination)


# 管理用户---删除用户（同时删除此用户发布的所有文章以及告白墙）
@main.route('/delete_user/<int:id>',methods=['GET', 'POST'])
@login_required
def delete_user(id):
    try:
        if current_user.is_administrator():     # 要求是管理员，否则禁止访问，并记录IP。
            user = User.query.filter_by(id=id).first()
            username = user.username
            # 删除他的所有文章
            posts = Post.query.filter_by(author_id=user.id).all()
            # print u"该用户提交的文章数目：",len(posts)
            for post in posts:
                db.session.delete(post)
            # 删除他的所有告白
            confess = Confess.query.filter_by(author_id=user.id).all()
            for con in confess:
                db.session.delete(con)
            db.session.delete(user)
            db.session.commit()
            flash(u'用户{}已删除'.format(username))
        else:
            flash(u'没有访问权限，已记录你的IP')
            return redirect(url_for('.index'))
    except:
        pass
    return redirect(url_for('.management_users'))


# 管理用户---冻结用户
@main.route('/freeze_user/<int:id>',methods=['GET', 'POST'])
@login_required
def freeze_user(id):
    try:
        if current_user.is_administrator():     # 要求是管理员，否则禁止访问，并记录IP。
            user = User.query.filter_by(id=id).first()
            user.confirmed = False
            db.session.commit()
            flash(u'用户{}已冻结'.format(user.username))
        else:
            flash(u'没有访问权限，已记录你的IP')
            return redirect(url_for('.index'))
    except:
        pass
    return redirect(url_for('.management_users'))


# 管理用户---激活用户
@main.route('/activation_user/<int:id>',methods=['GET', 'POST'])
@login_required
def activation_user(id):
    try:
        if current_user.is_administrator():     # 要求是管理员，否则禁止访问，并记录IP。
            user = User.query.filter_by(id=id).first()
            user.confirmed = True
            db.session.commit()
            flash(u'用户{}已激活'.format(user.username))
        else:
            flash(u'没有访问权限，已记录你的IP')
            return redirect(url_for('.index'))
    except:
        pass
    return redirect(url_for('.management_users'))


# 管理用户---搜索用户
@main.route('/search',methods=['GET', 'POST'])
@login_required
def search():
    search_content = request.form['search']
    # 模糊匹配，显示所有包含搜索内容的用户
    q_str = u'%{}%'.format(search_content)
    user = User.query.filter(User.username.like(q_str))
    return render_template('management_users.html',users=user)
