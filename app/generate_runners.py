import requests
import random
import time

API_URL = "http://<public-ip-of-flask>:5000/submit"

NAMES = ["Nino", "Tina", "Matej", "Anja", "Jure", "Sara", "Luka", "Petra", "David", "Eva", "Ana"]
DISTANCES = ["10km", "21km", "42km"]
CHECKPOINTS_BY_DISTANCE = {
    "10km": ["5km", "10km"],
    "21km": ["5km", "10km", "21km"],
    "42km": ["5km", "10km", "21km", "30km", "finish"]
}

def generate_runner_data():
    name = random.choice(NAMES) + str(random.randint(1, 999))
    age = random.randint(18, 60)
    gender = random.choice(["M", "F"])
    distance = random.choice(DISTANCES)
    start_number = random.randint(1000, 9999)

    checkpoints = CHECKPOINTS_BY_DISTANCE[distance]
    base_time = 300  # sekunde za prvih 5km
    times = {}

    for cp in checkpoints:
        base_time += random.randint(200, 800)  # dodamo realno variacijo
        times[cp] = base_time

    return {
        "name": name,
        "age": age,
        "gender": gender,
        "distance": distance,
        "start_number": start_number,
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
        res = requests.post(API_URL, json=payload)
        print(f"{name} - {cp}: {res.status_code}")

if __name__ == "__main__":
    for _ in range(20):  # ustvari 20 tekačev
        r = generate_runner_data()
        send_checkpoints(r)
        time.sleep(0.2)  # rahla pavza, da se podatki lepo obdelajo
