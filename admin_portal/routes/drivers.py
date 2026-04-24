import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from admin_portal.utils import admin_required
from shared import db

admin_drivers_bp = Blueprint('admin_drivers', __name__)

@admin_drivers_bp.route('/')
@admin_required
def drivers_list():
    search   = request.args.get('q', '').strip().lower()
    approval = request.args.get('approval', '')
    status   = request.args.get('status', '')
    drivers  = db.find('drivers')

    if search:
        drivers = [d for d in drivers if
                   search in d.get('name','').lower() or
                   search in d.get('email','').lower() or
                   search in d.get('vehicle_number','').lower()]
    if approval:
        drivers = [d for d in drivers if d.get('approval') == approval]
    if status:
        drivers = [d for d in drivers if d.get('status') == status]

    drivers.sort(key=lambda d: d.get('created_at', ''), reverse=True)
    return render_template('admin/drivers.html',
                           drivers=drivers, search=search,
                           approval_filter=approval, status_filter=status)

@admin_drivers_bp.route('/<driver_id>')
@admin_required
def driver_detail(driver_id):
    driver = db.find_one('drivers', {'_id': driver_id})
    if not driver:
        flash('Driver not found.', 'danger')
        return redirect(url_for('admin_drivers.drivers_list'))
    rides  = db.find('bookings', {'driver_id': driver_id})
    rides.sort(key=lambda b: b.get('created_at', ''), reverse=True)
    zones = db.find('zones')
    return render_template('admin/driver_detail.html',
                           driver=driver, rides=rides, zones=zones)

@admin_drivers_bp.route('/<driver_id>/approve', methods=['POST'])
@admin_required
def approve(driver_id):
    db.update_one('drivers', {'_id': driver_id},
                  {'approval': 'approved', 'status': 'offline'})
    flash('Driver approved. They can now go online.', 'success')
    return redirect(url_for('admin_drivers.driver_detail', driver_id=driver_id))

@admin_drivers_bp.route('/<driver_id>/reject', methods=['POST'])
@admin_required
def reject(driver_id):
    db.update_one('drivers', {'_id': driver_id},
                  {'approval': 'rejected', 'status': 'offline'})
    flash('Driver application rejected.', 'warning')
    return redirect(url_for('admin_drivers.driver_detail', driver_id=driver_id))

@admin_drivers_bp.route('/<driver_id>/suspend', methods=['POST'])
@admin_required
def suspend(driver_id):
    db.update_one('drivers', {'_id': driver_id},
                  {'status': 'suspended', 'approval': 'rejected'})
    flash('Driver suspended.', 'danger')
    return redirect(url_for('admin_drivers.driver_detail', driver_id=driver_id))

@admin_drivers_bp.route('/<driver_id>/reinstate', methods=['POST'])
@admin_required
def reinstate(driver_id):
    db.update_one('drivers', {'_id': driver_id},
                  {'status': 'offline', 'approval': 'approved'})
    flash('Driver reinstated.', 'success')
    return redirect(url_for('admin_drivers.driver_detail', driver_id=driver_id))

@admin_drivers_bp.route('/<driver_id>/payout', methods=['POST'])
@admin_required
def payout(driver_id):
    driver = db.find_one('drivers', {'_id': driver_id})
    if not driver:
        return jsonify({'error': 'Not found'}), 404
    amount = float(driver.get('wallet', 0))
    if amount <= 0:
        flash('No balance to pay out.', 'warning')
        return redirect(url_for('admin_drivers.driver_detail', driver_id=driver_id))
    db.update_one('drivers', {'_id': driver_id}, {'wallet': 0.0})
    db.insert_one('payments', {
        'booking_id':          '',
        'razorpay_order_id':   '',
        'razorpay_payment_id': f'manual_payout_{driver_id[:8]}',
        'amount':              amount,
        'status':              'payout',
        'note':                f'Admin payout to driver {driver.get("name")}',
    })
    flash(f'Payout of ₹{amount:.2f} recorded for {driver["name"]}.', 'success')
    return redirect(url_for('admin_drivers.driver_detail', driver_id=driver_id))

@admin_drivers_bp.route('/api/bulk-approve', methods=['POST'])
@admin_required
def bulk_approve():
    ids = request.get_json().get('ids', [])
    for did in ids:
        db.update_one('drivers', {'_id': did},
                      {'approval': 'approved', 'status': 'offline'})
    return jsonify({'success': True, 'count': len(ids)})

# ── Withdrawal Management ─────────────────────────────────────────────────────

@admin_drivers_bp.route('/withdrawals')
@admin_required
def withdrawals_list():
    """Admin view of all pending + processed driver withdrawals."""
    status = request.args.get('status', 'pending')
    all_w  = db.find('withdrawals')
    if status != 'all':
        all_w = [w for w in all_w if w.get('status') == status]
    all_w.sort(key=lambda w: w.get('created_at', ''), reverse=True)
    pending_count = len([w for w in db.find('withdrawals') if w.get('status') == 'pending'])
    return render_template('admin/withdrawals.html',
                           withdrawals=all_w,
                           status_filter=status,
                           pending_count=pending_count)

