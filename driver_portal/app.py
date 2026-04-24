"""
Driver Portal — Port 5002
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from shared.config import Config
from driver_portal.routes.auth     import driver_auth_bp
from driver_portal.routes.dashboard import driver_dash_bp
from driver_portal.routes.rides    import driver_rides_bp
from driver_portal.routes.profile  import driver_profile_bp
from driver_portal.routes.earnings import driver_earnings_bp
from driver_portal.routes.public   import driver_public_bp

def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    app.config.from_object(Config)
    app.config['SESSION_COOKIE_NAME'] = 'etuktuk_driver'

    app.register_blueprint(driver_auth_bp)
    app.register_blueprint(driver_dash_bp,      url_prefix='/dashboard')
    app.register_blueprint(driver_rides_bp,     url_prefix='/rides')
    app.register_blueprint(driver_profile_bp,   url_prefix='/profile')
    app.register_blueprint(driver_earnings_bp,  url_prefix='/earnings')
    app.register_blueprint(driver_public_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
