from app import app, models, db, lm
from flask import render_template, flash, redirect, session, request, url_for, g
from flask_login import login_user, login_required, logout_user, current_user, login_required
from .forms import SignupForm, LoginForm
from .models import User



@lm.user_loader
def load_user(id):
    return models.User.query.get(int(id))

@app.before_request
def before_request(): # Stores the current user in the g.user global variable
    g.user = current_user.fname

@app.route('/', methods=['GET'])
def index():
    return render_template("base.html", title="Home", session=session)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if request.method == "GET":
        return render_template("general/signup.html", title="Sign Up", form=form)
    if form.validate_on_submit():
        new_user = models.User(fname=form.fname.data, lname=form.lname.data, email=form.email.data, nickname=form.nickname.data, username=form.username.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("index"))
    return render_template("general/signup.html", title="Sign Up", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "GET":
        return render_template("general/login.html", title="Log In", form=form)
    if form.validate():
        user = models.User.query.filter_by(email=form.email.data).one()
        login_user(user)
        return redirect(request.args.get("next") or url_for("index"))
    return render_template("general/login.html", title="Log In", form=form)

@app.route('/profile')
def profile():
    return render_template("user/profile.html", name = g.user, title = g.user + "'s Profile")

@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(request.args.get("next") or url_for("index"))
