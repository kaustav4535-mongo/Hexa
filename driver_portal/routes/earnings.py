import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash
from functools import wraps
from shared import db
from datetime import datetime

driver_earnings_bp = Blueprint('driver_earnings', __name__)

def driver_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'driver' or not session.get('user_id'):
            return redirect(url_for('driver_auth.login'))
        return f(*args, **kwargs)
    return decorated

def get_driver():
    uid = session.get('user_id', '')
    return db.find_one('drivers', {'_id': uid}) if uid else None

# ── Earnings overview ─────────────────────────────────────────────────────────
@driver_earnings_bp.route('/')
@driver_required
def earnings():
    driver = get_driver()
    if not driver:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('driver_auth.login'))

    bookings = db.find('bookings', {'driver_id': driver['_id'], 'status': 'completed'})
    bookings.sort(key=lambda b: b.get('created_at', ''), reverse=True)

    weekly = {}
    for b in bookings:
        day = b.get('created_at', '')[:10]
        if day:
            weekly[day] = weekly.get(day, 0) + max(0.0, float(b.get('fare', 0)) - 2.0)
    weekly_sorted = sorted(weekly.items())[-7:]
    total_earn = sum(max(0.0, float(b.get('fare', 0)) - 2.0) for b in bookings)

    withdrawals = db.find('withdrawals', {'driver_id': driver['_id']})
    withdrawals.sort(key=lambda w: w.get('created_at', ''), reverse=True)

    return render_template('driver/earnings.html',
                           driver=driver,
                           bookings=bookings,
                           weekly=weekly_sorted,
                           total_earn=total_earn,
                           withdrawals=withdrawals)

# ── Bank / UPI details ────────────────────────────────────────────────────────
@driver_earnings_bp.route('/bank-details', methods=['GET', 'POST'])
@driver_required
def bank_details():
    driver = get_driver()
    if not driver:
        session.clear()
        return redirect(url_for('driver_auth.login'))

    if request.method == 'POST':
        payout_method = request.form.get('payout_method', 'upi')
        updates = {'payout_method': payout_method}

        if payout_method == 'upi':
            upi = request.form.get('upi_id', '').strip()
            if not upi or '@' not in upi:
                flash('Please enter a valid UPI ID (e.g. name@paytm).', 'danger')
                withdrawals = db.find('withdrawals', {'driver_id': driver['_id']})
                return render_template('driver/bank_details.html', driver=driver, withdrawals=withdrawals)
            updates['upi_id']          = upi
            updates['bank_account_no'] = ''
            updates['bank_ifsc']       = ''
        else:
            acc_no = request.form.get('bank_account_no', '').strip()
            ifsc   = request.form.get('bank_ifsc', '').strip().upper()
            if not acc_no or not ifsc:
                flash('Bank account number and IFSC are required.', 'danger')
                withdrawals = db.find('withdrawals', {'driver_id': driver['_id']})
                return render_template('driver/bank_details.html', driver=driver, withdrawals=withdrawals)
            updates['bank_account_no'] = acc_no
            updates['bank_ifsc']       = ifsc
            updates['upi_id']          = ''

        # Clear stale Razorpay IDs so they get recreated with new details
        updates['rzp_contact_id']      = ''
        updates['rzp_fund_account_id'] = ''

        db.update_one('drivers', {'_id': driver['_id']}, updates)
        flash('Payment details saved. You can now request withdrawals.', 'success')
        return redirect(url_for('driver_earnings.earnings'))

    withdrawals = db.find('withdrawals', {'driver_id': driver['_id']})
    withdrawals.sort(key=lambda w: w.get('created_at', ''), reverse=True)
    return render_template('driver/bank_details.html', driver=driver, withdrawals=withdrawals)

# ── Request withdrawal ────────────────────────────────────────────────────────
@driver_earnings_bp.route('/request-withdrawal', methods=['POST'])
@driver_required
def request_withdrawal():
    driver = get_driver()
    if not driver:
        return jsonify({'success': False, 'error': 'Session expired'}), 401

    wallet = float(driver.get('wallet', 0) or 0)
    if wallet < 100:
        return jsonify({'success': False,
                        'error': f'Minimum withdrawal is ₹100. Your balance: ₹{wallet:.2f}'}), 400

    payout_method = driver.get('payout_method', '')
    upi_id        = driver.get('upi_id', '')
    bank_acc      = driver.get('bank_account_no', '')

    if not payout_method or (not upi_id and not bank_acc):
        return jsonify({'success': False,
                        'error': 'Please save your bank/UPI details first.'}), 400

    existing = db.find_one('withdrawals', {'driver_id': driver['_id'], 'status': 'pending'})
    if existing:
        return jsonify({'success': False,
                        'error': 'You already have a pending withdrawal request.'}), 400

    data   = request.get_json() or {}
    amount = float(data.get('amount', wallet) or wallet)
    amount = min(round(amount, 2), wallet)
    if amount < 100:
        return jsonify({'success': False, 'error': 'Minimum ₹100 per withdrawal.'}), 400

    db.insert_one('withdrawals', {
        'driver_id':       driver['_id'],
        'driver_name':     driver.get('name', ''),
        'driver_email':    driver.get('email', ''),
        'amount':          amount,
        'payout_method':   payout_method,
        'upi_id':          upi_id,
        'bank_account_no': bank_acc,
        'bank_ifsc':       driver.get('bank_ifsc', ''),
        'status':          'pending',
        'rzp_payout_id':   '',
        'note':            '',
    })

    return jsonify({'success': True,
                    'message': f'Withdrawal of ₹{amount:.2f} requested. Admin will process within 24 hours.'})

# ── Summary API ───────────────────────────────────────────────────────────────
@driver_earnings_bp.route('/api/summary')
@driver_required
def summary_api():
    driver = get_driver()
    if not driver:
        return jsonify({'error': 'Session expired'}), 401
    bookings = db.find('bookings', {'driver_id': driver['_id'], 'status': 'completed'})
    today    = datetime.utcnow().strftime('%Y-%m-%d')
    today_r  = [b for b in bookings if b.get('created_at', '')[:10] == today]
    today_e  = sum(max(0.0, float(b.get('fare', 0)) - 2.0) for b in today_r)
    return jsonify({
        'today_rides':    len(today_r),
        'today_earnings': round(today_e, 2),
        'total_rides':    driver.get('total_rides', 0) or 0,
        'total_earnings': round(driver.get('total_earnings', 0.0) or 0.0, 2),
        'wallet':         round(driver.get('wallet', 0.0) or 0.0, 2),
        'rating':         driver.get('rating', 5.0) or 5.0,
    })
