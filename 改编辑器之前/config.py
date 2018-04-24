#encoding: utf-8
import os
basedir = os.path.abspath(os.path.dirname(__file__))

# 限制上传格式
ALLOWED_EXTENSIONS = set(['msi','txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','docx','doc','ppt','exe','mp4','iso'])

class Config:
    SECRET_KEY = 'this is a password'       # 生成token时用到
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 邮件设置
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "1274866364@qq.com"
    MAIL_PASSWORD = "iaivitlcqcyjiiai"      #   QQ邮箱SMTP密码
    FLASKY_MAIL_SUBJECT_PREFIX = u'TimeAshore-'
    FLASKY_MAIL_SENDER ='1274866364@qq.com'
    FLASKY_ADMIN = '1274866364@qq.com'

    # 分页，每页文章数量
    FLASKY_POSTS_PER_PAGE = 6
    # 显示关注用户列表
    FLASKY_FOLLOWERS_PER_PAGE = 11
    # 每页评论
    FLASKY_COMMENTS_PER_PAGE = 15

    #上传路径
    UPLOAD_FOLDER = 'C:\Users\TIME\Desktop\hehe_2\uploads'
    #文件大小（200M）
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-product.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
