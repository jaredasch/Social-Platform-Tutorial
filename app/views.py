from app import app, models, db, lm
from flask import render_template, flash, redirect, session, request, url_for
from flask_login import login_user, login_required, logout_user, current_user, login_required
from .forms import SignupForm, LoginForm, PostForm
import datetime

lm.login_view = "login"


@lm.user_loader
def load_user(id):
    return models.User.query.get(int(id))


@app.route('/', methods=['GET'])
@login_required
def index():
    posts = models.Post.query.order_by("date desc").all()
    form = PostForm()
    return render_template("user/index.html", title='Home', posts=posts, form=form)


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


@app.route('/profile/<user>')
@login_required
def profile(user):
    if models.User.query.filter_by(username=user).count() == 0:
        return redirect(url_for("index"))
    user = models.User.query.filter_by(username=user).one()
    posts = models.Post.query.filter_by(author=user)
    return render_template("user/profile.html", user=user, posts=posts, title=user.fname + "'s Profile")


@app.route('/post', methods=['POST'])
@login_required
def post():
    form = PostForm()
    if form.validate():
        new_post = models.Post(body=form.body.data, date=datetime.datetime.utcnow(), author=current_user)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("index"))
    print form.body.errors
    return redirect(url_for("index"))


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(request.args.get("next") or url_for("index"))
