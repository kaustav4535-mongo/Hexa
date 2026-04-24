"""
seed_db.py — Run once to populate db.json with sample data.
Usage: python seed_db.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from shared import db
from shared.auth import hash_password

def seed():
    print("\n🌱 Seeding E-TukTukGo database...\n")

    # ── Zones ────────────────────────────────────────────────────────────────
    if not db.find('zones'):
        zones = [
            {"name":"Jorhat Central", "state":"Assam","district":"Jorhat",
             "base_fare":20,"per_km_rate":8,"per_hour_rate":60,"minimum_fare":30,"center_lat":26.9839,"center_lng":94.6397,"radius_km":5,"interzone_surcharge":1.2,"center_lat":26.7509,"center_lng":94.2037,"radius_km":8,"interzone_surcharge":1.3,
             "night_surcharge":1.3,"peak_multiplier":1.5,"emergency_multiplier":1.5,
             "cancellation_pct":10,"active":True},
            {"name":"Golaghat",       "state":"Assam","district":"Golaghat",
             "base_fare":22,"per_km_rate":9,"per_hour_rate":63,"minimum_fare":32,"center_lat":27.4871,"center_lng":95.3586,"radius_km":5,"interzone_surcharge":1.2,"center_lat":26.5041,"center_lng":93.9700,"radius_km":6,"interzone_surcharge":1.25,
             "night_surcharge":1.4,"peak_multiplier":1.6,"emergency_multiplier":2.0,
             "cancellation_pct":10,"active":True},
            {"name":"Sibsagar",       "state":"Assam","district":"Sivasagar",
             "base_fare":20,"per_km_rate":8,"per_hour_rate":60,"minimum_fare":30,"center_lat":26.9839,"center_lng":94.6397,"radius_km":5,"interzone_surcharge":1.2,
             "night_surcharge":1.2,"peak_multiplier":1.4,"emergency_multiplier":1.5,
             "cancellation_pct":10,"active":True},
            {"name":"Dibrugarh",      "state":"Assam","district":"Dibrugarh",
             "base_fare":24,"per_km_rate":10,"per_hour_rate":68,"minimum_fare":38,"center_lat":27.4728,"center_lng":94.9120,"radius_km":7,"interzone_surcharge":1.3,
             "night_surcharge":1.2,"peak_multiplier":1.4,"emergency_multiplier":1.5,
             "cancellation_pct":10,"active":True},
            {"name":"Tinsukia",       "state":"Assam","district":"Tinsukia",
             "base_fare":22,"per_km_rate":9,"per_hour_rate":63,"minimum_fare":32,"center_lat":27.4871,"center_lng":95.3586,"radius_km":5,"interzone_surcharge":1.2,
             "night_surcharge":1.2,"peak_multiplier":1.3,"emergency_multiplier":1.5,
             "cancellation_pct":10,"active":True},
        ]
        for z in zones:
            db.insert_one('zones', z)
        print(f"  ✓ Created {len(zones)} pricing zones")
    else:
        print(f"  → Zones already exist ({db.count('zones')}), skipping")

    # ── Super Admin ───────────────────────────────────────────────────────────
    if not db.find_one('admins', {'email': 'admin@etuktuk.in'}):
        db.insert_one('admins', {
            'name': 'Super Admin', 'email': 'admin@etuktuk.in',
            'password_hash': hash_password('Admin@1234'),
            'role': 'superadmin', 'status': 'active',
        })
        print("  ✓ Admin created    → admin@etuktuk.in / Admin@1234")
    else:
        print("  → Admin already exists, skipping")

    # ── Sample Driver ─────────────────────────────────────────────────────────
    if not db.find_one('drivers', {'email': 'driver1@etuktuk.in'}):
        db.insert_one('drivers', {
            'name': 'Raju Sharma', 'email': 'driver1@etuktuk.in',
            'phone': '+91 98765 00001',
            'password_hash': hash_password('Driver@1234'),
            'vehicle_number': 'MH12-EV-0001', 'license_no': 'MH1234567890',
            'avatar': '', 'status': 'online',
            'approval': 'approved',
            'rating': 4.8, 'rating_count': 12,
            'wallet': 0.0, 'total_rides': 0, 'total_earnings': 0.0,
            'lat': 18.5204, 'lng': 73.8567,
            'auth_provider': 'email',
        })
        print("  ✓ Driver created   → driver1@etuktuk.in / Driver@1234")
    else:
        print("  → Driver already exists, skipping")

    # ── Sample Customer ───────────────────────────────────────────────────────
    if not db.find_one('users', {'email': 'customer1@etuktuk.in'}):
        db.insert_one('users', {
            'name': 'Priya Kulkarni', 'email': 'customer1@etuktuk.in',
            'phone': '+91 99000 11111',
            'password_hash': hash_password('Customer@1234'),
            'avatar': '', 'wallet': 100.0,
            'loyalty_points': 50, 'status': 'active',
            'auth_provider': 'email',
        })
        print("  ✓ Customer created → customer1@etuktuk.in / Customer@1234")
    else:
        print("  → Customer already exists, skipping")

    # ── Sample Booking (with new fields) ─────────────────────────────────────
    if not db.find('bookings'):
        zone = db.find_one('zones', {'name': 'Pune Central'})
        user = db.find_one('users', {'email': 'customer1@etuktuk.in'})
        drv  = db.find_one('drivers', {'email': 'driver1@etuktuk.in'})
        if zone and user:
            db.insert_one('bookings', {
                'customer_id':        user['_id'],
                'customer_name':      user['name'],
                'customer_email':     user['email'],
                'pickup_address':     '12 MG Road, Pune',
                'dropoff_address':    'Pune Airport',
                'pickup_lat':         '18.5204',
                'pickup_lng':         '73.8567',
                'dropoff_lat':        '18.5822',
                'dropoff_lng':        '73.9197',
                'distance_km':        8.5,
                'zone_id':            zone['_id'],
                'booking_type':       'now',
                'hours':              1,
                'scheduled_datetime': '',
                'driver_id':          drv['_id'] if drv else '',
                'driver_name':        drv['name'] if drv else '',
                'notes':              'Sample booking for testing',
                'fare':               160.0,
                'status':             'completed',
                'payment_status':     'paid',
                'payment_method':     'online',
                'driver_earn':        0.0,
                'payment_locked':     False,
            })
            print("  ✓ Sample booking created (completed + paid)")
    else:
        print(f"  → Bookings already exist ({db.count('bookings')}), skipping")

    print("\n" + "─"*52)
    print("✅  Seeding complete!\n")
    print("📋  Test credentials:")
    print("    Customer  → customer1@etuktuk.in  / Customer@1234")
    print("    Driver    → driver1@etuktuk.in    / Driver@1234")
    print("    Admin     → admin@etuktuk.in      / Admin@1234")
    print("\n🚀  Quick start:")
    print("    python run_all.py          # all 3 portals")
    print("    python customer_portal/app.py   # port 5001")
    print("    python driver_portal/app.py     # port 5002")
    print("    python admin_portal/app.py      # port 5003")
    print("─"*52 + "\n")

if __name__ == '__main__':
    seed()
