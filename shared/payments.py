"""
payments.py — Razorpay integration helper.
Handles: order creation, payment verification, recording, and PAYOUTS via Razorpay X.

PAYOUT REQUIREMENTS (Razorpay X):
  - Activate Razorpay X in your Razorpay dashboard
  - Use same KEY_ID but RAZORPAY_X_KEY_SECRET for payout calls
  - Requires KYC completion and minimum balance in Razorpay X account
"""
import hmac, hashlib, requests
import razorpay
from shared.config import Config
from shared import db

# ── Standard Razorpay (payment collection) ────────────────────────────────────
client = razorpay.Client(
    auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET)
)

def create_order(amount_inr: float, booking_id: str, notes: dict = None) -> dict:
    """Create Razorpay order. amount_inr in rupees → converts to paise."""
    order = client.order.create({
        "amount":   int(amount_inr * 100),
        "currency": "INR",
        "receipt":  booking_id,
        "notes":    notes or {},
    })
    return order

def verify_payment(razorpay_order_id: str,
                   razorpay_payment_id: str,
                   razorpay_signature: str) -> bool:
    """Verify Razorpay webhook signature."""
    msg = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected = hmac.new(
        Config.RAZORPAY_KEY_SECRET.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, razorpay_signature)

def record_payment(booking_id: str, razorpay_order_id: str,
                   razorpay_payment_id: str, amount: float,
                   status: str = "captured") -> dict:
    return db.insert_one("payments", {
        "booking_id":          booking_id,
        "razorpay_order_id":   razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "amount":              amount,
        "status":              status,
    })

# ── Razorpay X Payouts (driver withdrawals) ───────────────────────────────────

RZP_X_BASE = "https://api.razorpay.com/v1"

def _rzp_headers():
    """Auth headers for Razorpay X API calls."""
    return {"Content-Type": "application/json"}

def _rzp_auth():
    return (Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET)

def create_razorpay_contact(driver: dict) -> dict | None:
    """
    Create a Razorpay Contact for the driver.
    Contact = the person who will receive the payout.
    Returns contact dict with 'id' field, or None on failure.
    """
    payload = {
        "name":         driver.get('name', ''),
        "email":        driver.get('email', ''),
        "contact":      driver.get('phone', ''),
        "type":         "vendor",
        "reference_id": driver['_id'][:16],
        "notes": {
            "driver_id":      driver['_id'],
            "vehicle_number": driver.get('vehicle_number', ''),
        }
    }
    try:
        resp = requests.post(
            f"{RZP_X_BASE}/contacts",
            json=payload,
            auth=_rzp_auth(),
            headers=_rzp_headers(),
            timeout=15
        )
        data = resp.json()
        if data.get('id'):
            return data
        return None
    except Exception as e:
        print(f"[Razorpay] create_contact error: {e}")
        return None

def create_fund_account_upi(contact_id: str, upi_id: str) -> dict | None:
    """
    Create a Fund Account linked to a Razorpay Contact using UPI.
    Fund Account = the specific bank/UPI where money is sent.
    """
    payload = {
        "contact_id":    contact_id,
        "account_type":  "vpa",
        "vpa": {
            "address": upi_id
        }
    }
    try:
        resp = requests.post(
            f"{RZP_X_BASE}/fund_accounts",
            json=payload,
            auth=_rzp_auth(),
            headers=_rzp_headers(),
            timeout=15
        )
        data = resp.json()
        return data if data.get('id') else None
    except Exception as e:
        print(f"[Razorpay] create_fund_account_upi error: {e}")
        return None

def create_fund_account_bank(contact_id: str, account_no: str,
                              ifsc: str, account_name: str) -> dict | None:
    """
    Create a Fund Account linked to a Razorpay Contact using bank account.
    """
    payload = {
        "contact_id":   contact_id,
        "account_type": "bank_account",
        "bank_account": {
            "name":           account_name,
            "ifsc":           ifsc,
            "account_number": account_no,
        }
    }
    try:
        resp = requests.post(
            f"{RZP_X_BASE}/fund_accounts",
            json=payload,
            auth=_rzp_auth(),
            headers=_rzp_headers(),
            timeout=15
        )
        data = resp.json()
        return data if data.get('id') else None
    except Exception as e:
        print(f"[Razorpay] create_fund_account_bank error: {e}")
        return None

def trigger_payout(fund_account_id: str, amount_inr: float,
                   driver_name: str, driver_id: str) -> dict | None:
    """
    Trigger actual payout via Razorpay X.
    amount_inr in rupees → paise. Returns payout dict or None.

    IMPORTANT: Razorpay X must be activated and have balance.
    Mode: 'IMPS' for bank (24×7), 'UPI' for UPI.
    """
    payload = {
        "account_number": Config.RAZORPAY_X_ACCOUNT,  # your Razorpay X account number
        "fund_account_id": fund_account_id,
        "amount": int(amount_inr * 100),
        "currency": "INR",
        "mode": "UPI",          # or "IMPS" for bank transfers
        "purpose": "payout",
        "queue_if_low_balance": True,
        "reference_id": f"drv_{driver_id[:8]}_{int(amount_inr)}",
        "narration": f"E-TukTukGo earnings - {driver_name}",
        "notes": {
            "driver_id": driver_id,
            "platform":  "etuktukgo"
        }
    }
    try:
        resp = requests.post(
            f"{RZP_X_BASE}/payouts",
            json=payload,
            auth=_rzp_auth(),
            headers=_rzp_headers(),
            timeout=20
        )
        data = resp.json()
        return data if data.get('id') else None
    except Exception as e:
        print(f"[Razorpay] trigger_payout error: {e}")
        return None

def get_payout_status(payout_id: str) -> dict | None:
    """Check status of a previously initiated payout."""
    try:
        resp = requests.get(
            f"{RZP_X_BASE}/payouts/{payout_id}",
            auth=_rzp_auth(),
            timeout=10
        )
        return resp.json()
    except Exception:
        return None
