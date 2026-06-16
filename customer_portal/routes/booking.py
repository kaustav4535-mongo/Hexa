import sys, os, uuid, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from shared import db
from shared.config import Config
from shared.auth import login_required, current_user
from shared.zone_engine import detect_zone, is_in_zone, calculate_fare

booking_bp = Blueprint('booking', __name__)
COMMISSION = Config.PLATFORM_COMMISSION  # ₹2 flat

def _valid_india_coords(lat: float, lng: float) -> bool:
    if not lat or not lng:
        return False
    return (Config.INDIA_LAT_MIN <= lat <= Config.INDIA_LAT_MAX and
            Config.INDIA_LNG_MIN <= lng <= Config.INDIA_LNG_MAX)

# ── New booking ───────────────────────────────────────────────────────────────
@booking_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_booking():
    zones   = db.find('zones')
    drivers = db.find('drivers', {'status': 'online', 'approval': 'approved'})

    if request.method == 'POST':
        user        = current_user()
        data        = request.form
        pickup      = data.get('pickup_address', '').strip()
        dropoff     = data.get('dropoff_address', '').strip()
        pickup_lat  = float(data.get('pickup_lat',  0) or 0)
        pickup_lng  = float(data.get('pickup_lng',  0) or 0)
        dropoff_lat = float(data.get('dropoff_lat', 0) or 0)
        dropoff_lng = float(data.get('dropoff_lng', 0) or 0)
        zone_id     = data.get('zone_id', '').strip()
        book_type   = data.get('booking_type', 'now')
        hours       = float(data.get('hours', 1) or 1)
        date_time   = data.get('scheduled_datetime', '')
        notes       = data.get('notes', '')
        distance_km = float(data.get('distance_km', 0) or 0)

        if not pickup:
            flash('Pickup address is required.', 'danger')
            return render_template('customer/booking_new.html',
                                   zones=zones, drivers=drivers,
                                   maptiler_key=Config.MAPTILER_KEY)
        if not _valid_india_coords(pickup_lat, pickup_lng):
            flash('Please select a valid pickup location in India.', 'danger')
            return render_template('customer/booking_new.html',
                                   zones=zones, drivers=drivers,
                                   maptiler_key=Config.MAPTILER_KEY)
        if (dropoff_lat or dropoff_lng) and not _valid_india_coords(dropoff_lat, dropoff_lng):
            flash('Please select a valid drop-off location in India.', 'danger')
            return render_template('customer/booking_new.html',
                                   zones=zones, drivers=drivers,
                                   maptiler_key=Config.MAPTILER_KEY)

        # Auto-detect zone
        if not zone_id and pickup_lat and pickup_lng:
            auto_zone = detect_zone(pickup_lat, pickup_lng)
            if auto_zone:
                zone_id = auto_zone['_id']

        # Calculate reference fare (shown to drivers as a guide only)
        zone = db.find_one('zones', {'_id': zone_id}) if zone_id else None
        interzone      = False
        reference_fare = 0.0
        if zone:
            if pickup_lat and pickup_lng:
                interzone = not is_in_zone(pickup_lat, pickup_lng, zone)
            fare_info      = calculate_fare(zone, distance_km, hours, is_interzone=interzone)
            reference_fare = fare_info['total']

        # Create booking — NO price set yet (driver will quote)
        booking = db.insert_one('bookings', {
            'customer_id':         user['_id'],
            'customer_name':       user['name'],
            'customer_email':      user['email'],
            'pickup_address':      pickup,
            'dropoff_address':     dropoff,
            'pickup_lat':          pickup_lat,
            'pickup_lng':          pickup_lng,
            'dropoff_lat':         dropoff_lat,
            'dropoff_lng':         dropoff_lng,
            'distance_km':         round(distance_km, 2),
            'zone_id':             zone_id,
            'booking_type':        book_type,
            'hours':               hours,
            'scheduled_datetime':  date_time,
            'notes':               notes,
            'fare':                0.0,          # set when customer confirms a driver's quote
            'reference_fare':      round(reference_fare, 2),  # zone estimate (guide only)
            'commission':          COMMISSION,
            'driver_earn':         0.0,          # set after fare confirmed
            'driver_id':           '',
            'driver_name':         '',
            'driver_phone':        '',
            'status':              'open',        # open = waiting for driver quotes
            'payment_status':      'pending',
            'payment_method':      '',
            'payment_locked':      True,          # unlocked after customer confirms quote
            'driver_quotes':       [],            # [{driver_id, name, price, avatar, rating, vehicle}]
            'interested_drivers':  [],
            'is_interzone':        interzone,
        })

        flash('Ride posted! Drivers will send you their price quotes.', 'success')
        return redirect(url_for('booking.booking_detail', booking_id=booking['_id']))

    return render_template('customer/booking_new.html',
                           zones=zones, drivers=drivers,
                           maptiler_key=Config.MAPTILER_KEY,
                           commission=COMMISSION)

