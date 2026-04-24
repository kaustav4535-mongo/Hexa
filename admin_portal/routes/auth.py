import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, session)
from shared import db
from shared.auth import hash_password, check_password

admin_auth_bp = Blueprint('admin_auth', __name__)

def _admin_login(admin):
    session['admin_id']    = admin['_id']
    session['admin_name']  = admin.get('name', '')
    session['admin_email'] = admin.get('email', '')
    session['admin_role']  = admin.get('role', 'admin')
    session.permanent      = True

def current_admin():
    if session.get('admin_id'):
        return db.find_one('admins', {'_id': session['admin_id']})
    return None

@admin_auth_bp.route('/')
def root():
    if current_admin():
        return redirect(url_for('admin_dash.dashboard'))
    return redirect(url_for('admin_auth.login'))

@admin_auth_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    if current_admin():
        return redirect(url_for('admin_dash.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        admin    = db.find_one('admins', {'email': email})

        if admin and check_password(password, admin.get('password_hash', '')):
            _admin_login(admin)
            flash(f'Welcome, {admin["name"]}! 👑', 'success')
            return redirect(url_for('admin_dash.dashboard'))
        flash('Invalid credentials.', 'danger')

    return render_template('admin/login.html')

@admin_auth_bp.route('/auth/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin_auth.login'))