@admin_drivers_bp.route('/withdrawals/<wid>/process', methods=['POST'])
@admin_required
def process_withdrawal(wid):
    """
    Admin processes a withdrawal — triggers Razorpay X payout.
    If Razorpay X not set up, marks as manual payout.
    """
    from shared.payments import (create_razorpay_contact,
                                  create_fund_account_upi,
                                  create_fund_account_bank,
                                  trigger_payout)
    w = db.find_one('withdrawals', {'_id': wid})
    if not w:
        flash('Withdrawal not found.', 'danger')
        return redirect(url_for('admin_drivers.withdrawals_list'))

    driver = db.find_one('drivers', {'_id': w['driver_id']})
    if not driver:
        flash('Driver not found.', 'danger')
        return redirect(url_for('admin_drivers.withdrawals_list'))

    amount = float(w.get('amount', 0))
    wallet = float(driver.get('wallet', 0))

    if amount > wallet:
        flash(f'Insufficient wallet balance (₹{wallet:.2f}).', 'danger')
        return redirect(url_for('admin_drivers.withdrawals_list'))

    from shared.config import Config
    rzp_payout_id = ''

    # Try Razorpay X payout if configured
    if Config.RAZORPAY_X_ACCOUNT:
        # Step 1: Create or reuse Razorpay Contact
        contact_id = driver.get('rzp_contact_id', '')
        if not contact_id:
            contact = create_razorpay_contact(driver)
            if contact:
                contact_id = contact['id']
                db.update_one('drivers', {'_id': driver['_id']}, {'rzp_contact_id': contact_id})

        # Step 2: Create Fund Account
        fund_id = driver.get('rzp_fund_account_id', '')
        if contact_id and not fund_id:
            if w.get('payout_method') == 'upi' and w.get('upi_id'):
                fa = create_fund_account_upi(contact_id, w['upi_id'])
            else:
                fa = create_fund_account_bank(contact_id, w.get('bank_account_no',''),
                                               w.get('bank_ifsc',''), driver.get('name',''))
            if fa:
                fund_id = fa['id']
                db.update_one('drivers', {'_id': driver['_id']}, {'rzp_fund_account_id': fund_id})

        # Step 3: Trigger payout
        if fund_id:
            payout = trigger_payout(fund_id, amount, driver.get('name',''), driver['_id'])
            if payout:
                rzp_payout_id = payout.get('id', '')

    # Deduct from wallet and mark withdrawal
    new_wallet = max(0.0, wallet - amount)
    db.update_one('drivers', {'_id': driver['_id']}, {'wallet': round(new_wallet, 2)})
    db.update_one('withdrawals', {'_id': wid}, {
        'status':       'completed',
        'rzp_payout_id': rzp_payout_id,
        'note':         f'Processed by admin. Razorpay payout: {rzp_payout_id or "manual"}',
    })
    db.insert_one('payments', {
        'booking_id':          '',
        'razorpay_order_id':   '',
        'razorpay_payment_id': rzp_payout_id or f'manual_payout_{wid[:8]}',
        'amount':              amount,
        'status':              'payout',
        'note':                f'Withdrawal to {driver.get("name")} via {w.get("payout_method","?")}',
    })

    method_str = f"Razorpay X ({rzp_payout_id})" if rzp_payout_id else "manual (no Razorpay X)"
    flash(f'₹{amount:.2f} paid to {driver["name"]} via {method_str}.', 'success')
    return redirect(url_for('admin_drivers.withdrawals_list'))

@admin_drivers_bp.route('/withdrawals/<wid>/reject', methods=['POST'])
@admin_required
def reject_withdrawal(wid):
    note = request.form.get('note', 'Rejected by admin')
    w    = db.find_one('withdrawals', {'_id': wid})
    if not w:
        flash('Not found.', 'danger')
        return redirect(url_for('admin_drivers.withdrawals_list'))
    db.update_one('withdrawals', {'_id': wid}, {'status': 'rejected', 'note': note})
    flash('Withdrawal rejected.', 'warning')
    return redirect(url_for('admin_drivers.withdrawals_list'))

@admin_drivers_bp.route('/<driver_id>/assign-zone', methods=['POST'])
@admin_required
def assign_zone(driver_id):
    """Assign driver to serve one or more zones."""
    home_zone = request.form.get('home_zone_id', '')
    extra_zones = request.form.getlist('extra_zone_ids')
    db.update_one('drivers', {'_id': driver_id}, {
        'home_zone_id':    home_zone,
        'served_zone_ids': extra_zones,
    })
    flash('Driver zone assignment updated.', 'success')
    return redirect(url_for('admin_drivers.driver_detail', driver_id=driver_id))
