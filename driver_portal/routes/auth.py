import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, session)
from shared import db
from shared.auth import (google_login_url, google_exchange_code,
                         hash_password, check_password)
from shared.config import Config

driver_auth_bp = Blueprint('driver_auth', __name__)

def _driver_login(driver):
    session['user_id']    = driver['_id']
    session['user_name']  = driver.get('name', '')
    session['user_email'] = driver.get('email', '')
    session['role']       = 'driver'
    session['avatar']     = driver.get('avatar', '')
    session.permanent     = True

def _profile_complete(driver):
    """Check all essential driver fields are filled."""
    required = ['phone', 'vehicle_number', 'license_no']
    return all(driver.get(f, '').strip() for f in required)

@driver_auth_bp.route('/')
def root():
    if session.get('role') == 'driver' and session.get('user_id'):
        return redirect(url_for('driver_dash.dashboard'))
    return redirect(url_for('driver_auth.login'))

@driver_auth_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    if session.get('role') == 'driver':
        return redirect(url_for('driver_dash.dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        driver   = db.find_one('drivers', {'email': email})
        if driver and check_password(password, driver.get('password_hash', '')):
            if driver.get('status') == 'suspended':
                flash('Your account has been suspended. Contact admin.', 'danger')
                return render_template('driver/login.html')
            _driver_login(driver)
            # Check profile completeness
            if not _profile_complete(driver):
                flash('Please complete your profile to continue.', 'warning')
                return redirect(url_for('driver_profile.setup'))
            flash(f'Welcome back, {driver["name"]}! 🛺', 'success')
            return redirect(url_for('driver_dash.dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('driver/login.html')

@driver_auth_bp.route('/auth/register', methods=['GET', 'POST'])
def register():
    if session.get('role') == 'driver':
        return redirect(url_for('driver_dash.dashboard'))
    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        email      = request.form.get('email', '').strip().lower()
        phone      = request.form.get('phone', '').strip()
        password   = request.form.get('password', '')
        vehicle    = request.form.get('vehicle_number', '').strip().upper()
        license_no = request.form.get('license_no', '').strip().upper()
        if not all([name, email, phone, password, vehicle, license_no]):
            flash('All fields are required.', 'danger')
            return render_template('driver/register.html')
        if db.find_one('drivers', {'email': email}):
            flash('Email already registered.', 'warning')
            return render_template('driver/register.html')
        driver = db.insert_one('drivers', {
            'name': name, 'email': email, 'phone': phone,
            'password_hash': hash_password(password),
            'vehicle_number': vehicle, 'license_no': license_no,
            'avatar': '', 'status': 'offline', 'approval': 'pending',
            'rating': 5.0, 'rating_count': 0, 'wallet': 0.0,
            'total_rides': 0, 'total_earnings': 0.0,
            'lat': 0.0, 'lng': 0.0, 'auth_provider': 'email',
        })
        _driver_login(driver)
        flash('Account created! Awaiting admin approval. 🛺', 'success')
        return redirect(url_for('driver_dash.dashboard'))
    return render_template('driver/register.html')

@driver_auth_bp.route('/auth/google')
def google_login():
    return redirect(google_login_url(Config.GOOGLE_REDIRECT_URI_OWNER, state='driver'))

@driver_auth_bp.route('/auth/google/callback')
def google_callback():
    code  = request.args.get('code')
    error = request.args.get('error')
    if error or not code:
        flash('Google login failed.', 'danger')
        return redirect(url_for('driver_auth.login'))
    user_info = google_exchange_code(code, Config.GOOGLE_REDIRECT_URI_OWNER)
    if not user_info or not user_info.get('email'):
        flash('Could not get Google account info.', 'danger')
        return redirect(url_for('driver_auth.login'))
    email  = user_info['email'].lower()
    driver = db.find_one('drivers', {'email': email})
    if not driver:
        # New Google driver — create with minimal info, force setup
        driver = db.insert_one('drivers', {
            'name': user_info.get('name', ''), 'email': email,
            'phone': '', 'password_hash': '',
            'vehicle_number': '', 'license_no': '',
            'avatar': user_info.get('picture', ''),
            'status': 'offline', 'approval': 'pending',
            'rating': 5.0, 'rating_count': 0, 'wallet': 0.0,
            'total_rides': 0, 'total_earnings': 0.0,
            'lat': 0.0, 'lng': 0.0, 'auth_provider': 'google',
        })
        _driver_login(driver)
        flash('Welcome! Please complete your driver profile to get started.', 'info')
        return redirect(url_for('driver_profile.setup'))
    else:
        db.update_one('drivers', {'email': email},
                      {'avatar': user_info.get('picture', driver.get('avatar', ''))})
        driver = db.find_one('drivers', {'email': email})
        _driver_login(driver)
        # Check if profile is complete
        if not _profile_complete(driver):
            flash('Please complete your profile to continue.', 'warning')
            return redirect(url_for('driver_profile.setup'))
    flash(f'Welcome back, {driver["name"]}! 🛺', 'success')
    return redirect(url_for('driver_dash.dashboard'))

@driver_auth_bp.route('/auth/logout')
def logout():
    if session.get('user_id') and session.get('role') == 'driver':
        db.update_one('drivers', {'_id': session['user_id']}, {'status': 'offline'})
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('driver_auth.login'))
