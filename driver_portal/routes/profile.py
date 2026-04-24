import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, session, jsonify)
from functools import wraps
from shared import db
from shared.auth import hash_password, check_password
from shared.cloudinary_upload import upload_avatar, upload_id_doc, validate_image, validate_doc

driver_profile_bp = Blueprint('driver_profile', __name__)

def driver_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'driver' or not session.get('user_id'):
            return redirect(url_for('driver_auth.login'))
        return f(*args, **kwargs)
    return decorated

def get_driver():
    uid = session.get('user_id', '')
    if not uid: return None
    return db.find_one('drivers', {'_id': uid})

def profile_complete(driver):
    if not driver: return False
    return all(str(driver.get(f, '') or '').strip()
               for f in ['phone', 'vehicle_number', 'license_no'])

# ── Setup (mandatory after Google login) ────────────────────────────────────
@driver_profile_bp.route('/setup', methods=['GET', 'POST'])
@driver_required
def setup():
    driver = get_driver()
    if not driver:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('driver_auth.login'))
    if request.method == 'POST':
        phone      = request.form.get('phone', '').strip()
        vehicle    = request.form.get('vehicle_number', '').strip().upper()
        license_no = request.form.get('license_no', '').strip().upper()
        name       = request.form.get('name', driver.get('name', '')).strip()
        if not all([phone, vehicle, license_no, name]):
            flash('All fields are required to activate your account.', 'danger')
            return render_template('driver/profile_setup.html', driver=driver)
        db.update_one('drivers', {'_id': driver['_id']}, {
            'name': name, 'phone': phone,
            'vehicle_number': vehicle, 'license_no': license_no,
        })
        session['user_name'] = name
        flash('Profile complete! Pending admin approval.', 'success')
        return redirect(url_for('driver_dash.dashboard'))
    return render_template('driver/profile_setup.html', driver=driver)

# ── View profile ─────────────────────────────────────────────────────────────
@driver_profile_bp.route('/')
@driver_required
def profile():
    driver = get_driver()
    if not driver:
        session.clear()
        flash('Session expired.', 'warning')
        return redirect(url_for('driver_auth.login'))
    return render_template('driver/profile.html', driver=driver)

# ── Edit profile ─────────────────────────────────────────────────────────────
@driver_profile_bp.route('/edit', methods=['GET', 'POST'])
@driver_required
def edit_profile():
    driver = get_driver()
    if not driver:
        session.clear()
        return redirect(url_for('driver_auth.login'))
    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        phone      = request.form.get('phone', '').strip()
        vehicle    = request.form.get('vehicle_number', '').strip().upper()
        license_no = request.form.get('license_no', '').strip().upper()
        if not name:
            flash('Name is required.', 'danger')
            return render_template('driver/edit_profile.html', driver=driver)
        db.update_one('drivers', {'_id': driver['_id']}, {
            'name': name, 'phone': phone,
            'vehicle_number': vehicle, 'license_no': license_no,
        })
        session['user_name'] = name
        flash('Profile updated.', 'success')
        return redirect(url_for('driver_profile.profile'))
    return render_template('driver/edit_profile.html', driver=driver)

# ── Upload profile picture ───────────────────────────────────────────────────
@driver_profile_bp.route('/upload-avatar', methods=['POST'])
@driver_required
def upload_avatar_route():
    driver = get_driver()
    if not driver:
        return jsonify({'success': False, 'error': 'Session expired'}), 401

    f = request.files.get('avatar')
    ok, err = validate_image(f)
    if not ok:
        return jsonify({'success': False, 'error': err}), 400

    url = upload_avatar(f.stream, f.filename, driver['_id'])
    if not url:
        return jsonify({'success': False,
                        'error': 'Upload not available in local development (Termux has no internet). This will work automatically when deployed on Render.com.'}), 500

    db.update_one('drivers', {'_id': driver['_id']}, {'avatar': url})
    session['avatar'] = url
    return jsonify({'success': True, 'url': url})

# ── Upload identity document ─────────────────────────────────────────────────
@driver_profile_bp.route('/upload-id-doc', methods=['POST'])
@driver_required
def upload_id_doc_route():
    driver = get_driver()
    if not driver:
        return jsonify({'success': False, 'error': 'Session expired'}), 401

    f       = request.files.get('id_doc')
    id_type = request.form.get('id_type', 'aadhaar').strip()

    ok, err = validate_doc(f)
    if not ok:
        return jsonify({'success': False, 'error': err}), 400

    url = upload_id_doc(f.stream, f.filename, driver['_id'], 'driver')
    if not url:
        return jsonify({'success': False,
                        'error': 'Upload not available in local development (Termux has no internet). This will work automatically when deployed on Render.com.'}), 500

    db.update_one('drivers', {'_id': driver['_id']}, {
        'id_doc_url':  url,
        'id_doc_type': id_type,
    })
    return jsonify({'success': True, 'url': url})

# ── Change password ──────────────────────────────────────────────────────────
@driver_profile_bp.route('/change-password', methods=['POST'])
@driver_required
def change_password():
    driver = get_driver()
    if not driver: return redirect(url_for('driver_auth.login'))
    if driver.get('auth_provider') == 'google':
        flash('Google account — no password to change.', 'info')
        return redirect(url_for('driver_profile.profile'))
    old_pw = request.form.get('old_password', '')
    new_pw = request.form.get('new_password', '')
    if not check_password(old_pw, driver.get('password_hash', '')):
        flash('Current password incorrect.', 'danger')
        return redirect(url_for('driver_profile.profile'))
    db.update_one('drivers', {'_id': driver['_id']},
                  {'password_hash': hash_password(new_pw)})
    flash('Password updated.', 'success')
    return redirect(url_for('driver_profile.profile'))
