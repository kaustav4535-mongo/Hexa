import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify, session)
from functools import wraps
from shared import db
from datetime import datetime

driver_dash_bp = Blueprint('driver_dash', __name__)

# ── Auth guard ────────────────────────────────────────────────────────────────
def driver_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'driver' or not session.get('user_id'):
            flash('Please log in as a driver.', 'warning')
            return redirect(url_for('driver_auth.login'))
        return f(*args, **kwargs)
    return decorated

# ── Profile completeness guard ────────────────────────────────────────────────
def setup_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        uid = session.get('user_id', '')
        if not uid:
            return redirect(url_for('driver_auth.login'))
        driver = db.find_one('drivers', {'_id': uid})
        if not driver:
            session.clear()
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('driver_auth.login'))
        required = ['phone', 'vehicle_number', 'license_no']
        if not all(str(driver.get(field, '') or '').strip() for field in required):
            flash('Please complete your profile first.', 'warning')
            return redirect(url_for('driver_profile.setup'))
        return f(*args, **kwargs)
    return decorated

def get_driver():
    uid = session.get('user_id', '')
    if not uid:
        return None
    return db.find_one('drivers', {'_id': uid})

# ── Dashboard ─────────────────────────────────────────────────────────────────
@driver_dash_bp.route('/')
@driver_required
def dashboard():
    driver = get_driver()
    if not driver:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('driver_auth.login'))

    all_bookings = db.find('bookings', {'driver_id': driver['_id']})
    active = [b for b in all_bookings if b['status'] in ('confirmed', 'in_progress')]
    today  = datetime.utcnow().strftime('%Y-%m-%d')
    today_done = [b for b in all_bookings
                  if b['status'] == 'completed'
                  and b.get('created_at', '')[:10] == today]
    today_earn = sum(max(0.0, float(b.get('fare', 0)) - 2.0) for b in today_done)

    return render_template('driver/dashboard.html',
                           driver=driver,
                           active_rides=active,
                           today_rides=len(today_done),
                           today_earnings=today_earn)

# ── Toggle online/offline ─────────────────────────────────────────────────────
@driver_dash_bp.route('/toggle-status', methods=['POST'])
@driver_required
def toggle_status():
    driver = get_driver()
    if not driver:
        return jsonify({'success': False, 'error': 'Session expired'}), 401

    # FIX: proper toggle logic
    current = driver.get('status', 'offline')
    new_status = 'offline' if current == 'online' else 'online'

    # Driver can go online/offline freely — their own choice
    db.update_one('drivers', {'_id': driver['_id']}, {'status': new_status})
    return jsonify({'success': True, 'status': new_status})

# ── GPS location update ───────────────────────────────────────────────────────
@driver_dash_bp.route('/update-location', methods=['POST'])
@driver_required
def update_location():
    data = request.get_json() or {}
    uid  = session.get('user_id', '')
    if uid:
        db.update_one('drivers', {'_id': uid}, {
            'lat': float(data.get('lat', 0)),
            'lng': float(data.get('lng', 0)),
        })
    return jsonify({'success': True})

# ── Incoming requests polling ─────────────────────────────────────────────────
@driver_dash_bp.route('/api/requests')
@driver_required
def incoming_requests():
    driver = get_driver()
    if not driver:
        return jsonify({'requests': [], 'count': 0})

    # Driver must be online to receive requests
    if driver.get('status') != 'online':
        return jsonify({'requests': [], 'count': 0, 'offline': True})

    driver_id = driver['_id']

    # New flow: driver sends a quote with their own price
    all_open = db.find('bookings', {'status': 'open'})

    # Show bookings where THIS driver was selected (pending=awaiting payment)
    my_pending = [b for b in db.find('bookings', {'status': 'pending'})
                  if b.get('driver_id') == driver_id]

    # Show confirmed+paid bookings not yet started (so driver can tap "View Ride")
    my_confirmed = [b for b in db.find('bookings', {'status': 'confirmed'})
                    if b.get('driver_id') == driver_id]

    available = all_open + my_pending + my_confirmed

    result = []
    for b in available[:10]:
        quotes       = b.get('driver_quotes') or []
        my_quote     = next((q for q in quotes if q.get('driver_id') == driver_id), None)
        already_sent = my_quote is not None
        result.append({
            '_id':          b['_id'],
            'pickup':       b.get('pickup_address', ''),
            'dropoff':      b.get('dropoff_address', ''),
            'reference':    b.get('reference_fare', 0),   # zone estimate
            'hours':        b.get('hours', 1),
            'type':         b.get('booking_type', 'now'),
            'customer':     b.get('customer_name', ''),
            'distance':     b.get('distance_km', 0),
            'scheduled':    b.get('scheduled_datetime', ''),
            'quotes_count': len(quotes),
            'already_sent': already_sent,
            'my_price':     my_quote['price'] if my_quote else 0,
            'status':       b.get('status', ''),
            'notes':        b.get('notes', ''),
        })

    return jsonify({'requests': result, 'count': len(result)})

# ── Accept ride → UNLOCK PAYMENT ─────────────────────────────────────────────
@driver_dash_bp.route('/accept/<booking_id>', methods=['POST'])
@driver_required
def accept_ride(booking_id):
    driver  = get_driver()
    if not driver:
        return jsonify({'success': False, 'error': 'Session expired'}), 401

    booking = db.find_one('bookings', {'_id': booking_id})
    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    # Allow if: no driver yet, OR pre-assigned to this driver
    existing_driver = booking.get('driver_id', '')
    if existing_driver and existing_driver != driver['_id']:
        return jsonify({'success': False, 'error': 'This ride was already taken by another driver.'}), 409

    # Must be pending
    if booking.get('status') != 'pending':
        return jsonify({'success': False, 'error': 'This booking is no longer available.'}), 409

    # Accept: assign driver + unlock payment
    db.update_one('bookings', {'_id': booking_id}, {
        'driver_id':      driver['_id'],
        'driver_name':    driver.get('name', ''),
        'driver_phone':   driver.get('phone', ''),
        'status':         'confirmed',
        'payment_locked': False,       # ← UNLOCK: customer can now pay
        'payment_status': 'unpaid',
    })

    return jsonify({
        'success':  True,
        'message':  'Ride accepted! Customer can now make payment.',
        'redirect': url_for('driver_rides.ride_detail', booking_id=booking_id)
    })

# ── Reject/skip ride ──────────────────────────────────────────────────────────
@driver_dash_bp.route('/reject/<booking_id>', methods=['POST'])
@driver_required
def reject_ride(booking_id):
    # Just skip — booking stays pending for other drivers
    return jsonify({'success': True})

# ── Debug endpoint: check what's in DB right now ──────────────────────────────
@driver_dash_bp.route('/api/debug')
@driver_required
def debug_info():
    driver = get_driver()
    if not driver:
        return jsonify({'error': 'no driver'}), 401
    pending = db.find('bookings', {'status': 'pending'})
    return jsonify({
        'driver_id':     driver['_id'],
        'driver_status': driver.get('status'),
        'approval':      driver.get('approval'),
        'pending_bookings': len(pending),
        'bookings_detail': [{
            '_id': b['_id'][:8],
            'driver_id': b.get('driver_id', '(none)'),
            'status': b.get('status'),
            'customer': b.get('customer_name',''),
        } for b in pending]
    })


# ── My expressed interests ────────────────────────────────────────────────────
@driver_dash_bp.route('/api/my-interests')
@driver_required
def my_interests():
    """Bookings where this driver expressed interest but customer hasn't chosen yet."""
    driver = get_driver()
    if not driver:
        return jsonify({'bookings': []})

    all_open = db.find('bookings', {'status': 'open'})
    mine = [b for b in all_open
            if any(q.get('driver_id') == driver['_id'] for q in (b.get('driver_quotes') or []))]

    result = []
    for b in mine:
        my_q = next((q for q in (b.get('driver_quotes') or []) if q.get('driver_id') == driver['_id']), {})
        result.append({
            '_id':     b['_id'],
            'pickup':  b.get('pickup_address', ''),
            'dropoff': b.get('dropoff_address', ''),
            'my_price':float(my_q.get('price', 0)),
            'quotes':  len(b.get('driver_quotes', [])),
        })

    return jsonify({'bookings': result, 'count': len(result)})

# ── Send Quote ────────────────────────────────────────────────────────────────
@driver_dash_bp.route('/send-quote/<booking_id>', methods=['POST'])
@driver_required
def send_quote(booking_id):
    """Driver sends a price quote for an open booking."""
    driver = get_driver()
    if not driver:
        return jsonify({'success': False, 'error': 'Session expired'}), 401

    booking = db.find_one('bookings', {'_id': booking_id})
    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404
    if booking.get('status') != 'open':
        return jsonify({'success': False, 'error': 'Booking no longer available'}), 409

    data  = request.get_json() or {}
    price = float(data.get('price', 0) or 0)
    msg   = str(data.get('message', '') or '').strip()[:120]

    if price < 10:
        return jsonify({'success': False, 'error': 'Minimum quote is ₹10'}), 400

    # Replace existing quote from this driver (if any)
    quotes = [q for q in (booking.get('driver_quotes') or [])
              if q.get('driver_id') != driver['_id']]
    quotes.append({
        'driver_id': driver['_id'],
        'name':      driver.get('name', ''),
        'price':     round(price, 2),
        'message':   msg,
        'avatar':    driver.get('avatar', ''),
        'rating':    driver.get('rating', 5.0),
        'vehicle':   driver.get('vehicle_number', ''),
    })
    db.update_one('bookings', {'_id': booking_id}, {'driver_quotes': quotes})

    return jsonify({
        'success': True,
        'price':   price,
        'message': f'Quote of ₹{price:.0f} sent! Waiting for customer to confirm.',
    })


# ── Withdraw Quote ────────────────────────────────────────────────────────────
@driver_dash_bp.route('/withdraw-quote/<booking_id>', methods=['POST'])
@driver_required
def withdraw_quote(booking_id):
    driver = get_driver()
    if not driver:
        return jsonify({'success': False, 'error': 'Session expired'}), 401
    booking = db.find_one('bookings', {'_id': booking_id})
    if not booking:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    quotes = [q for q in (booking.get('driver_quotes') or []) if q.get('driver_id') != driver['_id']]
    db.update_one('bookings', {'_id': booking_id}, {'driver_quotes': quotes})
    return jsonify({'success': True, 'message': 'Quote withdrawn.'})


# ── Alias for old express-interest URL ───────────────────────────────────────
@driver_dash_bp.route('/express-interest/<booking_id>', methods=['POST'])
@driver_required
def express_interest(booking_id):
    """Redirects to send_quote — kept for backward compat."""
    return jsonify({'success': False,
                    'error': 'Please use the Send Quote button to submit a price.'})
