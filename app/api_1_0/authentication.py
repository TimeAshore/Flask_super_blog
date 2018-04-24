# encoding: utf-8
# Author: Timeashore
# Time: 2018-4-22
# Email: 1274866364@qq.com
from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth
from ..models import User
from . import api
from .errors import unauthorized, forbidden

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):
    '''通过验证方式'''
    # 匿名禁止访问
    if email_or_token == '':
        return False
    # 令牌验证访问
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    # 普通用户验证邮箱、密码
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    '''每次发请求前都检查，禁止匿名用户、未验证用户访问'''
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('No login account')


@api.route('/tokens/', methods=['POST'])
def get_token():
    '''生成token令牌，禁止匿名用户和旧令牌获取新令牌'''
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(expiration=3600), 'expiration': 3600})