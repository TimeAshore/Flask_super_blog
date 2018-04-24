# encoding: utf-8
# Author: Timeashore
# Time: 2018-4-22
# Email: 1274866364@qq.com
'''REST WEB API'''
from flask import Blueprint

api = Blueprint('api', __name__)

from . import authentication, posts, users, errors, comments, confession

