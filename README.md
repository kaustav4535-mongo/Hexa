# 🛺 E-TukTukGo v2 — Electric Ride Booking Platform

> 3-portal Flask platform · MapTiler GPS · Razorpay · Google OAuth  
> Light / Dark / System theme · Payment locked until driver accepts

---

## 📁 Structure

```
etuktuk/
├── .env                        ← All credentials
├── db.json                     ← Auto-created JSON database
├── requirements.txt
├── seed_db.py                  ← Run once to create test data
├── run_all.py                  ← Start all 3 portals at once
├── start.sh                    ← Termux interactive launcher
│
├── shared/                     ← Used by all 3 portals
│   ├── config.py               ← Env vars incl. MapTiler + IPInfo
│   ├── db.py                   ← JSON DB (MongoDB-ready swap)
│   ├── auth.py                 ← Google OAuth + session helpers
│   ├── payments.py             ← Razorpay helpers
│   └── profile_utils.py        ← Profile completion guards
│
├── customer_portal/            ← Port 5001
├── driver_portal/              ← Port 5002
└── admin_portal/               ← Port 5003
```

---

## ⚡ Quick Start (Termux)

```bash
pip install -r requirements.txt
python seed_db.py
python run_all.py
```

Or interactive:
```bash
chmod +x start.sh && ./start.sh
```

---

## 🔑 Test Credentials

| Role     | Email                     | Password       | URL  |
|----------|---------------------------|----------------|------|
| Customer | customer1@etuktuk.in      | Customer@1234  | :5001|
| Driver   | driver1@etuktuk.in        | Driver@1234    | :5002|
| Admin    | admin@etuktuk.in          | Admin@1234     | :5003|

---

## ✨ v2 Features

| Feature | Detail |
|---|---|
| 🔒 Payment Lock | Payment unlocks ONLY after driver accepts — not before |
| 🗺️ MapTiler | Full GPS map on booking page, draggable pins, autocomplete, distance calc |
| 🌙 Dark/Light/System | 3-state theme toggle on all 3 portals |
| 🛺 TukTuk Hero | Your vehicle image on customer homepage |
| 👤 Profile Setup | Google login → forced profile setup for drivers |
| 📍 IPInfo | Auto-center map to user's city on page load |

---

## 🔒 Payment Flow

```
Customer books → payment_locked = True
Driver sees request → clicks Accept
  → payment_locked = False  (auto-unlocked)
Customer page polls every 7s → detects unlock
  → Pay button appears automatically
Customer pays → booking confirmed
```

---

## 🗺️ MapTiler Setup

Keys already in `.env`:
```
MAPTILER_KEY=EKwK8akvOHJ42vwjnWyM
IPINFO_TOKEN=60252ce1b807d2
```

Features used:
- `Streets` / `Streets Dark` map styles (auto-switches with theme)
- Forward + reverse geocoding
- Haversine distance calculation
- Draggable pickup/dropoff pins
- Address autocomplete (India-focused)
- Driver markers on homepage live map
- Mini-map on admin booking detail

---

## 💾 MongoDB Migration

Set these env vars and restart:
```
USE_MONGO=true
MONGO_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net
MONGO_DB_NAME=etuktukgo
```
All routes keep the same interface — zero refactoring needed.

## 🔐 Security & Ops Notes
- Set a strong `SECRET_KEY` in `.env` for production.
- CSRF protection is enabled (Flask-WTF). For fetch calls, send `X-CSRFToken`.
- Background scheduler auto-expires open bookings after 10 minutes.

## 📲 Driver Quote Notifications
Optional SMS/WhatsApp alerts when a driver sends a quote:
```
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=...

# Or MSG91
MSG91_AUTH_KEY=...
MSG91_SENDER_ID=...
```

---

## 💳 Razorpay Test Cards

- Card: `4111 1111 1111 1111`
- CVV: `123`  
- Expiry: Any future date
- UPI: `success@razorpay`

---

*E-TukTukGo v2 — Clean Electric Mobility 🌿*
# Hexa
