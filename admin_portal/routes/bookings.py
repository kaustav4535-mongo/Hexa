import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from admin_portal.utils import admin_required
from shared import db
from shared.config import Config

admin_bookings_bp = Blueprint('admin_bookings', __name__)

@admin_bookings_bp.route('/')
@admin_required
def bookings_list():
    search = request.args.get('q', '').strip().lower()
    status = request.args.get('status', '')
    btype  = request.args.get('type', '')

    bookings = db.find('bookings')
    if search:
        bookings = [b for b in bookings if
                    search in b.get('customer_name','').lower() or
                    search in b.get('pickup_address','').lower() or
                    search in b.get('_id','').lower()]
    if status:
        bookings = [b for b in bookings if b.get('status') == status]
    if btype:
        bookings = [b for b in bookings if b.get('booking_type') == btype]

    bookings.sort(key=lambda b: b.get('created_at', ''), reverse=True)
    return render_template('admin/bookings.html',
                           bookings=bookings, search=search,
                           status_filter=status, type_filter=btype)

@admin_bookings_bp.route('/<booking_id>')
@admin_required
def booking_detail(booking_id):
    booking  = db.find_one('bookings', {'_id': booking_id})
    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('admin_bookings.bookings_list'))
    customer = db.find_one('users',   {'_id': booking.get('customer_id','')})
    driver   = db.find_one('drivers', {'_id': booking.get('driver_id','')}) if booking.get('driver_id') else None
    payment  = db.find_one('payments',{'booking_id': booking_id})
    available_drivers = db.find('drivers', {'approval':'approved','status':'offline'}) + db.find('drivers', {'approval':'approved','status':'online'})
    return render_template('admin/booking_detail.html',
                           booking=booking, customer=customer,
                           driver=driver, payment=payment,
                           available_drivers=available_drivers,
                           maptiler_key=Config.MAPTILER_KEY)

@admin_bookings_bp.route('/<booking_id>/assign-driver', methods=['POST'])
@admin_required
def assign_driver(booking_id):
    driver_id = request.form.get('driver_id', '')
    driver    = db.find_one('drivers', {'_id': driver_id})
    if not driver:
        flash('Driver not found.', 'danger')
        return redirect(url_for('admin_bookings.booking_detail', booking_id=booking_id))
    db.update_one('bookings', {'_id': booking_id}, {
        'driver_id':   driver_id,
        'driver_name': driver.get('name',''),
        'status':      'confirmed',
    })
    flash(f'Driver {driver["name"]} assigned.', 'success')
    return redirect(url_for('admin_bookings.booking_detail', booking_id=booking_id))

@admin_bookings_bp.route('/<booking_id>/cancel', methods=['POST'])
@admin_required
def cancel_booking(booking_id):
    db.update_one('bookings', {'_id': booking_id}, {'status': 'cancelled'})
    flash('Booking cancelled.', 'warning')
    return redirect(url_for('admin_bookings.booking_detail', booking_id=booking_id))

@admin_bookings_bp.route('/api/export')
@admin_required
def export_csv():
    import csv, io
    from flask import Response
    bookings = db.find('bookings')
    output   = io.StringIO()
    writer   = csv.DictWriter(output, fieldnames=[
        '_id','customer_name','customer_email','pickup_address',
        'dropoff_address','booking_type','fare','status',
        'payment_status','created_at'
    ])
    writer.writeheader()
    for b in bookings:
        writer.writerow({k: b.get(k,'') for k in writer.fieldnames})
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition':'attachment;filename=bookings.csv'})
