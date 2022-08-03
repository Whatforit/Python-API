# pylint: disable=E1101, R0903
"""Simple Flask blog app"""
from datetime import datetime
import hashlib
import uuid
import regex as re
from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/database.db"
db = SQLAlchemy(app)


class Post(db.Model):
    """Post object for database"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    user_name = db.Column(db.String(100))
    content = db.Column(db.String(1000))
    post_time = db.Column(db.String(100))

    def __init__(self, title, user_name, content, post_time):
        self.title = title
        self.user_name = user_name
        self.content = content
        self.post_time = post_time


class User(db.Model):
    """User object for database"""
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100))
    password_hash = db.Column(db.String(100))
    email = db.Column(db.String(100))
    access_token = db.Column(db.String(100))

    def __init__(self, user_name, password, email):
        self.user_name = user_name
        self.password_hash = hash_password(password)
        self.email = email
        self.access_token = uuid.uuid4().hex


db.create_all()


def create_user(user_name, password, email):
    """Add user to database"""
    user = User(user_name, password, email)
    db.session.add(user)
    db.session.commit()
    return user


def delete_user(user_name):
    """Delete user from database"""
    user = User.query.filter_by(user_name=user_name).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return True
    return False


def user_name_exists(user_name):
    """Check if user_name is taken"""
    user = User.query.filter_by(user_name=user_name).first()
    if user:
        return True
    return False


def delete_post(post_id):
    """Delete post from database"""
    post = Post.query.filter_by(id=post_id).first()
    if post:
        db.session.delete(post)
        db.session.commit()
        return True
    return False


def edit_post(post_id, title, content):
    """Edit post in database"""
    post = Post.query.filter_by(id=post_id).first()
    if post:
        post.title = title
        post.content = content
        db.session.commit()
        return True
    return False


def hash_password(password):
    """Hash password"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def check_login(user_name, password):
    """Check if user_name and password are correct"""
    user = User.query.filter_by(user_name=user_name).first()
    print(user.password_hash)
    print(hash_password(password))
    if user.password_hash == hash_password(password):
        return True
    return False


def get_all_posts():
    """Get all posts from database"""
    return Post.query.all()


def get_post(post_id):
    """Get post from database"""
    return Post.query.filter_by(id=post_id).first()


def logged_in():
    """Check if user is logged in"""
    if "user_name" in session:
        print(session["user_name"])
        return True
    return False


def login_from_cookie():
    """Login user from cookie"""
    guid = request.cookies.get("guid")
    if guid:
        user = User.query.filter_by(access_token=guid).first()
        if user:
            session["user_name"] = user.user_name
            return (True, "Login successful")
    return (False, "Cookie not found")


def login(user_name, password):
    """Login user"""
    if user_name_exists(user_name):
        if check_login(user_name, password):
            print("Login successful")
            session["user_name"] = user_name
            return (True, "Login successful")
        return (False, "Password incorrect")
    return (False, "User not found")


def register(user_name, email, password, conf_password):
    """Register user"""
    if user_name_exists(user_name):
        return (False, "User already exists")
    if not re.match(r'([a-z0-9]+@[a-z]+\.[a-z]{2,3})', email):
        return (False, "Email not valid")
    if password != conf_password:
        return (False, "Passwords do not match")
    create_user(user_name, password, email)
    return (True, "Registration successful")


def delete_all_posts():
    """Delete all posts from database"""
    db.session.query(Post).delete()
    db.session.commit()


def delete_all_users():
    """Delete all users from database"""
    db.session.query(User).delete()
    db.session.commit()


def get_user(user_name):
    """Get user from database"""
    return User.query.filter_by(user_name=user_name).first()


def get_all_users():
    """Get all users from database"""
    return User.query.all()


