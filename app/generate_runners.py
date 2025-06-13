import requests
import random
import time

API_URL = "http://3.124.1.132:5000/submit"  # ⬅️ Zamenjaj s svojim IP naslovom

NAMES = ["Nino", "Tina", "Matej", "Anja", "Jure", "Sara", "Luka", "Petra", "David", "Eva"]
DISTANCES = ["10km", "21km", "42km"]
CHECKPOINTS_BY_DISTANCE = {
    "10km": ["5km", "10km"],
    "21km": ["5km", "10km", "21km"],
    "42km": ["5km", "10km", "21km", "30km", "finish"]
}

def generate_runner_data():
    name = random.choice(NAMES) + str(random.randint(1, 999))
    distance = random.choice(DISTANCES)
    checkpoints = CHECKPOINTS_BY_DISTANCE[distance]
    times = {}
    total_time = 0

    for cp in checkpoints:
        if cp == "5km":
            segment_time = random.randint(16 * 60, 50 * 60)
        elif cp == "10km":
            segment_time = random.randint(18 * 60, 45 * 60)
        elif cp == "21km":
            segment_time = random.randint(40 * 60, 80 * 60)
        elif cp == "30km":
            segment_time = random.randint(30 * 60, 60 * 60)
        elif cp == "finish":
            segment_time = random.randint(35 * 60, 70 * 60)
        else:
            segment_time = random.randint(10 * 60, 20 * 60)

        total_time += segment_time
        print(f"{name} | {cp}: segment={segment_time}, total={total_time}")
        times[cp] = total_time

    return {
        "name": name,
        "checkpoints": times
    }

def send_checkpoints(runner):
    name = runner["name"]
    for cp, t in runner["checkpoints"].items():
        payload = {
            "name": name,
            "checkpoint": cp,
            "time": t
        }
        try:
            res = requests.post(API_URL, json=payload)
            print(f"Submitted {name} - {cp}: {res.status_code} | {res.text}")
        except Exception as e:
            print(f"Error submitting {name} - {cp}: {e}")

if __name__ == "__main__":
    for _ in range(20):
        r = generate_runner_data()
        send_checkpoints(r)
        time.sleep(0.2)
