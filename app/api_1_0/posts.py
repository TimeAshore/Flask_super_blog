# encoding: utf-8
# Author: Timeashore
# Time: 2018-4-22
# Email: 1274866364@qq.com
from flask import jsonify, request, g, url_for, current_app
from .. import db
from ..models import Post, Permission, Comment
from . import api
from .decorators import permission_required
from .errors import forbidden


@api.route('/posts/', methods=['GET'])
def get_posts():
    # page是本次请求的页数，默认是第一页
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts = pagination.items
    prev = None
    # 判断上一页
    if pagination.has_prev:
        prev = url_for('api.get_posts', page=page-1, _external=True)
    next = None
    # 下一页
    if pagination.has_next:
        next = url_for('api.get_posts', page=page+1, _external=True)

    # 其实post.to_json()函数返回的是一个dict类型，经过jsonify()函数才成为一个Json响应
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev page': prev,
        'next page': next,
        'count': pagination.total
    })


@api.route('/posts/<int:id>', methods=['GET'])
def get_post(id):
    post = Post.query.get_or_404(id)   # 找得到返回文章对象并返回Json响应，找不到抛出404异常
    return jsonify(post.to_json())


@api.route('/posts/<int:id>/comments/', methods=['GET'])
def get_post_comments(id):
    '''某文章下所有评论，文章下可能有很多评论，所以需要分页'''
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_post_comments', id=id, page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_post_comments', id=id, page=page+1, _external=True)
    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


# eee,这个POST如何使用。。。？？？
@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post():
    '''使用API提交一篇文章。请求中提交的Json数据在request.json中包含。'''
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()), 201, {'Location': url_for('api.get_post', id=post.id)}


@api.route('/posts/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(id):
    post = Post.query.get_or_404(id)
    # 不是文章作者 ,不是管理员，就没有权限修改文章
    if g.current_user != post.author and not g.current_user.can(Permission.ADMINISTER):
        return forbidden('Not permissions')
    # 跟新文章body，（body_html注册在了body属性上，会随body改变），提交数据库
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json())