#!/usr/bin/env python3
"""
run_all.py — Start all 3 E-TukTukGo portals at once.
Usage:  python run_all.py
        python run_all.py --seed    (also seeds db.json first)

Portals:
  Customer  → http://127.0.0.1:5001
  Driver    → http://127.0.0.1:5002
  Admin     → http://127.0.0.1:5003
"""
import sys, os, subprocess, time, signal, threading

ROOT = os.path.dirname(os.path.abspath(__file__))

PORTALS = [
    ("Customer Portal", ["python", "customer_portal/app.py"], 5001),
    ("Driver Portal",   ["python", "driver_portal/app.py"],   5002),
    ("Admin Portal",    ["python", "admin_portal/app.py"],    5003),
]

procs = []

def print_banner():
    print("\n" + "═"*56)
    print("  🛺  E-TukTukGo — Starting All Portals")
    print("═"*56)

def start_portal(name, cmd, port):
    p = subprocess.Popen(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    procs.append(p)

    def stream():
        for line in p.stdout:
            prefix = f"[{name[:8]}] "
            print(prefix + line, end='')

    t = threading.Thread(target=stream, daemon=True)
    t.start()
    time.sleep(0.4)
    print(f"  ✅  {name:20s} → http://127.0.0.1:{port}")

def shutdown(sig, frame):
    print("\n\n🛑  Shutting down all portals...")
    for p in procs:
        p.terminate()
    sys.exit(0)

if __name__ == "__main__":
    if "--seed" in sys.argv or "-s" in sys.argv:
        print("🌱 Seeding database...")
        subprocess.run(["python", "seed_db.py"], cwd=ROOT)
        print()

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print_banner()
    for name, cmd, port in PORTALS:
        start_portal(name, cmd, port)

    print("═"*56)
    print("  🔑  Admin login: admin@etuktuk.in / Admin@1234")
    print("  Ctrl+C to stop all portals")
    print("═"*56 + "\n")

    # Keep alive
    try:
        while True:
            time.sleep(1)
            # Restart any crashed portal
            for i, (name, cmd, port) in enumerate(PORTALS):
                if procs[i].poll() is not None:
                    print(f"  ⚠️  {name} crashed, restarting...")
                    start_portal(name, cmd, port)
    except KeyboardInterrupt:
        shutdown(None, None)
