"""
auth.py — Google OAuth helpers + session utilities.
Works for all 3 portals; pass redirect_uri per portal.
"""
import requests, hashlib, os
from functools import wraps
from flask import session, redirect, url_for, request, flash
from shared.config import Config

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL  = "https://www.googleapis.com/oauth2/v3/userinfo"

def google_login_url(redirect_uri: str, state: str = "") -> str:
    params = {
        "client_id":     Config.GOOGLE_CLIENT_ID,
        "redirect_uri":  redirect_uri,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "state":         state,
    }
    return GOOGLE_AUTH_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())

def google_exchange_code(code: str, redirect_uri: str) -> dict | None:
    """Exchange auth code for user info dict."""
    try:
        token_resp = requests.post(GOOGLE_TOKEN_URL, data={
            "code":          code,
            "client_id":     Config.GOOGLE_CLIENT_ID,
            "client_secret": Config.GOOGLE_CLIENT_SECRET,
            "redirect_uri":  redirect_uri,
            "grant_type":    "authorization_code",
        }, timeout=10)
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return None
        user_resp = requests.get(GOOGLE_USER_URL,
                                 headers={"Authorization": f"Bearer {access_token}"},
                                 timeout=10)
        return user_resp.json()
    except Exception:
        return None

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed

# ── Session helpers ──────────────────────────────────────────────────────────
def login_user(user: dict, role: str):
    session['user_id']   = user['_id']
    session['user_name'] = user.get('name', '')
    session['user_email']= user.get('email', '')
    session['role']      = role
    session['avatar']    = user.get('avatar', '')
    session.permanent    = True

def logout_user():
    session.clear()

def current_user() -> dict | None:
    if 'user_id' in session:
        return {
            '_id':   session['user_id'],
            'name':  session['user_name'],
            'email': session['user_email'],
            'role':  session['role'],
            'avatar':session['avatar'],
        }
    return None

# ── Decorators ───────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user():
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = current_user()
            if not user or user.get('role') not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated
    return decorator
