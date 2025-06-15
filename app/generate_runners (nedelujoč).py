import random
import requests
import argparse
import time
import pymysql

API_URL = "http://52.59.234.124:5000/submit"

# MySQL povezava
MYSQL_CONFIG = {
    "host": "marathon-db.cz4kumcau3h2.eu-central-1.rds.amazonaws.com",
    "user": "admin",
    "password": "rdsmysql",
    "database": "leaderboard_db"
}

names = ["Nino", "Eva", "Sara", "Luka", "Tina", "Anja", "David", "Petra", "Jure", "Matej", "Ana"]
checkpoints = ["5km", "10km", "21km", "30km", "finish"]
checkpoint_dist = {
    "5km": 5,
    "10km": 5,
    "21km": 11,
    "30km": 9,
    "finish": 12.2
}

def reset_mysql():
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM checkpoints")
        conn.commit()
        conn.close()
        print("✅ MySQL: Vsi podatki izbrisani.")
    except Exception as e:
        print("⚠️ Napaka pri brisanju podatkov iz MySQL:", e)

def reset_redis():
    try:
        requests.post("http://localhost:5000/reset")  # Flask /reset endpoint
        print("✅ Redis: Vsi podatki izbrisani.")
    except Exception as e:
        print("⚠️ Napaka pri brisanju podatkov iz Redis:", e)

def send_checkpoints(runner):
    name = runner["name"]
    total_time = 0
    for cp in runner["checkpoints"]:
        segment_time = random.randint(4 * 60, 10 * 60) * checkpoint_dist[cp]
        total_time += int(segment_time)
        payload = {
            "name": name,
            "checkpoint": cp,
            "time": total_time
        }
        try:
            res = requests.post(API_URL, json=payload)
            print(f"Submitted {name} - {cp}: {res.status_code} | {res.json()}")
        except Exception as e:
            print(f"❌ Napaka pri pošiljanju {name} - {cp}: {e}")

def generate_runners(count=30):
    for _ in range(count):
        name = f"{random.choice(names)}{random.randint(1, 999)}"
        runner = {"name": name, "checkpoints": ["5km", "10km"]}
        if random.random() < 0.7:
            runner["checkpoints"].append("21km")
        if random.random() < 0.5:
            runner["checkpoints"].append("30km")
        if "30km" in runner["checkpoints"] or random.random() < 0.3:
            runner["checkpoints"].append("finish")
        send_checkpoints(runner)
        time.sleep(0.2)  # rahla zakasnitev

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Pobriši vse obstoječe podatke pred generacijo")
    args = parser.parse_args()

    if args.reset:
        reset_mysql()
        reset_redis()

    generate_runners()
