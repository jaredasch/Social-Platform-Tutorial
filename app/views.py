from app import app, models, db, lm
from flask import render_template, flash, redirect, session, request, url_for
from flask_login import login_user, login_required, logout_user, current_user, login_required
from flask_security import url_for_security
from .forms import SignupForm, LoginForm, PostForm, UpdatePasswordForm
from config import ADMINS
import datetime

lm.login_view = "login"


@lm.user_loader
def load_user(id):
    return models.User.query.get(int(id))


@app.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        posts = current_user.followed_posts()
    else:
        posts = models.Post.query.order_by("date desc").all()
    form = PostForm()
    return render_template("user/index.html", title='Home', posts=posts, form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if request.method == "GET":
        return render_template("general/signup.html", title="Sign Up", form=form)
    if form.validate_on_submit():
        new_user = models.User(name=form.fname.data + ' ' + form.lname.data, fname=form.fname.data, lname=form.lname.data, email=form.email.data, nickname=form.nickname.data, username=form.username.data)
        new_user.set_password(form.password.data)
        if form.email.data in ADMINS:
            new_user.is_admin = True
        db.session.add(new_user)
        db.session.commit()
        db.session.add(new_user.follow(new_user))
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("index"))
    return render_template("general/signup.html", title="Sign Up", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "GET":
        return render_template("general/login.html", title="Log In", form=form)
    if form.validate_on_submit():
        if models.User.query.filter_by(email=form.email.data).count() == 0:
            flash("Email or Password is incorrect")
        else:
            user = models.User.query.filter_by(email=form.email.data).one()
            if user.check_password(form.password.data):
                login_user(user)
                return redirect(request.args.get("next") or url_for("index"))
            else:
                flash("Email or Password is incorrect")
    return render_template("general/login.html", title="Log In", form=form)


@app.route('/profile/<user>')
def profile(user):
    if models.User.query.filter_by(username=user).count() == 0:
        return render_template('user/user_not_found.html')
    edit_form = PostForm()
    change_password_form = UpdatePasswordForm()
    user = models.User.query.filter_by(username=user).one()
    posts = models.Post.query.filter_by(author=user).order_by("date desc")
    return render_template("user/profile.html", user=user, posts=posts, title="%s %s" % (user.fname, user.lname), edit_form=edit_form, password_form = change_password_form)


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


@app.route('/delete_post/<int:id>', methods=['GET'])
@login_required
def delete_post(id):
    post = models.Post.query.filter_by(id=id).one()
    if post.author == current_user or current_user.is_admin:
        db.session.delete(post)
        db.session.commit()
    return redirect(request.referrer)


@app.route('/follow/<username>', methods=["GET"])
@login_required
def follow(username):
    user_to_follow = models.User.query.filter_by(username=username).one()
    user = models.User.query.filter_by(username=current_user.username).one().follow(user_to_follow)
    db.session.add(user)
    db.session.commit()
    return redirect(request.referrer)


@app.route('/unfollow/<username>', methods=["GET"])
@login_required
def unfollow(username):
    user_to_follow = models.User.query.filter_by(username=username).one()
    user = models.User.query.filter_by(username=current_user.username).one().unfollow(user_to_follow)
    db.session.add(user)
    db.session.commit()
    return redirect(request.referrer)


@app.route('/users', methods=["GET"])
def users():
    users = models.User.query.all()
    return render_template("user/users.html", title="All Users", users=users)


@app.route('/users/search', methods=["GET"])
def user_search():
    tag = request.args.get('tag')
    print tag
    results = models.User.query.whoosh_search(tag).all()
    print results
    if len(results) == 1:
        user = results[0]
        return redirect(url_for('profile', user=user.username))
    elif len(results) == 0:
        return render_template('user/user_not_found.html')
    return render_template('user/users.html', title="Results for %s" % tag, users=results)


@app.route('/admin/')
@login_required
def admin_controls():
    if not current_user.is_admin:
        return redirect(url_for("index"))
    else:
        return render_template('admin/admin_panel.html', admin=current_user, postCount=models.Post.query.count(), userCount=models.User.query.count())


@app.route('/edit_post/<int:id>', methods=["POST"])
@login_required
def edit_post(id):
    form = PostForm()
    post = models.Post.query.filter_by(id=id).one()
    if post.author == current_user or current_user.is_admin:
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
    return redirect(request.referrer)


@app.route('/update_password/', methods=['POST'])
def update_password():
    form = UpdatePasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        db.session.add(current_user)
        db.session.commit()
        return redirect(request.referrer)
    errors = []
    for field in form:
        errors += field.errors
    flash(errors)
    return redirect(request.referrer)
