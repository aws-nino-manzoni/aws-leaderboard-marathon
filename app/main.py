from flask import Flask, request, jsonify, render_template
import redis

app = Flask(__name__)

# POSODOBI IP, če se spremeni Redis EC2
r = redis.Redis(host='10.0.2.190', port=6379, decode_responses=True) #Zasebni IP Redis

# Shrani checkpoint
@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.get_json()
        name = data['name']
        checkpoint = data['checkpoint']
        time = data['time']
        r.hset(f"runner:{name}", checkpoint, time)
        return jsonify({"message": f"Checkpoint {checkpoint} recorded for {name}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Leaderboard JSON
@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    base_url = 'https://marathon-leaderboard-images.s3.eu-central-1.amazonaws.com/'

    distance_km = {
        "5km": 5,
        "10km": 10,
        "21km": 21.1,
        "30km": 30,
        "finish": 42.2
    }

    runners = []
    for key in r.scan_iter("runner:*"):
        name = key.split(":")[1]
        checkpoints = r.hgetall(key)

        # Pretvori vse čase v float
        checkpoints = {cp: float(t) for cp, t in checkpoints.items() if cp in distance_km}

        if not checkpoints:
            continue

        # Najdaljši dosežen checkpoint
        longest_cp = max(checkpoints.keys(), key=lambda cp: distance_km.get(cp, 0))
        finish_time = checkpoints[longest_cp]
        km = distance_km.get(longest_cp, 0)

        if km == 0:
            continue

        pace = finish_time / km  # sekunde na km
        pace_min = int(pace // 60)
        pace_sec = int(pace % 60)
        pace_formatted = f"{pace_min}:{pace_sec:02d} min/km"

        runners.append({
            "name": name,
            "image": f"{base_url}{name.lower()}.png",
            "checkpoints": checkpoints,
            "total_time_sec": finish_time,
            "distance_km": km,
            "pace_sec_per_km": round(pace, 2),
            "pace_formatted": pace_formatted
        })

    # Sortiranje po času
    sorted_runners = sorted(runners, key=lambda x: x['total_time_sec'])

    return jsonify(sorted_runners), 200

# HTML prikaz
@app.route('/leaderboard.html')
def leaderboard_page():
    return render_template('leaderboard.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