# ── My bookings ───────────────────────────────────────────────────────────────
@booking_bp.route('/my')
@login_required
def my_bookings():
    user     = current_user()
    bookings = db.find('bookings', {'customer_id': user['_id']})
    bookings.sort(key=lambda b: b.get('created_at', ''), reverse=True)
    return render_template('customer/my_bookings.html', bookings=bookings)

# ── Booking detail ────────────────────────────────────────────────────────────
@booking_bp.route('/<booking_id>')
@login_required
def booking_detail(booking_id):
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id})
    if not booking or booking.get('customer_id') != user['_id']:
        flash('Booking not found.', 'danger')
        return redirect(url_for('booking.my_bookings'))

    driver  = db.find_one('drivers', {'_id': booking.get('driver_id', '')}) \
              if booking.get('driver_id') else None
    payment = db.find_one('payments', {'booking_id': booking_id})

    # Enrich driver_quotes with live driver info
    quotes = []
    for q in (booking.get('driver_quotes') or []):
        d = db.find_one('drivers', {'_id': q.get('driver_id', '')})
        if d:
            # Distance from driver to pickup
            dlat = float(d.get('lat', 0) or 0)
            dlng = float(d.get('lng', 0) or 0)
            dist = None
            if dlat and dlng and booking.get('pickup_lat'):
                R    = 6371
                dLat = math.radians(dlat - float(booking['pickup_lat']))
                dLng = math.radians(dlng - float(booking.get('pickup_lng', 0)))
                a    = (math.sin(dLat/2)**2 +
                        math.cos(math.radians(float(booking['pickup_lat']))) *
                        math.cos(math.radians(dlat)) * math.sin(dLng/2)**2)
                dist = round(6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)), 1)
            quotes.append({
                'driver_id':    d['_id'],
                'name':         d.get('name', ''),
                'price':        float(q.get('price', 0)),
                'driver_earn':  max(0.0, round(float(q.get('price', 0)) - COMMISSION, 2)),
                'rating':       d.get('rating', 5.0),
                'vehicle':      d.get('vehicle_number', ''),
                'avatar':       d.get('avatar', ''),
                'dist_km':      dist,
                'total_rides':  d.get('total_rides', 0),
                'message':      q.get('message', ''),
            })

    # Sort quotes by price (lowest first)
    quotes.sort(key=lambda q: q['price'])

    return render_template('customer/booking_detail.html',
                           booking=booking, driver=driver,
                           payment=payment, driver_quotes=quotes,
                           commission=COMMISSION)

# ── Customer confirms a driver's quote ───────────────────────────────────────
@booking_bp.route('/<booking_id>/confirm-quote', methods=['POST'])
@login_required
def confirm_quote(booking_id):
    """Customer selects a driver's price quote. Fare is set to that price."""
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id})
    if not booking or booking.get('customer_id') != user['_id']:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    if booking.get('status') not in ('open',):
        return jsonify({'success': False, 'error': 'Booking no longer open'}), 409

    data             = request.get_json() or {}
    chosen_driver_id = data.get('driver_id', '')

    # Find the quote from this driver
    quote = next((q for q in (booking.get('driver_quotes') or [])
                  if q.get('driver_id') == chosen_driver_id), None)
    if not quote:
        return jsonify({'success': False, 'error': 'Quote not found'}), 400

    driver = db.find_one('drivers', {'_id': chosen_driver_id})
    if not driver:
        return jsonify({'success': False, 'error': 'Driver not found'}), 404

    fare        = float(quote['price'])
    driver_earn = max(0.0, round(fare - COMMISSION, 2))

    db.update_one('bookings', {'_id': booking_id}, {
        'driver_id':      chosen_driver_id,
        'driver_name':    driver.get('name', ''),
        'driver_phone':   driver.get('phone', ''),
        'fare':           fare,
        'driver_earn':    driver_earn,
        'status':         'pending',
        'payment_locked': False,   # customer can now pay
        'payment_status': 'unpaid',
        'driver_quotes':  [],      # clear quotes
        'interested_drivers': [],
    })

    return jsonify({
        'success': True,
        'fare':    fare,
        'message': f'Driver {driver["name"]} confirmed at ₹{fare:.0f}!'
    })

