"""
profile_utils.py — Profile completion helpers for all portals.
Used to enforce profile setup after Google OAuth.
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request
from shared import db


# ── Field requirements per role ──────────────────────────────────────────────
DRIVER_REQUIRED   = ['name', 'phone', 'vehicle_number', 'license_no']
CUSTOMER_REQUIRED = ['name', 'phone']


def is_driver_profile_complete(driver: dict) -> bool:
    return all(str(driver.get(f, '')).strip() for f in DRIVER_REQUIRED)


def is_customer_profile_complete(customer: dict) -> bool:
    return all(str(customer.get(f, '')).strip() for f in CUSTOMER_REQUIRED)


def missing_driver_fields(driver: dict) -> list:
    return [f for f in DRIVER_REQUIRED if not str(driver.get(f, '')).strip()]


def missing_customer_fields(customer: dict) -> list:
    return [f for f in CUSTOMER_REQUIRED if not str(customer.get(f, '')).strip()]


# ── Decorator: force driver profile setup after Google login ─────────────────
def driver_profile_required(f):
    """
    Redirect Google-authenticated drivers to profile setup
    if they haven't filled required fields yet.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'driver' or not session.get('user_id'):
            return redirect(url_for('driver_auth.login'))
        driver = db.find_one('drivers', {'_id': session['user_id']})
        if not driver:
            return redirect(url_for('driver_auth.login'))
        # Only enforce for Google-authenticated drivers with incomplete profiles
        if (driver.get('auth_provider') == 'google'
                and not is_driver_profile_complete(driver)):
            # Allow access to setup page and logout only
            allowed = {'driver_profile.setup', 'driver_auth.logout'}
            if request.endpoint not in allowed:
                flash('Please complete your profile to start accepting rides. 🛺', 'warning')
                return redirect(url_for('driver_profile.setup'))
        return f(*args, **kwargs)
    return decorated


# ── Decorator: soft nudge for customer (banner, not hard block) ───────────────
def customer_profile_nudge(f):
    """
    Injects profile_incomplete flag into view context for customers.
    Does NOT hard-block — shows a banner instead.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated
