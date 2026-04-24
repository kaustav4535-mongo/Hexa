from flask import Blueprint, render_template, jsonify, request
from admin_portal.utils import admin_required
from shared import db
from shared.config import Config

admin_payments_bp = Blueprint('admin_payments', __name__)

COMMISSION = Config.PLATFORM_COMMISSION  # ₹2

@admin_payments_bp.route('/')
@admin_required
def payments_list():
    payments = db.find('payments')
    payments.sort(key=lambda p: p.get('created_at',''), reverse=True)

    total_revenue  = sum(float(p.get('amount',0)) for p in payments
                         if p.get('status') not in ('payout',))
    total_payouts  = sum(float(p.get('amount',0)) for p in payments
                         if p.get('status') == 'payout')

    # ── Commission stats ──────────────────────────────────────────────────────
    commissions    = db.find('commissions')
    total_comm     = sum(float(c.get('commission', COMMISSION)) for c in commissions)
    cash_comm_pend = sum(float(c.get('commission', COMMISSION)) for c in commissions
                         if c.get('method') == 'cash' and c.get('status') == 'pending')
    online_comm    = sum(float(c.get('commission', COMMISSION)) for c in commissions
                         if c.get('method') == 'online')

    # ── Commission by driver (for settlement) ─────────────────────────────────
    cash_by_driver = {}
    for com in commissions:
        if com.get('method') == 'cash' and com.get('status') == 'pending':
            did  = com.get('driver_id','')
            name = com.get('driver_name','?')
            if did not in cash_by_driver:
                cash_by_driver[did] = {'name': name, 'amount': 0.0, 'rides': 0}
            cash_by_driver[did]['amount'] += float(com.get('commission', COMMISSION))
            cash_by_driver[did]['rides']  += 1

    return render_template('admin/payments.html',
                           payments=payments,
                           total_revenue=total_revenue,
                           total_payouts=total_payouts,
                           platform_commission=COMMISSION,
                           total_comm=round(total_comm, 2),
                           cash_comm_pending=round(cash_comm_pend, 2),
                           online_comm=round(online_comm, 2),
                           commissions=commissions[:20],
                           cash_pending_by_driver=list(cash_by_driver.values()))


@admin_payments_bp.route('/commissions')
@admin_required
def commissions_list():
    """Full commission ledger."""
    method = request.args.get('method', '')
    status = request.args.get('status', '')
    comms  = db.find('commissions')
    if method: comms = [c for c in comms if c.get('method') == method]
    if status: comms = [c for c in comms if c.get('status') == status]
    comms.sort(key=lambda c: c.get('created_at',''), reverse=True)
    return render_template('admin/commissions.html',
                           commissions=comms,
                           method_filter=method, status_filter=status,
                           total=sum(float(c.get('commission',2)) for c in comms),
                           platform_commission=COMMISSION)


@admin_payments_bp.route('/commissions/<comm_id>/settle', methods=['POST'])
@admin_required
def settle_commission(comm_id):
    """Mark a pending cash commission as settled."""
    from flask import request as req
    db.update_one('commissions', {'_id': comm_id}, {'status': 'settled'})
    return jsonify({'success': True})


@admin_payments_bp.route('/api/stats')
@admin_required
def payment_stats_api():
    comms = db.find('commissions')
    return jsonify({
        'total_commission':       round(sum(float(c.get('commission',2)) for c in comms), 2),
        'online_commission':      round(sum(float(c.get('commission',2)) for c in comms if c.get('method')=='online'), 2),
        'cash_pending':           round(sum(float(c.get('commission',2)) for c in comms if c.get('method')=='cash' and c.get('status')=='pending'), 2),
        'total_rides_with_commission': len(comms),
    })
