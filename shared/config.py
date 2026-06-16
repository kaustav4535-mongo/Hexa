import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')

    # Feature flags
    USE_MONGO = os.getenv('USE_MONGO', 'false').lower() in ('1', 'true', 'yes')
    SCHEDULER_ENABLED = os.getenv('SCHEDULER_ENABLED', 'true').lower() in ('1', 'true', 'yes')
    WTF_CSRF_ENABLED = os.getenv('WTF_CSRF_ENABLED', 'true').lower() in ('1', 'true', 'yes')

    CLIENT_APP_URL = os.getenv('CLIENT_APP_URL', 'http://127.0.0.1:5001')
    OWNER_APP_URL  = os.getenv('OWNER_APP_URL',  'http://127.0.0.1:5002')
    ADMIN_APP_URL  = os.getenv('ADMIN_APP_URL',  'http://127.0.0.1:5003')

    RAZORPAY_KEY_ID     = os.getenv('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')

    GOOGLE_CLIENT_ID           = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET       = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI_CLIENT = os.getenv('GOOGLE_REDIRECT_URI_CLIENT', '')
    GOOGLE_REDIRECT_URI_OWNER  = os.getenv('GOOGLE_REDIRECT_URI_OWNER', '')
    GOOGLE_REDIRECT_URI_ADMIN  = os.getenv('GOOGLE_REDIRECT_URI_ADMIN', '')

    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY    = os.getenv('CLOUDINARY_API_KEY', '')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', '')

    # MapTiler — two keys: satellite (hybrid-v4) + street (streets-v2)
    MAPTILER_KEY_SAT    = os.getenv('MAPTILER_KEY_SAT',    '8DcBKk2W2VGTtOYBBBgk')
    MAPTILER_KEY_STREET = os.getenv('MAPTILER_KEY_STREET', 'EKwK8akvOHJ42vwjnWyM')
    MAPTILER_KEY        = os.getenv('MAPTILER_KEY',        '8DcBKk2W2VGTtOYBBBgk')

    # IPInfo — city-level location fallback when GPS denied
    IPINFO_TOKEN = os.getenv('IPINFO_TOKEN', '60252ce1b807d2')

    # Razorpay X (payouts) — your Razorpay X current account number
    RAZORPAY_X_ACCOUNT = os.getenv('RAZORPAY_X_ACCOUNT', '')

    # Platform commission — flat ₹2 per completed ride
    # Deducted from driver wallet when ride completes.
    # For cash rides: recorded as pending, collected during weekly settlement.
    PLATFORM_COMMISSION = max(0.0, float(os.getenv('PLATFORM_COMMISSION', '2.0')))

    # MongoDB (optional)
    MONGO_URI = os.getenv('MONGO_URI', '')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'etuktukgo')

    # Quote rate limiting
    QUOTE_COOLDOWN_SECONDS = int(os.getenv('QUOTE_COOLDOWN_SECONDS', '30'))

    # Booking expiry (seconds)
    BOOKING_EXPIRY_SECONDS = int(os.getenv('BOOKING_EXPIRY_SECONDS', '600'))
    BOOKING_EXPIRY_WARNING_SECONDS = int(os.getenv('BOOKING_EXPIRY_WARNING_SECONDS', '420'))

    # India coordinate bounds (rough bounding box)
    INDIA_LAT_MIN = float(os.getenv('INDIA_LAT_MIN', '6.0'))
    INDIA_LAT_MAX = float(os.getenv('INDIA_LAT_MAX', '37.0'))
    INDIA_LNG_MIN = float(os.getenv('INDIA_LNG_MIN', '68.0'))
    INDIA_LNG_MAX = float(os.getenv('INDIA_LNG_MAX', '98.0'))

    # Notifications (Twilio / MSG91)
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER', '')

    MSG91_AUTH_KEY = os.getenv('MSG91_AUTH_KEY', '')
    MSG91_SENDER_ID = os.getenv('MSG91_SENDER_ID', '')
    MSG91_TEMPLATE_ID = os.getenv('MSG91_TEMPLATE_ID', '')

    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db.json')
