from app import app, models, db, lm
from flask import render_template, flash, redirect, session, request, url_for, send_file, send_from_directory
from flask_login import login_user, login_required, logout_user, current_user, login_required
from .forms import SignupForm, LoginForm, PostForm, UpdatePasswordForm, ForgotForm, UpdateUsernameForm
from config import ADMINS, ALLOWED_EXTENSIONS, UPLOAD_FOLDER, POSTS_PER_PAGE
from .emails import send_email
import datetime, csv, os
from werkzeug import secure_filename

lm.login_view = "login"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@lm.user_loader
def load_user(id):
    return models.User.query.get(int(id))


@app.route('/', methods=['GET'])
def index():
    page = int(request.args.get('page')) if 'page' in request.args else 1
    if current_user.is_authenticated:
        posts = current_user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
    else:
        posts = models.Post.query.order_by("date desc").paginate(page, POSTS_PER_PAGE, False)
    form = PostForm()
    return render_template("user/index.html", title='Home', posts=posts, form=form)


@app.route('/posts', methods=["GET"])
def all_posts():
    page = int(request.args.get('page')) if 'page' in request.args else 1
    posts = models.Post.query.order_by("date desc").paginate(page, POSTS_PER_PAGE, False)
    form = PostForm()
    return render_template("user/index.html", title='Home', posts=posts, form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if request.method == "GET":
        return render_template("general/signup.html", title="Sign Up", form=form)
    if form.validate_on_submit():
        if models.User.query.filter_by(email=form.email.data).count() > 0:
            flash("Email is already in use")
        elif models.User.query.filter_by(username=form.username.data).count() > 0:
            flash("Username is already in use")
        else:
            new_user = models.User(name=form.fname.data + ' ' + form.lname.data, fname=form.fname.data, lname=form.lname.data, email=form.email.data, nickname=form.nickname.data, username=form.username.data)
            new_user.set_password(form.password.data)
            if form.email.data in ADMINS:
                new_user.is_admin = True
            else:
                new_user.is_admin = False
            db.session.add(new_user)
            db.session.commit()
            new_user.follow(new_user)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            send_email("Your account was created successfully", "Website Name", [form.email.data], "WebDevBlog@gmail.com", render_template("email/account_created.html"))
            return redirect(url_for("index"))
    return render_template("general/signup.html", title="Sign Up", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if request.method == "GET":
        return render_template("general/login.html", title="Log In", form=form)
    if form.validate_on_submit():
        if models.User.query.filter_by(username=form.username.data).count() == 0:
            flash("Email or Password is incorrect")
        else:
            user = models.User.query.filter_by(username=form.username.data).one()
            if user.check_password(form.password.data):
                login_user(user)
                return redirect(request.args.get("next") or url_for("index"))
            else:
                flash("Email or Password is incorrect")
    return render_template("general/login.html", title="Log In", form=form)


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(request.args.get("next") or url_for("index"))


@app.route('/profile/<user>', methods=['GET'])
def profile(user):
    page = int(request.args.get('page')) if 'page' in request.args else 1
    if models.User.query.filter_by(username=user).count() == 0:
        return render_template('user/user_not_found.html')
    edit_form = PostForm()
    change_password_form = UpdatePasswordForm()
    user = models.User.query.filter_by(username=user).one()
    posts = models.Post.query.filter_by(author=user).order_by("date desc").paginate(page, POSTS_PER_PAGE, False)
    return render_template("user/profile.html", user=user, update_form=SignupForm(), posts=posts, title="%s %s" % (user.fname, user.lname), edit_form=edit_form, password_form=change_password_form)


@app.route('/post', methods=['POST'])
@login_required
def post():
    form = PostForm()
    if form.validate():
        new_post = models.Post(body=form.body.data.strip(), date=datetime.datetime.utcnow(), author=current_user)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("index"))
    print form.body.errors
    return redirect(url_for("index"))


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
    if current_user.username == username:
        return redirect(request.referrer)
    user_to_follow = models.User.query.filter_by(username=username).one()
    user = models.User.query.filter_by(username=current_user.username).one().unfollow(user_to_follow)
    db.session.add(user)
    db.session.commit()
    return redirect(request.referrer)


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


@app.route('/delete_post/<int:id>', methods=['GET'])
@login_required
def delete_post(id):
    post = models.Post.query.filter_by(id=id).one()
    if post.author == current_user or current_user.is_admin:
        db.session.delete(post)
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


@app.route('/update_user', methods=['POST'])
def update_user():
    user = models.User.query.filter_by(username=request.args.get('user')).one()
    errors = []
    form = SignupForm()
    form.password.data = "Need_to_validate"
    form.confirm_password.data = "Need_to_validate"
    if form.validate_on_submit():
        if models.User.query.filter_by(username=form.username.data).count() == 1:
            if models.User.query.filter_by(username=form.username.data).one() != current_user:
                errors += ["This username is already in use"]
        if models.User.query.filter_by(email=form.email.data).count() == 1:
            if models.User.query.filter_by(email=form.email.data).one() != current_user:
                errors += ["This email is already in use"]
        user.email = form.email.data
        user.username = form.username.data
        user.nickname = form.nickname.data
        user.fname = form.fname.data
        user.lname = form.lname.data
        user.name = "%s %s" % (form.fname.data, form.lname.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('profile', user=form.username.data))
    for field in form:
        errors += field.errors
    print "Errors: ", errors
    flash(errors, 'user-errors')
    return redirect(request.referrer)


@app.route('/users', methods=["GET"])
def users():
    if current_user.is_authenticated:
        users = [current_user] + models.User.query.filter(models.User.id != current_user.id).all()
    else:
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


@app.route('/delete_user/<int:id>', methods=["GET"])
@login_required
def delete_user(id):
    if id == current_user.id or current_user.is_admin:
        query = models.User.query.filter_by(id=id)
        if query.one().is_admin and id != current_user.id:
            flash("You cannot delete the account of an admin without demoting them first", "delete-error")
            return redirect(request.referrer)
        else:
            models.Post.query.filter_by(author=query.one()).delete()
            query.delete()
            db.session.commit()
    return redirect(url_for("index"))


@app.route('/forgot_password', methods=["GET", "POST"])
def forgot_password():
    form = ForgotForm()
    if form.validate_on_submit():
        if models.User.query.filter_by(email=form.email.data).count() == 1:
            user = models.User.query.filter_by(email=form.email.data).one()
        else:
            return render_template("general/forgot_password.html", title="Forgot Password", form=form)
        user_request = models.ResetRequest(user=user, date=datetime.datetime.utcnow())
        db.session.add(user_request)
        requests_to_delete = db.session.query(models.ResetRequest).filter(models.ResetRequest.date >= datetime.datetime.utcnow() + datetime.timedelta(minutes=10)).all()
        for req in requests_to_delete:
            db.session.delete(req)
        db.session.commit()
        send_email("Password Recovery", "Website Name", [form.email.data], "WebDevBlog@gmail.com", render_template("email/password_change.html", id=user_request.id))
        return redirect(request.args.get("next") or url_for("login"))
    return render_template("general/forgot_password.html", title="Forgot Password", form=form)


@app.route('/change_password/<id>', methods=["GET", "POST"])
def change_password(id):
    form = UpdatePasswordForm()
    if form.validate_on_submit():
        user_request = models.ResetRequest.query.filter_by(id=id).one()
        user = user_request.user
        user.set_password(form.new_password.data)
        models.ResetRequest.query.filter_by(id=id).delete()
        db.session.add(user, user_request)
        db.session.commit()
        return render_template("general/login.html", id=id, form=LoginForm())
    return render_template("general/change_password.html", id=id, form=form)


@app.route('/forgot_username', methods=["GET", "POST"])
def forgot_username():
    form = ForgotForm()
    if form.validate_on_submit():
        if models.User.query.filter_by(email=form.email.data).count() == 1:
            user = models.User.query.filter_by(email=form.email.data).one()
        else:
            return render_template("general/forgot_username.html", title="Forgot Username", form=form)
        user_request = models.ResetRequest(user=user, date=datetime.datetime.utcnow())
        db.session.add(user_request)
        requests_to_delete = db.session.query(models.ResetRequest).filter(models.ResetRequest.date >= datetime.datetime.utcnow() + datetime.timedelta(minutes=10)).all()
        for req in requests_to_delete:
            db.session.delete(req)
        db.session.commit()
        send_email("Username Recovery", "Website Name", [form.email.data], "WebDevBlog@gmail.com", render_template("email/username_change.html", id=user_request.id))
        return redirect(request.args.get("next") or url_for("login"))
    return render_template("general/forgot_username.html", title="Forgot Username", form=form)


@app.route('/change_username/<id>', methods=["GET", "POST"])
def change_username(id):
    form = UpdateUsernameForm()
    if form.validate_on_submit():
        if models.ResetRequest.query.filter_by(id=id).count() == 1:
            user_request = models.ResetRequest.query.filter_by(id=id).one()
        else:
            return render_template("general/no_request.html")
        user = user_request.user
        if models.User.query.filter_by(username=form.username.data).count() == 1:
            flash("This username is already in use")
            return render_template("general/change_username.html", id=id, form=form)
        else:
            user.username = form.username.data
            models.ResetRequest.query.filter_by(id=id).delete()
            db.session.add(user, user_request)
            db.session.commit()
        return render_template("general/login.html", id=id, form=LoginForm())
    return render_template("general/change_username.html", id=id, form=form)


@app.route('/upload_profile_pic', methods=["POST"])
@login_required
def upload_profile_pic():
    file = request.files['picture']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        old_filename = current_user.profile_image
        if old_filename != "default.png":
            os.remove(os.path.join(UPLOAD_FOLDER, old_filename))
        current_user.profile_image = filename
        db.session.add(current_user)
        db.session.commit()
    return redirect(request.referrer)


@app.route('/profile_picture/<int:user_id>', methods=["GET"])
def get_profile_pic(user_id):
    filename = models.User.query.filter_by(id=user_id).one().profile_image
    return send_from_directory('data/uploads/', filename)


@app.route('/add_admin/<int:id>', methods=["GET"])
@login_required
def add_admin(id):
    if current_user.is_admin:
        u = models.User.query.filter_by(id=id).one()
        u.is_admin = True
        db.session.add(u)
        db.session.commit()
    return redirect(request.referrer)


@app.route('/remove_admin/<int:id>', methods=["GET"])
@login_required
def remove_admin(id):
    if current_user.is_admin:
        u = models.User.query.filter_by(id=id).one()
        if u.email not in ADMINS:
            u.is_admin = False
            db.session.add(u)
            db.session.commit()
        else:
            flash("You Can't Remove this Admin", "admin-error")
    return redirect(request.referrer)


@app.route('/admin')
@login_required
def admin_controls():
    page = int(request.args.get('page')) if 'page' in request.args else 1
    form = PostForm()
    if not current_user.is_admin:
        return redirect(url_for("index"))
    else:
        posts = models.Post.query.order_by("date desc").paginate(page, POSTS_PER_PAGE, False)
        return render_template('admin/admin_panel.html', title="Admin Panel", edit_form=form, postCount=models.Post.query.count(), userCount=models.User.query.count(), posts=posts)


@app.route('/users/csv', methods=['GET'])
@login_required
def get_users_csv():
    if current_user.is_admin:
        users = [models.User.query.first().__dict__.keys()]
        for u in models.User.query.all():
            user_temp = []
            for key, value in u.__dict__.items():
                user_temp += [value]
            users += [user_temp]
        with open("app/data/users.csv", "wb") as f:
            writer = csv.writer(f)
            writer.writerows(users)
        return send_file('data/users.csv',
                         mimetype='text/csv',
                         attachment_filename='data/users.csv',
                         as_attachment=True)
    return redirect(url_for("index"))
