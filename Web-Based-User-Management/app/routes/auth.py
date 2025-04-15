import os
import requests
from flask import Blueprint, redirect, url_for, session, flash, request, render_template
from app.models import User
import app.services.auth_service as auth_service
from app.extensions.db import db

auth = Blueprint('auth', __name__)

# Load secrets 
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
SCOPE = ["User.Read"]

@auth.route("/login")
def microsoft_login():
    if "user" in session:
        return redirect(url_for("admin.admin_dashboard"))

    redirect_uri = url_for('auth.microsoft_callback', _external=True)
    login_url = (
        f"{AUTHORITY}?client_id={CLIENT_ID}"
        f"&response_type=code&redirect_uri={redirect_uri}"
        f"&scope={' '.join(SCOPE)}"
    )
    return redirect(login_url)


@auth.route('/auth/callback')
def microsoft_callback():
    redirect_uri = url_for('auth.microsoft_callback', _external=True)
    user, err_msg = auth_service.microsoft_callback(redirect_uri)

    if type(user) is not type(dict()):
        flash(err_msg, "error")
        return redirect(url_for("main.home"))

    user = User.query.filter_by(email=session["email"].lower()).first()

    if user is None:
        flash("Account doesn't exist in the system. Please logout and login with a valid account or contact support", "error")
        session["exists"] = False
        return redirect(url_for('main.home'))

    if user.status.lower() != "active":
        flash("Account isn't active. Please logout and login with a valid account or contact support", "error")
        session["active"] = False
        return redirect(url_for("main.home"))

    flash(f"Welcome, {session['user']}!", "success")

    if user.role.lower() == "admin":
        session["role"] = "Admin"
        return redirect(url_for('admin.admin_dashboard'))
    else:
        session["role"] = "User"
        return redirect(url_for('dashboard.user_dashboard'))


@auth.route('/logout')
def logout():
    session.clear()
    ms_logout_url = "https://login.microsoftonline.com/common/oauth2/logout?post_logout_redirect_uri=" + url_for('main.home', _external=True)
    flash("You have been logged out.", "success")
    return redirect(ms_logout_url)


# New user registration route
@auth.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        display_name = request.form.get("display_name")
        email = request.form.get("email")

        if not email.endswith("@cougarnet.uh.edu"):
            flash("Only UH emails are allowed.", "error")
            return render_template("register.html")

        # Check if user exists already
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with that email already exists.", "error")
            return render_template("register.html")

        new_user = User(display_name=display_name, email=email.lower(), role="User", status="active")
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for("auth.microsoft_login"))

    return render_template("register.html")
