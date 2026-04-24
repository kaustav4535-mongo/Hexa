import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')

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
    PLATFORM_COMMISSION = float(os.getenv('PLATFORM_COMMISSION', '2.0'))

    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db.json')
