#encoding: utf-8
from flask_wtf import FlaskForm,Form
from wtforms import StringField, SubmitField,TextAreaField,BooleanField,SelectField
from wtforms.validators import Required,Length,ValidationError,Email
from ..models import Role,User
from flask_pagedown.fields import PageDownField


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')

class EditProfileForm(Form):
    name = StringField('Real name',validators=[Required(),Length(0,64)])
    location = StringField('Location',validators=[Length(0,64)])
    about_me = TextAreaField('About me.')
    submit = SubmitField('Submit')

class EditProfileAdminForm(Form):
    email = StringField('Email',validators=[Required(),Length(1,64),Email()])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role',coerce=int)
    name = StringField('Real name',validators=[Length(0,64)])
    location = StringField('Location',validators=[Length(0,64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self,user,*args,**kwargs):
        super(EditProfileAdminForm, self).__init__(*args,**kwargs)
        self.role.choices = [ (role.id,role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user
    def validate_email(self,field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self,field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

class PostForm(Form):
    body = PageDownField(u"新文章",validators=[Required()])
    submit = SubmitField(u'发布')

class CommentForm(FlaskForm):
    body = StringField(u'评论', validators=[Required()])
    submit = SubmitField(u'评论')

class Send_Email_To_Admin(Form):
    # render_kw={'placeholder':u'输入用户名'}指定在输入框内显示的内容
    content = TextAreaField(u'发送内容',validators=[Required()],render_kw={'placeholder':u'输入要发送的内容'})
    send = SubmitField(u'发送')


# 告白墙
class Confession(Form):
    confession = TextAreaField(u'告白',validators=[Required()],render_kw={'placeholder':u"告白内容"})
    submit = SubmitField(u'发布')

# translate online
class Translate(Form):
    content = TextAreaField(u'在线翻译',validators=[Required()],render_kw={'placeholder':u"请输入你要翻译的文字"})
    submit = SubmitField(u'翻译')
class Translate_answer(Form):
    answer = TextAreaField(u'结果')