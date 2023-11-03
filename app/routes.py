"""Provides all routes for the Social Insecurity application.

This file contains the routes for the application. It is imported by the app package.
It also contains the SQL queries used for communicating with the database.
"""

from pathlib import Path

import flask
from flask import flash, redirect, render_template, send_from_directory, url_for, request
from app import app, sqlite, User, bcrypt
from app.forms import CommentsForm, FriendsForm, IndexForm, PostForm, ProfileForm
from flask_login import login_user, login_required, logout_user, current_user, LoginManager, UserMixin, login_required


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    """Provides the index page for the application.

    It reads the composite IndexForm and based on which form was submitted,
    it either logs the user in or registers a new user.

    If no form was submitted, it simply renders the index page.
    """
    index_form = IndexForm()
    login_form = index_form.login
    register_form = index_form.register

    from flask_login import login_user

    # ...
    if login_form.validate_on_submit() and login_form.submit.data:
        get_user = f"""
        SELECT * FROM Users WHERE username = ?;
        """
        user = sqlite.query(get_user, True, login_form.username.data)
        if user is None:
            flash("Sorry, this user does not exist!", category="warning")
        if not bcrypt.check_password_hash(user["password"], login_form.password.data):
            flash("Sorry, wrong password!", category="warning")
        else:
            user_obj = User(
                id=user["id"],
                username=user["username"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                password=user["password"],
            )
            login_user(user_obj)
            return redirect(url_for("stream", username=user["username"]))

    elif register_form.validate_on_submit() and register_form.submit.data:
        hashed_password = bcrypt.generate_password_hash(register_form.password.data).decode('utf-8')
        insert_user = f"""
            INSERT INTO Users (username, first_name, last_name, password)
            VALUES (?, ?, ?, ?);
            """
        sqlite.query(insert_user, False, register_form.username.data, register_form.first_name.data, register_form.last_name.data, hashed_password)
        flash("User successfully created!", category="success")

        return redirect(url_for("index"))

    return render_template("index.html.j2", title="Welcome", form=index_form)


@app.route("/logout")
@login_required
def logout():
    """Provides the logout page for the application.
    It simply logs the user out and redirects them to the index page.
    """
    print(logout_user())
    return redirect(url_for("index"))


@app.route("/stream/<string:username>", methods=["GET", "POST"])
@login_required
def stream(username: str):
    """Provides the stream page for the application.

    If a form was submitted, it reads the form data and inserts a new post into the database.

    Otherwise, it reads the username from the URL and displays all posts from the user and their friends.
    """
    post_form = PostForm()

    if current_user.username != username:
        flash("You cannot access to others profile!", category="warning")
        logout_user()
        return redirect(url_for("index"))

    get_user = f"""
        SELECT *
        FROM Users
        WHERE username = ?;
        """
    user = sqlite.query(get_user, True, username)

    if post_form.is_submitted():
        if post_form.image.data:
            path = Path(app.instance_path) / app.config["UPLOADS_FOLDER_PATH"] / post_form.image.data.filename
            post_form.image.data.save(path)

        insert_post = f"""
            INSERT INTO Posts (u_id, content, image, creation_time)
            VALUES (?,?,?, CURRENT_TIMESTAMP);
            """
        sqlite.query(insert_post, False,user["id"],post_form.content.data, post_form.image.data.filename)
        return redirect(url_for("stream", username=username))

    get_posts = """
             SELECT p.*, u.*, (SELECT COUNT(*) FROM Comments WHERE p_id = p.id) AS cc
             FROM Posts AS p JOIN Users AS u ON u.id = p.u_id
             WHERE p.u_id IN (SELECT u_id FROM Friends WHERE f_id = ?) OR p.u_id IN (SELECT f_id FROM Friends WHERE u_id = ?) OR p.u_id = ?
             ORDER BY p.creation_time DESC;
            """
    posts = sqlite.query(get_posts, False, user["id"], user["id"], user["id"])
    return render_template("stream.html.j2", title="Stream", username=username, form=post_form, posts=posts)


@app.route("/comments/<string:username>/<int:post_id>", methods=["GET", "POST"])
@login_required
def comments(username: str, post_id: int):
    """Provides the comments page for the application.

    If a form was submitted, it reads the form data and inserts a new comment into the database.

    Otherwise, it reads the username and post id from the URL and displays all comments for the post.
    """
    if current_user.username != username:
        flash("You cannot access to others profile!", category="warning")
        logout_user()
        return redirect(url_for("index"))

    comments_form = CommentsForm()
    get_user = f"""
        SELECT *
        FROM Users
        WHERE username = ?;
        """
    user = sqlite.query(get_user, True, username)

    if comments_form.is_submitted():
        insert_comment = f"""
            INSERT INTO Comments (p_id, u_id, comment, creation_time)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP);
            """
        sqlite.query(insert_comment, False, post_id, user["id"], comments_form.comment.data)

    get_post = f"""
        SELECT *
        FROM Posts AS p JOIN Users AS u ON p.u_id = u.id
        WHERE p.id = ?;
        """

    get_comments = f"""
        SELECT DISTINCT *
        FROM Comments AS c JOIN Users AS u ON c.u_id = u.id
        WHERE c.p_id= ?
        ORDER BY c.creation_time DESC;
        """
    post = sqlite.query(get_post, True, post_id)
    comments = sqlite.query(get_comments, False, post_id)
    return render_template(
        "comments.html.j2", title="Comments", username=username, form=comments_form, post=post, comments=comments
    )


@app.route("/friends/<string:username>", methods=["GET", "POST"])
@login_required
def friends(username: str):

    if current_user.username != username:
        flash("You cannot access to others profile!", category="warning")
        logout_user()
        return redirect(url_for("index"))

    """Provides the friends page for the application.

    If a form was submitted, it reads the form data and inserts a new friend into the database.

    Otherwise, it reads the username from the URL and displays all friends of the user.
    """
    friends_form = FriendsForm()
    get_user = f"""
        SELECT *
        FROM Users
        WHERE username = ?;
        """
    user = sqlite.query(get_user, True, username)

    if friends_form.is_submitted():
        get_friend = f"""
            SELECT *
            FROM Users
            WHERE username = ?;
            """
        friend = sqlite.query(get_friend, True, friends_form.username.data)
        get_friends = f"""
            SELECT f_id
            FROM Friends
            WHERE u_id = ?;
            """
        friends = sqlite.query(get_friends, False, user["id"])

        if friend is None:
            flash("User does not exist!", category="warning")
        elif friend["id"] == user["id"]:
            flash("You cannot be friends with yourself!", category="warning")
        elif friend["id"] in [friend["f_id"] for friend in friends]:
            flash("You are already friends with this user!", category="warning")
        else:
            insert_friend = f"""
                INSERT INTO Friends (u_id, f_id)
                VALUES (?,  ?);
                """
            sqlite.query(insert_friend, False, user["id"], friend["id"])
            flash("Friend successfully added!", category="success")

    get_friends = f"""
        SELECT *
        FROM Friends AS f JOIN Users as u ON f.f_id = u.id
        WHERE f.u_id = ? AND f.f_id != ?;
        """
    friends = sqlite.query(get_friends, False, user["id"], user["id"])
    return render_template("friends.html.j2", title="Friends", username=username, friends=friends, form=friends_form)


@app.route("/profile/<string:username>", methods=["GET", "POST"])
@login_required
def profile(username: str):

    if current_user.username != username:
        flash("You cannot access to others profile!", category="warning")
        logout_user()
        return redirect(url_for("index"))

    """Provides the profile page for the application.

    If a form was submitted, it reads the form data and updates the user's profile in the database.

    Otherwise, it reads the username from the URL and displays the user's profile.
    """
    profile_form = ProfileForm()
    get_user = f"""
        SELECT *
        FROM Users
        WHERE username = ?;
        """
    user = sqlite.query(get_user, True, username)

    if profile_form.is_submitted():
        update_profile = """
            UPDATE Users
            SET education=?, employment=?,
                music=?, movie=?,
                nationality=?, birthday=?
            WHERE username=?;
            """
        sqlite.query(update_profile, False, profile_form.education.data, profile_form.employment.data,
                     profile_form.music.data, profile_form.movie.data,
                     profile_form.nationality.data, profile_form.birthday.data,
                     username)
        return redirect(url_for("profile", username=username))

    return render_template("profile.html.j2", title="Profile", username=username, user=user, form=profile_form)


@app.route("/uploads/<string:filename>")
@login_required
def uploads(filename):



    """Provides an endpoint for serving uploaded files."""
    return send_from_directory(Path(app.instance_path) / app.config["UPLOADS_FOLDER_PATH"], filename)
