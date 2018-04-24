#encoding: utf-8
from flask import  render_template,redirect,request,url_for,flash,current_app,Response
from . import auth     # 导入蓝本
from flask_login import login_user,logout_user,login_required,current_user
from ..models import User
from .forms import LoginForm,RegistrationForm,ChangePasswordForm,PasswordResetRequestForm, PasswordResetForm
from .. import db
from ..email import send_email
from ..func import sms
from ..models import Comment,Post
from datetime import datetime
import json
import re,time


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()     #更新登陆用户的访问时间
        if not current_user.confirmed and request.endpoint and request.endpoint[:5] != 'auth.' and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))

ans = 0
# 写文章————TinyMCE编辑器上传本地图片到服务器
@auth.route('/pasteimg', methods=['GET', 'POST'])
def paste_upload():
    global ans
    if request.method == 'POST':
        imgdata = request.get_data()
        try:
            # 保存图片到服务器
            with open('app/static/article_img/'+str(ans)+'.jpg', 'wb') as fp:
                fp.write(imgdata)
            # 图片在服务器上的地址
            imgsrc = "/static/article_img/" + str(ans) + ".jpg"
            ans += 1
            time.sleep(2)
        except Exception,e:
            print 'error',e
    # 返回图片对象
    return Response(imgsrc, mimetype='application/text')

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

# 用户登录
@auth.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user,form.remember_me.data)
            return redirect(url_for('main.index'))
        elif User.query.filter_by(email=form.email.data).first() is None:
            flash("Email don't exist." )
        else:
            flash('Email or Password wrong.')
    return render_template('auth/login.html',form=form)

class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


# ajax加载文章内容
@auth.route("/article_data", methods=['POST', 'GET'])
def article_data():
    if request.method == 'GET':
        pid = request.args.get('pid')
        d = {}
        d['post'] = Post.query.filter_by(id=pid).first().body
        d['post_html'] = Post.query.filter_by(id=pid).first().body_html
    return json.dumps(d)

# ajax加载评论
@auth.route("/commits", methods=['POST', "GET"])
def commits():
    if request.method == 'GET':
        pid = request.args.get('pid')
        # 查出某篇文章的评论 ，按时间从新到旧排序
        commit = Comment.query.filter_by(post_id=pid).order_by(Comment.timestamp.desc()).all()
        # print str(Comment.query.filter_by(post_id=pid).order_by(Comment.timestamp.desc()))   # 打印原生SQL语句
        l = []
        for x in commit:
            d = {}
            d['id'] = x.id
            d['username'] = x.author.username
            d['gravatar'] = x.author.gravatar(size=40)
            d['timestamp'] = str(x.timestamp).split('.')[:-1][0]
            # 加8个小时换成北京时间
            d['timestamp'] = re.sub(' \d{2}', " " + str(int(d['timestamp'].split(':')[0].split(' ')[1]) + 8), d['timestamp'])
            d['body_html'] = x.body_html
            d['body'] = x.body
            l.append(d)
    return json.dumps(l,cls=CJsonEncoder)



# 发送手机短信验证码修改密码
@auth.route("/verification", methods=['POST', 'GET'])
def verification():
    error_msg = None
    if request.method == 'GET':
        # 获取 GET 请求参数（获取AJAX请求发送过来的手机号）
        phone_number = request.args.get('mobile_phone_number')
        # 在数据库中查找符合此手机号的用户
        user = User.query.filter_by(phone=phone_number).first()
        if not user and phone_number != None:
            print u"此手机号暂未绑定任何账户！不发送验证码！"
            return json.dumps({"answer":0})         # 返回ajax消息提示前端页面验证码发送失败。发送json格式比较好，所以使用json.dumps()
            flash(u'Error!')   # 为什么在get请求里的flash在网页上不显示？？？  答：是AJAX请求，不刷新整个页面。
        else:
            print u'当前请求号码：',phone_number
            if phone_number is not None:
                if sms.send_message(phone_number):
                    return json.dumps({"answer":1})    # 返回ajax消息提示前端页面验证码发送成功。发送json格式比较好，所以使用json.dumps()
                    flash(u"Succeed to get the verification code!")
                else:
                    flash(u"Failed to get the verification code!")
    elif request.method == 'POST':
        phone_number = request.form['phone']
        code = request.form['code']
        print phone_number,code
        if phone_number == '':
            # print "heree2"
            error_msg = u'请输入手机号！'
        elif code == '':
            # print "heree1"
            error_msg = u'请输入验证码！'
        elif sms.verify(phone_number, code):
            print u"验证通过，跳转到重置密码页面。"
            user = User.query.filter_by(phone=phone_number).first()
            token = user.generate_reset_token()  # 生成一个随机字符串，携带发送
            print u"新生成的 token 是:",token
            return redirect('http://127.0.0.1:5000/auth/reset/'+token)      # 重定向到指定的重置密码地址，如果以后部署，这个地方的地址也要更改。
        else:
            flash(u'验证码不匹配')
            print  u'验证码有误，请重新验证！'
            error_msg = u'验证码有误，请重新验证！'
    return render_template('auth/reset_password_use_phone.html',error_msg=error_msg)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

# 注册
@auth.route('/register',methods=['GET','POST'])
def register():
    form = RegistrationForm()
    # 1、验证输入是否符合要求
    # 2、检查手机号是否已经被占用
    if User.query.filter_by(phone=form.phone.data).first():    #如果根据手机号能查询到某用户，则手机号被占用。
        flash(u'该手机号已被注册')
    else:
        if form.validate_on_submit():
            print form.password.data
            user = User(email=form.email.data,username=form.username.data,phone=form.phone.data,password=form.password.data)
            db.session.add(user)
            db.session.commit()  #令牌需要用到id，因此不能延后提交，在此直接提交分配给用户id
            token = user.generate_confirmation_token()
            send_email(user.email,'Confirm Your Account','auth/email/confirm',user=user,token=token)
            flash(u'验证码已发送到你的邮箱，请查收！')
            if current_app.config['FLASKY_ADMIN']:
                 send_email(current_app.config['FLASKY_ADMIN'], 'New User', 'mail/new_user', user=user)
            return redirect(url_for('auth.login'))
    return render_template('auth/register.html',form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account,Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    print current_user.email
    send_email(current_user.email, 'Confirm Your Account','auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))

@auth.route('/change_password',methods=['GET','POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('Your password has been updated.')
            return  redirect(url_for('main.index'))
        else:
            flash('Invalid password.')
    return render_template('auth/change_password.html', form=form)

@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    # 判断当前用户是否是匿名用户
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        # 查找邮箱用户
        user = User.query.filter_by(email=form.email.data).first()
        if user: # 存在该用户，发送重置密码邮件
            token = user.generate_reset_token()   #生成一个随机字符串，携带发送
            send_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
            flash(u'一封重置密码的邮件已发送到你的邮箱，请查收。')
            return redirect(url_for('auth.login'))
        else: # 不存在改用户，pass
            flash(u'系统无此邮箱地址')
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))

        # 验证码输入正确，通过验证，根据手机号查找到user，根据user生成token,验证token,通过token验证才会允许更新密码。(同时杜绝了恶意用户用自己的手机改别人的密码。)
        if user.reset_password(token, form.password.data):
            flash(u'密码已更新')
            return redirect(url_for('auth.login'))
        else:
            # 向私自构造URL的人给出警告！
            flash(u'错误！你没有该权限')
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)