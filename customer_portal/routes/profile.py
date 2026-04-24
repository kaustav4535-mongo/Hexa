import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from shared import db
from shared.auth import login_required, current_user, hash_password, check_password
from shared.cloudinary_upload import upload_avatar, upload_id_doc, validate_image, validate_doc

profile_bp = Blueprint('profile', __name__)

def _get_full_user():
    user = current_user()
    if not user: return None
    full = db.find_one('users', {'_id': user['_id']})
    if not full: session.clear()
    return full

@profile_bp.route('/')
@login_required
def profile():
    full = _get_full_user()
    if not full:
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    bookings  = db.find('bookings', {'customer_id': full['_id']})
    completed = [b for b in bookings if b.get('status') == 'completed']
    return render_template('customer/profile.html',
                           user=full,
                           total_bookings=len(bookings),
                           completed_rides=len(completed))

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    full = _get_full_user()
    if not full:
        flash('Session expired.', 'warning')
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        name  = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        if not name or not phone:
            flash('Name and phone are required.', 'danger')
            return render_template('customer/edit_profile.html', user=full)
        db.update_one('users', {'_id': full['_id']}, {'name': name, 'phone': phone})
        session['user_name'] = name
        flash('Profile updated.', 'success')
        return redirect(url_for('profile.profile'))
    return render_template('customer/edit_profile.html', user=full)

# ── Upload profile picture ────────────────────────────────────────────────────
@profile_bp.route('/upload-avatar', methods=['POST'])
@login_required
def upload_avatar_route():
    full = _get_full_user()
    if not full:
        return jsonify({'success': False, 'error': 'Session expired'}), 401

    f = request.files.get('avatar')
    ok, err = validate_image(f)
    if not ok:
        return jsonify({'success': False, 'error': err}), 400

    url = upload_avatar(f.stream, f.filename, full['_id'])
    if not url:
        return jsonify({'success': False,
                        'error': 'Upload not available in local development (Termux has no internet). This will work automatically when deployed on Render.com.'}), 500

    db.update_one('users', {'_id': full['_id']}, {'avatar': url})
    session['avatar'] = url
    return jsonify({'success': True, 'url': url})

# ── Upload identity document ──────────────────────────────────────────────────
@profile_bp.route('/upload-id-doc', methods=['POST'])
@login_required
def upload_id_doc_route():
    full = _get_full_user()
    if not full:
        return jsonify({'success': False, 'error': 'Session expired'}), 401

    f       = request.files.get('id_doc')
    id_type = request.form.get('id_type', 'aadhaar').strip()

    ok, err = validate_doc(f)
    if not ok:
        return jsonify({'success': False, 'error': err}), 400

    url = upload_id_doc(f.stream, f.filename, full['_id'], 'customer')
    if not url:
        return jsonify({'success': False,
                        'error': 'Upload not available in local development (Termux has no internet). This will work automatically when deployed on Render.com.'}), 500

    db.update_one('users', {'_id': full['_id']}, {
        'id_doc_url':  url,
        'id_doc_type': id_type,
    })
    return jsonify({'success': True, 'url': url})

@profile_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    full = _get_full_user()
    if not full: return redirect(url_for('auth.login'))
    if full.get('auth_provider') == 'google':
        flash('Google account — no password to change.', 'info')
        return redirect(url_for('profile.profile'))
    old_pw = request.form.get('old_password', '')
    new_pw = request.form.get('new_password', '')
    if not check_password(old_pw, full.get('password_hash', '')):
        flash('Current password incorrect.', 'danger')
        return redirect(url_for('profile.profile'))
    db.update_one('users', {'_id': full['_id']}, {'password_hash': hash_password(new_pw)})
    flash('Password changed.', 'success')
    return redirect(url_for('profile.profile'))

@profile_bp.route('/wallet')
@login_required
def wallet():
    full = _get_full_user()
    if not full: return redirect(url_for('auth.login'))
    payments = db.find('payments', {})
    return render_template('customer/wallet.html', user=full, payments=payments)
