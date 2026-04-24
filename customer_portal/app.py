"""
Customer Portal — Port 5001
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from shared.config import Config
from customer_portal.routes.auth   import auth_bp
from customer_portal.routes.home   import home_bp
from customer_portal.routes.booking import booking_bp
from customer_portal.routes.payment import payment_bp
from customer_portal.routes.profile import profile_bp

def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    app.config.from_object(Config)
    app.config['SESSION_COOKIE_NAME'] = 'etuktuk_customer'

    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp,    url_prefix='/auth')
    app.register_blueprint(booking_bp, url_prefix='/booking')
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(profile_bp, url_prefix='/profile')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
