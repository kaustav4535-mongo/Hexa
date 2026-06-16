"""
scheduler.py — Background tasks (booking expiry, cleanup)
"""
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from shared import db
from shared.config import Config

_scheduler = None
_started = False

def _parse_time(ts: str):
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None

def expire_open_bookings():
    """Expire open bookings with no quotes after a fixed timeout."""
    now = datetime.utcnow()
    open_bookings = db.find('bookings', {'status': 'open'})
    for b in open_bookings:
        created = _parse_time(b.get('created_at', ''))
        if not created:
            continue
        elapsed = (now - created).total_seconds()
        has_quotes = bool(b.get('driver_quotes'))
        if elapsed > Config.BOOKING_EXPIRY_SECONDS and not has_quotes:
            db.update_one('bookings', {'_id': b['_id']}, {
                'status': 'expired',
                'expired_reason': 'No driver quotes in 10 minutes'
            })

def start_scheduler():
    """Start the APScheduler background worker (idempotent)."""
    global _scheduler, _started
    if _started or not Config.SCHEDULER_ENABLED:
        return
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(expire_open_bookings, 'interval',
                       seconds=60, id='expire_open_bookings',
                       replace_existing=True, max_instances=1, coalesce=True)
    _scheduler.start()
    _started = True
