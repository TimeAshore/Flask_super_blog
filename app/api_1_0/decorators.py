# encoding: utf-8
# Author: Timeashore
# Time: 2018-4-22
# Email: 1274866364@qq.com
from functools import wraps
from flask import g
from .errors import forbidden


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(permission):
                return forbidden('Not permissions')
            return f(*args, **kwargs)
        return decorated_function
    return decorator