# encoding: utf-8
# Author: Timeashore
# Time: 2018-4-22
# Email: 1274866364@qq.com
from flask import jsonify, request, current_app, url_for
from . import api
from ..models import User, Post, Comment, Confess


@api.route('/users/<int:id>')
def get_user(id):
    '''一个用户的详细信息。
    包括用户名，资料地址，发布文章列表及数量，注册时间及最近登录时间，关注的用户的文章列表地址'''
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())      # 生成json响应


@api.route('/users/<int:id>/posts/')
def get_user_posts(id):
    '''一个用户发布的所有文章列表，文章数量，上一页链接，下一页链接'''
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_posts', id=id, page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_posts', id=id, page=page+1, _external=True)
    # 生成json响应
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })

@api.route('/users/<int:id>/comments/')
def get_user_comments(id):
    '''一个用户发布的所有评论，数量，上一页链接，下一页链接'''
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.comments.order_by(Comment.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    comments = pagination.items
    prev = None
    # 如果有上一页
    if pagination.has_prev:
        prev = url_for('api.get_user_comments', id=id, page=page-1, _external=True)
    next = None
    # 如果有下一页
    if pagination.has_next:
        next = url_for('api.get_user_comments', id=id, page=page+1, _external=True)
    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/users/<int:id>/followed_articles/')
def get_user_followed_posts(id):
    '''一个用户关注的所有文章列表，关注文章数量，上一页链接，下一页链接'''
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_posts.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_followed_posts', id=id, page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_followed_posts', id=id, page=page+1, _external=True)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })

@api.route('/users/<int:id>/confessions/', methods=['GET'])
def get_user_confessions(id):
    '''一个用户的所有告白'''
    # 先根据用户id查找到该用户
    user = User.query.get_or_404(id)
    # 请求页码
    page = request.args.get('page', 1, type=int)
    pagination = user.confessions.order_by(Confess.time.asc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    # 该用户所有告白
    confessions = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_post_comments', id=id, page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_post_comments', id=id, page=page+1, _external=True)
    return jsonify({
        'comments': [confession.to_json() for confession in confessions],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })