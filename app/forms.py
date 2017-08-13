from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo
from app import models


class LoginForm(Form):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField()


class SignupForm(Form):
    fname = StringField("First Name", validators=[DataRequired()])
    lname = StringField("Last Name", validators=[DataRequired()])
    email = StringField("Email", validators=[Email()])
    username = StringField("Username", validators=[DataRequired()])
    nickname = StringField("Nickname", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Password", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField()


class PostForm(Form):
    body = TextAreaField('Post', validators=[DataRequired()])
    submit = SubmitField()


class ForgotForm(Form):
    email = StringField('Email', validators=[Email()])
    submit = SubmitField()


class UpdatePasswordForm(Form):
    new_password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Password", validators=[DataRequired(), EqualTo('new_password', message="Passwords don't Match")])
    submit = SubmitField()


class UpdateUsernameForm(Form):
    username = StringField("Username", validators=[DataRequired()])
    submit = SubmitField()