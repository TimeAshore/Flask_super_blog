# encoding: utf-8
# Author: Timeashore
# Time: 2018-4-22
# Email: 1274866364@qq.com
from flask import jsonify, request, g, url_for, current_app
from .. import db
from ..models import Post, Permission, Comment
from . import api
from .decorators import permission_required


@api.route('/comments/', methods=['GET'])
def get_comments():
    '''所有文章的所有评论，即数据库中所有评论'''
    # page是当前请求页码，默认第一页
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    comments = pagination.items
    prev = None
    # 上一页
    if pagination.has_prev:
        prev = url_for('api.get_comments', page=page-1, _external=True)
    next = None
    # 下一页
    if pagination.has_next:
        next = url_for('api.get_comments', page=page+1, _external=True)

    # 其实to_json()返回一个dict,jsonify()返回一个Json响应
    return jsonify({
        'comments': [comment.to_json() for comment in comments],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/comments/<int:id>', methods=['GET'])
def get_comment(id):
    '''返回某一条评论详细信息'''
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())


@api.route('/posts/<int:id>/comments/', methods=['POST'])
@permission_required(Permission.COMMENT)
def new_post_comment(id):
    '''通过API提交一条评论'''
    # 使用API提交一条评论。请求中提交的Json数据在request.json中包含。
    post = Post.query.get_or_404(id)
    comment = Comment.from_json(request.json)
    comment.author = g.current_user
    comment.post = post
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_json()), 201, {'Location': url_for('api.get_comment', id=comment.id)}