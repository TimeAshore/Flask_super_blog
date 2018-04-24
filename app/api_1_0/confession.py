# encoding: utf-8
# Author: Timeashore
# Time: 2018-4-23
# Email: 1274866364@qq.com
from . import api
from flask import request,jsonify,g,current_app,url_for
from ..models import Confess

@api.route('/confessions/', methods=['GET'])
def get_confessions():
    '''所有告白'''
    # page是当前请求页码，默认第一页
    page = request.args.get('page', 1, type=int)
    pagination = Confess.query.order_by(Confess.time.desc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    confessions = pagination.items
    prev = None
    # 上一页
    if pagination.has_prev:
        prev = url_for('api.get_confessions', page=page-1, _external=True)
    next = None
    # 下一页
    if pagination.has_next:
        next = url_for('api.get_confessions', page=page+1, _external=True)

    # 其实to_json()返回一个dict,jsonify()返回一个Json响应
    return jsonify({
        'confessions': [confess.to_json() for confess in confessions],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })

@api.route('/confessions/<int:id>', methods=['GET'])
def getconfession(id):
    confess = Confess.query.get_or_404(id)
    return jsonify(confess.to_json())