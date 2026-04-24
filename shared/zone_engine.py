"""
zone_engine.py — Geographic zone detection and driver matching engine.

Zone: a circular geographic area defined by center_lat, center_lng, radius_km.
Drivers are assigned to serve one or more zones.
Customers are auto-assigned to the nearest zone based on pickup GPS.

Inter-zone bookings (customer outside any zone) are handled with a surcharge.
"""
import math
from shared import db


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate straight-line distance in km between two GPS coordinates.
    Used for zone detection and driver matching.
    """
    R = 6371  # Earth radius km
    dLat = math.radians(lat2 - lat1)
    dLng = math.radians(lng2 - lng1)
    a = (math.sin(dLat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dLng/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def detect_zone(lat: float, lng: float) -> dict | None:
    """
    Detect which zone the given coordinates fall into.
    Returns the zone dict if inside a zone boundary, else None.

    A zone must have: center_lat, center_lng, radius_km to use geo-detection.
    Falls back to first active zone if zones have no coordinates set.
    """
    if not lat or not lng:
        return None

    zones = db.find('zones')
    active = [z for z in zones if z.get('active', True)]

    if not active:
        return None

    # Zones with geo boundaries defined
    geo_zones = [z for z in active if z.get('center_lat') and z.get('center_lng') and z.get('radius_km')]

    if geo_zones:
        # Find zone containing the point
        inside = []
        for z in geo_zones:
            dist = haversine(lat, lng, float(z['center_lat']), float(z['center_lng']))
            if dist <= float(z.get('radius_km', 10)):
                inside.append((dist, z))

        if inside:
            # If multiple zones overlap, use the one whose center is closest
            inside.sort(key=lambda x: x[0])
            return inside[0][1]

        # Not inside any zone — find nearest zone
        nearest = min(geo_zones, key=lambda z: haversine(
            lat, lng, float(z['center_lat']), float(z['center_lng'])
        ))
        return nearest  # flagged as out-of-zone via is_in_zone()

    # No geo boundaries — return first active zone (legacy behavior)
    return active[0]


def is_in_zone(lat: float, lng: float, zone: dict) -> bool:
    """
    Check if coordinates are within a zone's boundary.
    Returns True if inside, False if outside (inter-zone).
    """
    if not zone.get('center_lat') or not zone.get('center_lng') or not zone.get('radius_km'):
        return True  # No boundary defined — assume in-zone

    dist = haversine(lat, lng, float(zone['center_lat']), float(zone['center_lng']))
    return dist <= float(zone.get('radius_km', 10))


def get_interzone_surcharge(zone: dict) -> float:
    """
    Extra charge multiplier for bookings outside zone boundary.
    Stored per zone (default 1.3 = 30% extra).
    """
    return float(zone.get('interzone_surcharge', 1.3))


def calculate_fare(zone: dict, distance_km: float, hours: float,
                   is_night: bool = False, is_peak: bool = False,
                   is_emergency: bool = False, is_interzone: bool = False) -> dict:
    """
    Complete fare calculator using zone rates.
    Returns detailed breakdown dict.
    """
    base     = float(zone.get('base_fare', 30))
    per_km   = float(zone.get('per_km_rate', 12))
    per_hour = float(zone.get('per_hour_rate', 80))
    min_fare = float(zone.get('minimum_fare', 50))

    fare = base + (per_km * distance_km) + (per_hour * hours)

    multiplier = 1.0
    if is_night:      multiplier *= float(zone.get('night_surcharge', 1.3))
    if is_peak:       multiplier *= float(zone.get('peak_multiplier', 1.5))
    if is_emergency:  multiplier *= float(zone.get('emergency_multiplier', 1.5))
    if is_interzone:  multiplier *= get_interzone_surcharge(zone)

    final = max(fare * multiplier, min_fare)

    return {
        'base':          round(base, 2),
        'km_cost':       round(per_km * distance_km, 2),
        'hour_cost':     round(per_hour * hours, 2),
        'subtotal':      round(fare, 2),
        'multiplier':    round(multiplier, 2),
        'is_interzone':  is_interzone,
        'is_night':      is_night,
        'is_peak':       is_peak,
        'total':         round(final, 2),
        'zone_name':     zone.get('name', ''),
    }


def get_available_drivers_in_zone(zone_id: str) -> list:
    """
    Return online, approved drivers who serve the given zone.
    Drivers can serve multiple zones (stored as list in served_zone_ids).
    """
    all_online = db.find('drivers', {'status': 'online', 'approval': 'approved'})
    result = []
    for d in all_online:
        served = d.get('served_zone_ids', [])
        home   = d.get('home_zone_id', '')
        # Driver serves this zone if: home zone matches, OR zone is in their served list
        if home == zone_id or zone_id in served:
            result.append(d)
    # Fallback: if no drivers assigned to zone, return all online drivers
    if not result:
        result = all_online
    return result


def find_nearest_drivers(lat: float, lng: float, zone_id: str,
                          max_results: int = 10) -> list:
    """
    Find available drivers sorted by distance from pickup point.
    Prioritizes zone-assigned drivers, falls back to all online drivers.
    """
    drivers = get_available_drivers_in_zone(zone_id)
    with_dist = []
    for d in drivers:
        dlat = float(d.get('lat', 0) or 0)
        dlng = float(d.get('lng', 0) or 0)
        if dlat == 0 and dlng == 0:
            dist = 9999  # no GPS — put at end
        else:
            dist = haversine(lat, lng, dlat, dlng)
        with_dist.append({**d, '_distance_km': round(dist, 2)})

    with_dist.sort(key=lambda d: d['_distance_km'])
    return with_dist[:max_results]


def get_zone_status(zone: dict) -> dict:
    """
    Returns status info for a zone: driver count, active bookings, etc.
    """
    zone_id   = zone['_id']
    online    = get_available_drivers_in_zone(zone_id)
    active_bk = db.find('bookings', {'zone_id': zone_id, 'status': 'in_progress'})
    pending   = db.find('bookings', {'zone_id': zone_id, 'status': 'pending'})
    return {
        'zone_id':         zone_id,
        'zone_name':       zone.get('name', ''),
        'online_drivers':  len(online),
        'active_rides':    len(active_bk),
        'pending_bookings':len(pending),
        'active':          zone.get('active', True),
    }
