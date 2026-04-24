import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from admin_portal.utils import admin_required, current_admin
from shared import db
from shared.auth import hash_password, check_password
import json
from shared.cloudinary_upload import upload_avatar, validate_image

admin_settings_bp = Blueprint('admin_settings', __name__)

@admin_settings_bp.route('/')
@admin_required
def settings():
    admin = current_admin()
    if not admin:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('admin_auth.login'))
    return render_template('admin/settings.html', admin=admin)

@admin_settings_bp.route('/change-password', methods=['POST'])
@admin_required
def change_password():
    admin = current_admin()
    if not admin:
        session.clear()
        return redirect(url_for('admin_auth.login'))
    old_pw = request.form.get('old_password', '')
    new_pw = request.form.get('new_password', '')
    if not check_password(old_pw, admin.get('password_hash', '')):
        flash('Current password incorrect.', 'danger')
        return redirect(url_for('admin_settings.settings'))
    db.update_one('admins', {'_id': admin['_id']},
                  {'password_hash': hash_password(new_pw)})
    flash('Password updated successfully.', 'success')
    return redirect(url_for('admin_settings.settings'))

@admin_settings_bp.route('/export-db')
@admin_required
def export_db():
    from flask import Response
    data = db.get_all_collections()
    return Response(
        json.dumps(data, indent=2, default=str),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment;filename=etuktuk_db_export.json'}
    )

@admin_settings_bp.route('/create-admin', methods=['POST'])
@admin_required
def create_admin():
    name  = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    pw    = request.form.get('password', '')
    if not all([name, email, pw]):
        flash('All fields required.', 'danger')
        return redirect(url_for('admin_settings.settings'))
    if db.find_one('admins', {'email': email}):
        flash('Admin with this email already exists.', 'warning')
        return redirect(url_for('admin_settings.settings'))
    db.insert_one('admins', {
        'name':          name,
        'email':         email,
        'password_hash': hash_password(pw),
        'role':          'admin',
        'status':        'active',
    })
    flash(f'Sub-admin {name} created successfully.', 'success')
    return redirect(url_for('admin_settings.settings'))


# ── Upload admin profile picture ────────────────────────────────────────────
@admin_settings_bp.route('/upload-avatar', methods=['POST'])
@admin_required
def upload_avatar_route():
    from flask import jsonify
    admin = current_admin()
    if not admin:
        return jsonify({'success': False, 'error': 'Session expired'}), 401

    f = request.files.get('avatar')
    ok, err = validate_image(f)
    if not ok:
        return jsonify({'success': False, 'error': err}), 400

    url = upload_avatar(f.stream, f.filename, admin['_id'])
    if not url:
        return jsonify({'success': False,
                        'error': 'Upload not available in local development (Termux has no internet). This will work automatically when deployed on Render.com.'}), 500

    db.update_one('admins', {'_id': admin['_id']}, {'avatar': url})
    session['avatar'] = url
    return jsonify({'success': True, 'url': url})
