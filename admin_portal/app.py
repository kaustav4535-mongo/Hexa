"""
Super Admin Portal — Port 5003
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from shared.config import Config
from admin_portal.routes.auth      import admin_auth_bp
from admin_portal.routes.dashboard import admin_dash_bp
from admin_portal.routes.users     import admin_users_bp
from admin_portal.routes.drivers   import admin_drivers_bp
from admin_portal.routes.bookings  import admin_bookings_bp
from admin_portal.routes.pricing   import admin_pricing_bp
from admin_portal.routes.payments  import admin_payments_bp
from admin_portal.routes.settings  import admin_settings_bp
from shared import db

def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    app.config.from_object(Config)
    app.config['SESSION_COOKIE_NAME'] = 'etuktuk_admin'

    app.register_blueprint(admin_auth_bp)
    app.register_blueprint(admin_dash_bp,     url_prefix='/dashboard')
    app.register_blueprint(admin_users_bp,    url_prefix='/users')
    app.register_blueprint(admin_drivers_bp,  url_prefix='/drivers')
    app.register_blueprint(admin_bookings_bp, url_prefix='/bookings')
    app.register_blueprint(admin_pricing_bp,  url_prefix='/pricing')
    app.register_blueprint(admin_payments_bp, url_prefix='/payments')
    app.register_blueprint(admin_settings_bp, url_prefix='/settings')

    # ── Global context: pending_count available on every admin page ──────────
    @app.context_processor
    def inject_pending_count():
        return {
            'pending_count':    db.count('drivers', {'approval': 'pending'}),
            'withdrawal_count': db.count('withdrawals', {'status': 'pending'}),
        }

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
