from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo
from app import models


class LoginForm(Form):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField()

    def validate_on_submit(self):
        if Form.validate(self):
            return False
        if models.User.query.filter_by(email=self.email.data).count() == 0:
            self.email.errors.append("User is not registered")
            return False
        if not models.User.query.filter_by(email=self.email.data).one().check_password(self.password.data):
            self.password.errors.append("Email or password is incorrect")
            return False
        return True


class SignupForm(Form):
    fname = StringField("First Name", validators=[DataRequired()])
    lname = StringField("Last Name", validators=[DataRequired()])
    email = StringField("Email", validators=[Email()])
    username = StringField("Username", validators=[DataRequired()])
    nickname = StringField("Nickname", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Password", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField()

