from functools import wraps
from flask import session, redirect, url_for, flash
from shared import db

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Admin login required.', 'warning')
            return redirect(url_for('admin_auth.login'))
        # Validate session is still valid in DB
        admin = db.find_one('admins', {'_id': session['admin_id']})
        if not admin:
            session.clear()
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('admin_auth.login'))
        return f(*args, **kwargs)
    return decorated

def current_admin():
    aid = session.get('admin_id')
    if not aid:
        return None
    admin = db.find_one('admins', {'_id': aid})
    return admin  # may be None if DB was wiped — callers must check
