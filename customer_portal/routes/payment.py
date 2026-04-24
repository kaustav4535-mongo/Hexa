import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from shared import db
from shared.auth import login_required, current_user
from shared.payments import create_order, verify_payment, record_payment
from shared.config import Config

payment_bp = Blueprint('payment', __name__)

COMMISSION = Config.PLATFORM_COMMISSION  # ₹2

@payment_bp.route('/checkout/<booking_id>')
@login_required
def checkout(booking_id):
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('booking.my_bookings'))

    # In new flow: payment_locked=False after select_driver, or booking is 'confirmed'
    # Only block if still 'open' (no driver selected yet)
    if booking.get('status') == 'open':
        flash('Please select a driver first before paying.', 'info')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))

    if booking.get('payment_status') in ('paid', 'paid_cash'):
        flash('This booking is already paid.', 'info')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))

    # Check if customer wants to update amount before paying
    new_amount = request.args.get('amount')
    if new_amount:
        try:
            new_amount = float(new_amount)
            if new_amount >= 10:
                driver_earn = max(0.0, round(new_amount - COMMISSION, 2))
                db.update_one('bookings', {'_id': booking_id}, {
                    'fare':        round(new_amount, 2),
                    'driver_earn': driver_earn,
                })
                booking = db.find_one('bookings', {'_id': booking_id})
        except (ValueError, TypeError):
            pass

    fare        = float(booking.get('fare', 0))
    driver_earn = max(0.0, round(fare - COMMISSION, 2))

    return render_template('customer/checkout.html',
                           booking=booking,
                           driver_earn=driver_earn,
                           commission=COMMISSION,
                           rzp_key=Config.RAZORPAY_KEY_ID,
                           user=user)

@payment_bp.route('/create-order', methods=['POST'])
@login_required
def create_order_route():
    """Create Razorpay order for online payment."""
    user    = current_user()
    data    = request.get_json() or {}
    booking_id = data.get('booking_id', '')

    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    if booking.get('status') == 'open':
        return jsonify({'success': False, 'error': 'Please select a driver first'}), 400

    # Allow custom amount (customer can change their offer at payment time)
    custom_amount = float(data.get('amount', booking['fare']) or booking['fare'])
    if custom_amount < 10:
        return jsonify({'success': False, 'error': 'Minimum ₹10'}), 400

    # Update booking fare if changed
    if abs(custom_amount - float(booking['fare'])) > 0.01:
        driver_earn = max(0.0, round(custom_amount - COMMISSION, 2))
        db.update_one('bookings', {'_id': booking_id}, {
            'fare':        round(custom_amount, 2),
            'driver_earn': driver_earn,
        })

    order = create_order(
        amount_inr=custom_amount,
        booking_id=booking_id,
        notes={'customer': user['name'], 'email': user['email']}
    )
    db.update_one('bookings', {'_id': booking_id}, {
        'razorpay_order_id': order['id'],
        'payment_method':    'online',
    })
    return jsonify({'success': True, 'order_id': order['id'], 'amount': custom_amount})

@payment_bp.route('/verify', methods=['POST'])
@login_required
def verify():
    data = request.get_json() or request.form
    razorpay_order_id   = data.get('razorpay_order_id', '')
    razorpay_payment_id = data.get('razorpay_payment_id', '')
    razorpay_signature  = data.get('razorpay_signature', '')
    booking_id          = data.get('booking_id', '')

    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    if verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        fare        = float(booking.get('fare', 0))
        driver_earn = max(0.0, round(fare - COMMISSION, 2))

        record_payment(booking_id, razorpay_order_id, razorpay_payment_id, fare)
        db.update_one('bookings', {'_id': booking_id}, {
            'payment_status':      'paid',
            'payment_method':      'online',
            'status':              'confirmed',
            'razorpay_payment_id': razorpay_payment_id,
            'driver_earn':         driver_earn,
            'commission':          COMMISSION,
        })
        # Loyalty points (1 point per ₹10)
        points   = int(fare / 10)
        customer = db.find_one('users', {'_id': user['_id']})
        db.update_one('users', {'_id': user['_id']}, {
            'loyalty_points': (customer.get('loyalty_points', 0) or 0) + points
        })
        return jsonify({'success': True,
                        'redirect': url_for('booking.booking_detail', booking_id=booking_id)})

    return jsonify({'success': False, 'error': 'Payment verification failed'}), 400

@payment_bp.route('/cash/<booking_id>', methods=['POST'])
@login_required
def choose_cash(booking_id):
    """Customer selects cash payment — no Razorpay needed."""
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404
    if booking.get('status') == 'open':
        return jsonify({'success': False, 'error': 'Please select a driver first'}), 400
    if booking.get('payment_status') in ('paid', 'paid_cash'):
        return jsonify({'success': False, 'error': 'Already paid'}), 400

    data = request.get_json() or {}
    # Use custom amount if provided, else use booking fare
    custom_amount = float(data.get('amount', 0) or 0)
    fare = custom_amount if custom_amount >= 10 else float(booking.get('fare', 0))
    driver_earn = max(0.0, round(fare - COMMISSION, 2))

    db.update_one('bookings', {'_id': booking_id}, {
        'payment_method':  'cash',
        'payment_status':  'cash_pending',
        'status':          'confirmed',
        'payment_locked':  False,
        'fare':            round(fare, 2),
        'driver_earn':     driver_earn,
        'commission':      COMMISSION,
    })
    return jsonify({
        'success': True,
        'message': f'Cash payment of ₹{fare:.0f} selected. Pay your driver directly after the ride.',
        'redirect': url_for('booking.booking_detail', booking_id=booking_id)
    })

@payment_bp.route('/success/<booking_id>')
@login_required
def success(booking_id):
    booking = db.find_one('bookings', {'_id': booking_id})
    return render_template('customer/payment_success.html', booking=booking)

@payment_bp.route('/failed/<booking_id>')
@login_required
def failed(booking_id):
    booking = db.find_one('bookings', {'_id': booking_id})
    return render_template('customer/payment_failed.html', booking=booking)
