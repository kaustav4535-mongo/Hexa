import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, jsonify, session, redirect, url_for, flash
from admin_portal.utils import admin_required, current_admin
from shared import db
from shared.config import Config
COMMISSION = Config.PLATFORM_COMMISSION

admin_dash_bp = Blueprint('admin_dash', __name__)

@admin_dash_bp.route('/')
@admin_required
def dashboard():
    admin = current_admin()
    if not admin:
        session.clear()
        flash('Session expired.', 'warning')
        return redirect(url_for('admin_auth.login'))

    total_users      = db.count('users')
    total_drivers    = db.count('drivers')
    all_payments     = db.find('payments')
    active_drivers   = db.count('drivers', {'status': 'online'})
    pending_drivers  = db.count('drivers', {'approval': 'pending'})
    active_rides     = db.count('bookings', {'status': 'in_progress'})
    open_bookings    = db.count('bookings', {'status': 'open'})
    pending_bookings = db.count('bookings', {'status': 'pending'}) + open_bookings

    total_revenue = sum(float(p.get('amount', 0)) for p in all_payments
                        if p.get('status') != 'payout')
    # ₹2 flat commission per ride
    all_commissions = db.find('commissions')
    platform_cut    = sum(float(c.get('commission', COMMISSION)) for c in all_commissions)

    all_bookings = db.find('bookings')
    all_bookings.sort(key=lambda b: b.get('created_at', ''), reverse=True)

    pending_drv = db.find('drivers', {'approval': 'pending'})
    pending_drv.sort(key=lambda d: d.get('created_at', ''), reverse=True)

    rev_by_day = {}
    for p in all_payments:
        if p.get('status') == 'payout':
            continue
        day = p.get('created_at', '')[:10]
        if day:
            rev_by_day[day] = rev_by_day.get(day, 0) + float(p.get('amount', 0))
    rev_chart = sorted(rev_by_day.items())[-7:]

    return render_template('admin/dashboard.html',
        admin=admin,
        total_users=total_users,
        total_drivers=total_drivers,
        active_drivers=active_drivers,
        pending_drivers=pending_drivers,
        active_rides=active_rides,
        pending_bookings=pending_bookings,
        open_bookings=open_bookings,
        total_revenue=total_revenue,
        platform_cut=platform_cut,
        recent_bookings=all_bookings[:8],
        pending_drv=pending_drv[:5],
        rev_chart=rev_chart,
    )

@admin_dash_bp.route('/api/stats')
@admin_required
def stats_api():
    return jsonify({
        'active_drivers':   db.count('drivers', {'status': 'online'}),
        'active_rides':     db.count('bookings', {'status': 'in_progress'}),
        'pending_bookings': db.count('bookings', {'status': 'pending'}),
        'total_users':      db.count('users'),
    })
