#encoding: utf-8
from flask_wtf import Form,FlaskForm
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import Required,Length,Email,Regexp,EqualTo
#EqualTo用来验证两个密码字段值是否一致，需要附加在一个上，另一个作为参数传入

from wtforms import ValidationError  #
from ..models import User #当注册新用户时，需要再数据库表中插入一条用户的完整信息记录，User模型就是用户表

class LoginForm(Form):
    email = StringField(u'邮箱',validators=[Required(),Length(1,64),Email()])
    password = PasswordField(u'密码',validators=[Required()])
    remember_me = BooleanField(u'记住我')
    submit = SubmitField(u'提交')

#注册表单以及两个验证函数（验证Email and username 是否已经被用）
class RegistrationForm(Form):
    email = StringField(u'邮箱',validators=[Required(),Length(1,64),Email()])
    username = StringField(u'用户名',validators=[Required(),Length(1,64)])    #,Regexp('^\w*$',0,'Username must have only letters,numbers,dots,or underscores'),加上这个要求输入英文且首字母非数字
    password = PasswordField(u'密码',validators=[Required(),EqualTo('password2',message='Password must match.')])
    password2 = PasswordField(u'重复密码',validators=[Required()])
    phone = StringField(u'绑定手机号',validators=[Required(),Length(6,11)])
    submit = SubmitField(u'提交')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

#change password
class ChangePasswordForm(Form):
    old_password = PasswordField('Old password', validators=[Required()])
    password = PasswordField('New password', validators=[
        Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm new password', validators=[Required()])
    submit = SubmitField('Update Password')

#change eamil
# class ChangeEmailForm(FlaskForm):
#     email = StringField('New Email', validators=[Required(), Length(1, 64),Email()])
#     password = PasswordField('Password', validators=[Required()])
#     submit = SubmitField('Update Email Address')
#
#     def validate_email(self, field):
#         if User.query.filter_by(email=field.data).first():
#             raise ValidationError('Email already registered.')


# 忘记密码
class PasswordResetRequestForm(FlaskForm):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64),Email()])
    submit = SubmitField(u'重置密码')


class PasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64),Email()])
    password = PasswordField('New Password', validators=[Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')