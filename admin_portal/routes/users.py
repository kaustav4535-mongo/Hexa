import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from admin_portal.utils import admin_required
from shared import db

admin_users_bp = Blueprint('admin_users', __name__)

@admin_users_bp.route('/')
@admin_required
def users_list():
    search = request.args.get('q', '').strip().lower()
    status = request.args.get('status', '')
    users  = db.find('users')

    if search:
        users = [u for u in users if
                 search in u.get('name','').lower() or
                 search in u.get('email','').lower() or
                 search in u.get('phone','')]
    if status:
        users = [u for u in users if u.get('status') == status]

    users.sort(key=lambda u: u.get('created_at', ''), reverse=True)
    return render_template('admin/users.html', users=users, search=search, status_filter=status)

@admin_users_bp.route('/<user_id>')
@admin_required
def user_detail(user_id):
    user     = db.find_one('users', {'_id': user_id})
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_users.users_list'))
    bookings = db.find('bookings', {'customer_id': user_id})
    bookings.sort(key=lambda b: b.get('created_at', ''), reverse=True)
    return render_template('admin/user_detail.html', user=user, bookings=bookings)

@admin_users_bp.route('/<user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_status(user_id):
    user = db.find_one('users', {'_id': user_id})
    if not user:
        return jsonify({'error': 'Not found'}), 404
    new = 'suspended' if user.get('status') == 'active' else 'active'
    db.update_one('users', {'_id': user_id}, {'status': new})
    return jsonify({'success': True, 'status': new})

@admin_users_bp.route('/<user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    db.delete_one('users', {'_id': user_id})
    flash('User deleted.', 'success')
    return redirect(url_for('admin_users.users_list'))

@admin_users_bp.route('/<user_id>/adjust-wallet', methods=['POST'])
@admin_required
def adjust_wallet(user_id):
    amount = float(request.form.get('amount', 0))
    user   = db.find_one('users', {'_id': user_id})
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_users.users_list'))
    new_bal = round(float(user.get('wallet', 0)) + amount, 2)
    db.update_one('users', {'_id': user_id}, {'wallet': new_bal})
    flash(f'Wallet adjusted by ₹{amount:+.2f}. New balance: ₹{new_bal}', 'success')
    return redirect(url_for('admin_users.user_detail', user_id=user_id))