# ── Cancel booking ────────────────────────────────────────────────────────────
@booking_bp.route('/<booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking:
        return jsonify({'error': 'Not found'}), 404
    if booking['status'] not in ('open', 'pending', 'confirmed'):
        return jsonify({'error': 'Cannot cancel at this stage'}), 400
    db.update_one('bookings', {'_id': booking_id}, {'status': 'cancelled'})
    return jsonify({'success': True})

# ── Post-ride rating ──────────────────────────────────────────────────────────
@booking_bp.route('/<booking_id>/rate', methods=['POST'])
@login_required
def rate_driver(booking_id):
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('booking.my_bookings'))
    if booking.get('status') != 'completed':
        flash('You can rate only after the ride is completed.', 'warning')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))
    if booking.get('rating'):
        flash('You already rated this ride.', 'info')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))

    try:
        rating = int(request.form.get('rating', 0))
    except (TypeError, ValueError):
        rating = 0
    if rating not in (1, 2, 3, 4, 5):
        flash('Please choose a rating between 1 and 5.', 'danger')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))

    comment = (request.form.get('comment', '') or '').strip()[:240]
    driver = db.find_one('drivers', {'_id': booking.get('driver_id', '')})
    if not driver:
        flash('Driver not found.', 'danger')
        return redirect(url_for('booking.booking_detail', booking_id=booking_id))

    count = int(driver.get('rating_count', 0) or 0)
    avg   = float(driver.get('rating', 5.0) or 5.0)
    new_avg = round(((avg * count) + rating) / (count + 1), 2)

    db.update_one('drivers', {'_id': driver['_id']}, {
        'rating': new_avg,
        'rating_count': count + 1,
    })
    db.update_one('bookings', {'_id': booking_id}, {
        'rating': rating,
        'rating_comment': comment,
    })
    flash('Thanks for rating your driver!', 'success')
    return redirect(url_for('booking.booking_detail', booking_id=booking_id))

# ── Booking status API (polled by customer page) ──────────────────────────────
@booking_bp.route('/api/status/<booking_id>')
@login_required
def booking_status_api(booking_id):
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'status':         booking['status'],
        'payment_status': booking.get('payment_status', 'pending'),
        'payment_method': booking.get('payment_method', ''),
        'fare':           booking.get('fare', 0),
        'quotes_count':   len(booking.get('driver_quotes') or []),
    })

# ── Driver GPS for customer map ───────────────────────────────────────────────
@booking_bp.route('/api/driver-location/<booking_id>')
@login_required
def driver_location_api(booking_id):
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking: return jsonify({'error': 'Not found'}), 404
    if not booking.get('driver_id'): return jsonify({'driver': None})
    driver = db.find_one('drivers', {'_id': booking['driver_id']})
    if not driver: return jsonify({'driver': None})
    return jsonify({
        'driver': {
            'lat': driver.get('lat', 0), 'lng': driver.get('lng', 0),
            'name': driver.get('name', ''), 'rating': driver.get('rating', 5.0),
            'vehicle': driver.get('vehicle_number', ''),
        },
        'booking_status': booking.get('status', ''),
        'quotes_count':   len(booking.get('driver_quotes') or []),
    })

# ── Zone fare estimate (reference only) ──────────────────────────────────────
@booking_bp.route('/api/fare-estimate')
def fare_estimate_api():
    zone_id = request.args.get('zone_id', '')
    hours   = float(request.args.get('hours', 1) or 1)
    km      = float(request.args.get('km', 0) or 0)
    zone    = db.find_one('zones', {'_id': zone_id})
    if not zone:
        return jsonify({'error': 'Zone not found'}), 404
    info = calculate_fare(zone, km, hours)
    return jsonify({'estimate': info['total'], 'breakdown': info})

# ── Detect zone from GPS ──────────────────────────────────────────────────────
@booking_bp.route('/api/detect-zone')
def detect_zone_api():
    lat = float(request.args.get('lat', 0) or 0)
    lng = float(request.args.get('lng', 0) or 0)
    if not lat or not lng:
        return jsonify({'zone_id': '', 'zone_name': ''})
    zone = detect_zone(lat, lng)
    if not zone:
        return jsonify({'zone_id': '', 'zone_name': ''})
    return jsonify({'zone_id': zone['_id'], 'zone_name': zone.get('name', ''),
                    'base_fare': zone.get('base_fare', 30)})

# ── Share payment link ────────────────────────────────────────────────────────
@booking_bp.route('/<booking_id>/share-payment', methods=['POST'])
@login_required
def share_payment_link(booking_id):
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    if booking.get('payment_locked', True):
        return jsonify({'success': False, 'error': 'Confirm a driver quote first'}), 400

    token = booking.get('share_token') or str(uuid.uuid4()).replace('-', '')[:24]
    db.update_one('bookings', {'_id': booking_id}, {'share_token': token})
    base  = request.host_url.rstrip('/')
    return jsonify({'success': True, 'link': f"{base}/booking/pay/{token}"})

