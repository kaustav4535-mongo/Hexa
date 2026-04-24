import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from flask import Blueprint, render_template
driver_public_bp = Blueprint('driver_public', __name__)

@driver_public_bp.route('/about')
def about():
    return render_template('driver/about_us.html')

@driver_public_bp.route('/terms')
def terms():
    return render_template('driver/terms.html')

@driver_public_bp.route('/install')
def install():
    return render_template('driver/install.html')

@driver_public_bp.route('/connect')
def connect():
    return render_template('driver/connect.html')
