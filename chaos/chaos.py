#!/usr/bin/env python3
"""
Chaos injection tool for ecom-sre-pulse.
Usage:
  python chaos.py enable payment
  python chaos.py enable all
  python chaos.py disable all
"""
import sys
import requests

SERVICES = {
    "payment": "http://localhost:8001",
    "product-catalog": "http://localhost:8002",
    "order-service": "http://localhost:8003",
}

def toggle_chaos(action: str, target: str):
    targets = list(SERVICES.items()) if target == "all" else [(target, SERVICES[target])]
    for name, url in targets:
        try:
            resp = requests.post(f"{url}/chaos/{action}", timeout=3)
            print(f"[{name}] chaos {action}: {resp.json()}")
        except Exception as e:
            print(f"[{name}] ERROR: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("enable", "disable"):
        print("Usage: python chaos.py <enable|disable> <service|all>")
        sys.exit(1)
    action, target = sys.argv[1], sys.argv[2]
    if target != "all" and target not in SERVICES:
        print(f"Unknown service: {target}. Valid: {list(SERVICES)}")
        sys.exit(1)
    toggle_chaos(action, target)
