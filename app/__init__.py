#encoding: utf-8
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager
from flask_pagedown import PageDown

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
pagedown = PageDown()

login_manager.session_protection = 'strong'         # 安全等级
login_manager.login_view = 'auth.login'             # 登陆页面的端点



def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])     # 导入配置
    config[config_name].init_app(app)
    login_manager.init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    pagedown.init_app(app)

    # 注册蓝本
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint,url_prefix='/main')

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint,url_prefix='/auth')


    # rest web api蓝本
    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    return app

