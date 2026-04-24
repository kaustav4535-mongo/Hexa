import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from shared import db
from shared.auth import (google_login_url, google_exchange_code,
                         hash_password, check_password,
                         login_user, logout_user, current_user)
from shared.config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user():
        return redirect(url_for('home.index'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user     = db.find_one('users', {'email': email})
        if user and check_password(password, user.get('password_hash', '')):
            login_user(user, 'customer')
            return redirect(url_for('home.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('customer/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user():
        return redirect(url_for('home.index'))
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        phone    = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        if not all([name, email, phone, password]):
            flash('All fields are required.', 'danger')
            return render_template('customer/register.html')
        if db.find_one('users', {'email': email}):
            flash('Email already registered.', 'warning')
            return render_template('customer/register.html')
        user = db.insert_one('users', {
            'name': name, 'email': email, 'phone': phone,
            'password_hash': hash_password(password),
            'avatar': '', 'wallet': 0.0, 'loyalty_points': 0,
            'status': 'active', 'auth_provider': 'email',
        })
        login_user(user, 'customer')
        flash(f'Welcome to E-TukTukGo, {name}! 🛺', 'success')
        return redirect(url_for('home.index'))
    return render_template('customer/register.html')

@auth_bp.route('/google')
def google_login():
    return redirect(google_login_url(Config.GOOGLE_REDIRECT_URI_CLIENT, state='customer'))

@auth_bp.route('/google/callback')
def google_callback():
    code  = request.args.get('code')
    error = request.args.get('error')
    if error or not code:
        flash('Google login failed.', 'danger')
        return redirect(url_for('auth.login'))
    user_info = google_exchange_code(code, Config.GOOGLE_REDIRECT_URI_CLIENT)
    if not user_info or not user_info.get('email'):
        flash('Could not retrieve Google account info.', 'danger')
        return redirect(url_for('auth.login'))
    email = user_info['email'].lower()
    user  = db.find_one('users', {'email': email})
    if not user:
        user = db.insert_one('users', {
            'name': user_info.get('name', ''), 'email': email, 'phone': '',
            'password_hash': '', 'avatar': user_info.get('picture', ''),
            'wallet': 0.0, 'loyalty_points': 0,
            'status': 'active', 'auth_provider': 'google',
        })
    else:
        db.update_one('users', {'email': email},
                      {'avatar': user_info.get('picture', user.get('avatar', ''))})
        user = db.find_one('users', {'email': email})
    login_user(user, 'customer')
    # If phone missing, redirect to complete profile
    if not user.get('phone'):
        flash('Welcome! Please complete your profile.', 'info')
        return redirect(url_for('profile.edit_profile'))
    flash(f'Welcome, {user["name"]}! 🛺', 'success')
    return redirect(url_for('home.index'))

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
