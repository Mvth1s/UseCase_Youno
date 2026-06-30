"""
Script de warm-up : ping le backend toutes les 14 minutes pour eviter
le cold start Render free tier (les services s'endorment apres 15 min d'inactivite).

Usage : python warmup.py https://ton-backend.onrender.com
Peut tourner en local ou sur un cron gratuit (cron-job.org, UptimeRobot).
"""
import sys
import time
import urllib.request


def ping(url: str) -> None:
    try:
        with urllib.request.urlopen(f"{url}/health", timeout=10) as resp:
            print(f"[OK] {resp.status} -- {url}/health")
    except Exception as exc:
        print(f"[WARN] {exc}")


if __name__ == "__main__":
    url = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
    print(f"Warm-up actif sur {url} (intervalle : 14 min)")
    while True:
        ping(url)
        time.sleep(14 * 60)