# ── Public payment page ───────────────────────────────────────────────────────
@booking_bp.route('/pay/<token>')
def public_pay(token):
    booking = db.find_one('bookings', {'share_token': token})
    if not booking:
        from flask import abort; abort(404)
    already_paid = booking.get('payment_status') in ('paid', 'paid_cash')
    locked       = booking.get('payment_locked', True)
    fare         = float(booking.get('fare', 0))
    driver_earn  = max(0.0, round(fare - COMMISSION, 2))
    return render_template('customer/pay_public.html',
                           booking=booking, token=token,
                           already_paid=already_paid, locked=locked,
                           fare=fare, driver_earn=driver_earn,
                           commission=COMMISSION,
                           rzp_key=Config.RAZORPAY_KEY_ID)

# ── Create order for public pay ───────────────────────────────────────────────
@booking_bp.route('/pay/<token>/create-order', methods=['POST'])
def public_create_order(token):
    from shared.payments import create_order
    booking = db.find_one('bookings', {'share_token': token})
    if not booking: return jsonify({'success': False, 'error': 'Invalid link'}), 404
    if booking.get('payment_locked', True): return jsonify({'success': False, 'error': 'Not ready'}), 400
    data   = request.get_json() or {}
    amount = float(data.get('amount', booking.get('fare', 0)) or booking.get('fare', 0))
    if amount < 10: return jsonify({'success': False, 'error': 'Minimum ₹10'}), 400
    order  = create_order(amount_inr=amount, booking_id=booking['_id'],
                          notes={'payer': 'third_party'})
    db.update_one('bookings', {'_id': booking['_id']},
                  {'razorpay_order_id': order['id'], 'payment_method': 'online'})
    return jsonify({'success': True, 'order_id': order['id'], 'amount': amount})

# ── Verify payment from public page ──────────────────────────────────────────
@booking_bp.route('/pay/<token>/verify', methods=['POST'])
def public_verify(token):
    from shared.payments import verify_payment, record_payment
    booking = db.find_one('bookings', {'share_token': token})
    if not booking: return jsonify({'success': False, 'error': 'Invalid link'}), 404
    data = request.get_json() or {}
    if verify_payment(data.get('razorpay_order_id',''),
                      data.get('razorpay_payment_id',''),
                      data.get('razorpay_signature','')):
        fare        = float(booking.get('fare', 0))
        driver_earn = max(0.0, round(fare - COMMISSION, 2))
        record_payment(booking['_id'], data['razorpay_order_id'], data['razorpay_payment_id'], fare)
        db.update_one('bookings', {'_id': booking['_id']}, {
            'payment_status': 'paid', 'payment_method': 'online', 'status': 'confirmed',
            'razorpay_payment_id': data['razorpay_payment_id'],
            'driver_earn': driver_earn, 'paid_by': 'third_party',
        })
        return jsonify({'success': True, 'message': 'Payment done! Ride confirmed.'})
    return jsonify({'success': False, 'error': 'Verification failed'}), 400

# ── Booking expiry check ──────────────────────────────────────────────────────
@booking_bp.route('/api/check-expiry/<booking_id>', methods=['POST'])
@login_required
def check_expiry(booking_id):
    from datetime import datetime
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking or booking.get('status') != 'open':
        return jsonify({'expired': False})
    try:
        created  = datetime.fromisoformat(booking.get('created_at', ''))
        elapsed  = (datetime.utcnow() - created).total_seconds()
        has_quot = bool(booking.get('driver_quotes'))
        if elapsed > Config.BOOKING_EXPIRY_SECONDS and not has_quot:
            db.update_one('bookings', {'_id': booking_id}, {
                'status': 'expired',
                'expired_reason': 'No driver quotes in 10 minutes'
            })
            return jsonify({'expired': True,
                            'message': 'No drivers available. Try again or change location.'})
        if elapsed > Config.BOOKING_EXPIRY_WARNING_SECONDS and not has_quot:
            return jsonify({'expired': False, 'warning': True,
                            'remaining_sec': int(Config.BOOKING_EXPIRY_SECONDS - elapsed),
                            'message': f'No quotes yet. Expires in {int((Config.BOOKING_EXPIRY_SECONDS-elapsed)//60)}m.'})
        return jsonify({'expired': False, 'elapsed': int(elapsed), 'has_quotes': has_quot})
    except Exception:
        return jsonify({'expired': False})

# ── Repost expired booking ────────────────────────────────────────────────────
@booking_bp.route('/<booking_id>/repost', methods=['POST'])
@login_required
def repost_booking(booking_id):
    user    = current_user()
    booking = db.find_one('bookings', {'_id': booking_id, 'customer_id': user['_id']})
    if not booking or booking.get('status') != 'expired':
        return jsonify({'success': False, 'error': 'Not expired'}), 400
    db.update_one('bookings', {'_id': booking_id}, {
        'status': 'open', 'driver_quotes': [], 'interested_drivers': []
    })
    return jsonify({'success': True, 'message': 'Booking reposted!'})
