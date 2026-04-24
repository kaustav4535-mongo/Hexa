import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from flask import Blueprint, render_template, jsonify
from shared import db
from shared.auth import current_user
from shared.config import Config
from shared.zone_engine import detect_zone, find_nearest_drivers

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    user           = current_user()
    total_drivers  = db.count('drivers', {'status': 'online'})
    total_bookings = db.count('bookings')
    zones          = db.find('zones')
    return render_template('customer/index.html',
                           user=user,
                           total_drivers=total_drivers,
                           total_bookings=total_bookings,
                           zones=zones,
                           maptiler_key=Config.MAPTILER_KEY_SAT,
                           maptiler_key_sat=Config.MAPTILER_KEY_SAT,
                           maptiler_key_street=Config.MAPTILER_KEY_STREET,
                           ipinfo_token=Config.IPINFO_TOKEN)

@home_bp.route('/api/drivers/available')
def available_drivers():
    from flask import request as req
    # Optional: filter by lat/lng to show nearest drivers
    lat = float(req.args.get('lat', 0) or 0)
    lng = float(req.args.get('lng', 0) or 0)

    if lat and lng:
        # Detect zone and return zone-relevant drivers sorted by distance
        zone = detect_zone(lat, lng)
        zone_id = zone['_id'] if zone else ''
        drivers = find_nearest_drivers(lat, lng, zone_id, max_results=20)
    else:
        drivers = db.find('drivers', {'status': 'online', 'approval': 'approved'})

    safe = [{
        '_id':     d['_id'],
        'name':    d.get('name', ''),
        'rating':  d.get('rating', 5.0),
        'lat':     d.get('lat', 0),
        'lng':     d.get('lng', 0),
        'vehicle': d.get('vehicle_number', ''),
        'avatar':  d.get('avatar', ''),
        'dist_km': d.get('_distance_km', None),
    } for d in drivers if d.get('status') == 'online']

    return jsonify({'drivers': safe, 'count': len(safe)})

@home_bp.route('/about')
def about():
    from flask import render_template
    return render_template('customer/about_us.html')

@home_bp.route('/terms')
def terms():
    from flask import render_template
    return render_template('customer/terms.html')

@home_bp.route('/install')
def install():
    return render_template('customer/install.html')

@home_bp.route('/connect')
def connect():
    return render_template('customer/connect.html')
