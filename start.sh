#!/data/data/com.termux/files/usr/bin/bash
# start.sh — Termux interactive launcher for E-TukTukGo v2
echo ""
echo "🛺  E-TukTukGo v2 — Termux Launcher"
echo "======================================"

# Install deps if needed
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install flask python-dotenv requests razorpay --break-system-packages 2>/dev/null || \
    pip install flask python-dotenv requests razorpay
fi

# Seed DB if it doesn't exist
if [ ! -f "db.json" ]; then
    echo "🌱 First run — seeding database..."
    python seed_db.py
fi

echo ""
echo "  1) Customer Portal  → http://127.0.0.1:5001"
echo "  2) Driver Portal    → http://127.0.0.1:5002"
echo "  3) Admin Portal     → http://127.0.0.1:5003"
echo "  4) All 3 Portals"
echo ""
read -p "Choose [1-4]: " choice

case $choice in
  1) python customer_portal/app.py ;;
  2) python driver_portal/app.py ;;
  3) python admin_portal/app.py ;;
  4) python run_all.py ;;
  *) echo "Invalid choice"; exit 1 ;;
esac
