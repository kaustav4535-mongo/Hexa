"""
notifications.py — SMS/WhatsApp notifications (Twilio / MSG91).
"""
import re
import requests
from shared.config import Config

def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D+", "", phone or "")
    if len(digits) == 10:
        return f"+91{digits}"
    if digits.startswith("91") and len(digits) == 12:
        return f"+{digits}"
    if digits.startswith("0") and len(digits) == 11:
        return f"+91{digits[1:]}"
    return f"+{digits}" if digits else ""

def _send_twilio(to_phone: str, message: str) -> bool:
    if not (Config.TWILIO_ACCOUNT_SID and Config.TWILIO_AUTH_TOKEN and Config.TWILIO_FROM_NUMBER):
        return False
    try:
        resp = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{Config.TWILIO_ACCOUNT_SID}/Messages.json",
            data={"To": to_phone, "From": Config.TWILIO_FROM_NUMBER, "Body": message},
            auth=(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN),
            timeout=12
        )
        return resp.status_code in (200, 201)
    except Exception as e:
        print(f"[Notify] Twilio error: {e}")
        return False

def _send_msg91(to_phone: str, message: str) -> bool:
    if not (Config.MSG91_AUTH_KEY and Config.MSG91_SENDER_ID):
        return False
    try:
        payload = {
            "sender": Config.MSG91_SENDER_ID,
            "route": "4",
            "country": "91",
            "sms": [{"message": message, "to": [to_phone.replace("+91", "")]}],
        }
        resp = requests.post(
            "https://api.msg91.com/api/v2/sendsms",
            json=payload,
            headers={"authkey": Config.MSG91_AUTH_KEY, "Content-Type": "application/json"},
            timeout=12
        )
        return resp.status_code in (200, 201)
    except Exception as e:
        print(f"[Notify] MSG91 error: {e}")
        return False

def send_quote_notification(customer: dict, booking: dict, quote: dict) -> bool:
    """Notify customer when a driver sends a price quote."""
    phone = _normalize_phone(customer.get('phone', ''))
    if not phone:
        return False
    message = (
        f"🛺 New quote for your ride {booking.get('_id','')[:8].upper()}: "
        f"{quote.get('name','Driver')} offered ₹{float(quote.get('price', 0)):.0f}. "
        "Open E-TukTukGo to confirm."
    )
    return _send_twilio(phone, message) or _send_msg91(phone, message)