def create_post(title, user_name, content):
    """Create post"""
    post = Post(
        title,
        user_name,
        content,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    db.session.add(post)
    db.session.commit()
    return post


delete_all_users()
delete_all_posts()
create_user("admin", "admin", "")
create_post("Welcome!", "Admin", "Welcome to the blog!")


@app.route("/")
@app.route("/Home")
def home_page():
    """Home page"""
    for user in get_all_users():
        print(user.user_name)
    if logged_in():
        if session["user_name"] == "admin":
            pages = ["Home", "About", "Users", "Post", "Logout"]
        else:
            pages = ["Home", "About", "Post", "Logout"]
    else:
        pages = ["Home", "About", "Register", "Login"]
    query = db.session.query(Post)
    return render_template(
        "home.html",
        pages=pages,
        current_page="Home",
        posts=query)


@app.route("/About")
def about_page():
    """About page"""
    if "user_name" in session:
        pages = ["Home", "About", "Post", "Logout"]
    if session["user_name"] == "admin":
        pages = ["Home", "About", "Users", "Post", "Logout"]
    else:
        pages = ["Home", "About", "Register", "Login"]
    return render_template("about.html", pages=pages, current_page="About")


@app.route("/Login", methods=["GET", "POST"])
def login_page():
    """Login page"""
    pages = ["Home", "About", "Register"]
    (success, message) = login_from_cookie()
    if success:
        resp = make_response(
            redirect(
                url_for(
                    "landing_page",
                    success=message)))
        resp.set_cookie("guid", request.cookies.get("guid"), max_age=60 * 60)
        return resp
    if request.method == "POST":
        user_name = request.form["user_name"]
        password = request.form["password"]
        remember = request.form.get("remember")
        (success, message) = login(user_name, password)
        if success:
            pages = ["Home", "About", "Post", "Logout"]
            resp = make_response(
                render_template(
                    "landing_page.html",
                    pages=pages,
                    success=message))
            if remember:
                print("setting cookie")
                resp.set_cookie("guid", get_user(user_name).access_token)
            else:
                resp.set_cookie("guid", "", expires=0)
            return resp
        return render_template(
            "login.html",
            pages=pages,
            current_page="Login",
            error=message)
    return render_template("login.html", pages=pages, current_page="Login")


@app.route("/Register", methods=["GET", "POST"])
def register_page():
    """Register page"""
    pages = ["Home", "About", "Login"]
    if request.method == "POST":
        user_name = request.form["user_name"]
        email = request.form["email"]
        password = request.form["password"]
        conf_password = request.form["conf_password"]
        (success, message) = register(user_name, email, password, conf_password)
        if success:
            print("Registration successful")
            resp = make_response(
                redirect(
                    url_for(
                        "login_page",
                        success=message)))
            login(user_name, password)
            return resp

        return render_template(
            "register.html",
            pages=pages,
            current_page="Register",
            error=message)
    return render_template(
        "register.html",
        pages=pages,
        current_page="Register")


@app.route("/Logout")
def logout():
    """Logout page"""
    session.pop("user_name", None)
    resp = make_response(redirect(url_for("home_page")))
    resp.set_cookie("guid", "", expires=0)
    return resp


@app.route("/Post", methods=["GET", "POST"])
def post_page():
    """Post page"""
    if not logged_in():
        pages = ["Home", "About", "Register", "Login"]
        resp = make_response(
            render_template(
                "landing_page.html",
                pages=pages,
                error="You must be logged in to post"))
        return resp
    if session["user_name"] == "admin":
        pages = ["Home", "About", "Users", "Post", "Logout"]
    pages = ["Home", "Posts", "About", "Logout"]
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        user_name = session["user_name"]
        create_post(title, user_name, content)
        return redirect(url_for("home_page"))
    return render_template("post.html", pages=pages, current_page="Post")


@app.route("/Users")
def users_page():
    """Users page"""
    if session["user_name"] != "admin":
        pages = ["Home", "About", "Register", "Login"]
        resp = make_response(
            render_template(
                "landing_page.html",
                pages=pages,
                error="You must be Admin to view this page"))
        return resp
    pages = ["Home", "About", "Posts", "Logout"]
    return render_template(
        "users.html",
        pages=pages,
        current_page="Users",
        users=get_all_users())


app.run("0.0.0.0", port=5000, debug=True)
