from flask import Flask, request, jsonify
import redis

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    name = data['name']
    checkpoint = data['checkpoint']
    time = float(data['time'])

    r.hset(f'runner:{name}', checkpoint, time)
    return jsonify({'message': f'Checkpoint {checkpoint} recorded for {name}'}), 200

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
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

        valid_checkpoints = [cp for cp in checkpoints if cp in distance_km]
        if not valid_checkpoints:
            continue

        longest_cp = max(valid_checkpoints, key=lambda cp: distance_km[cp])
        finish_time = float(checkpoints[longest_cp])
        km = distance_km[longest_cp]

        pace = finish_time / km
        pace_min = int(pace // 60)
        pace_sec = int(pace % 60)
        pace_formatted = f"{pace_min}:{pace_sec:02d} min/km"

        runners.append({
            "name": name,
            "checkpoints": checkpoints,
            "total_time_sec": finish_time,
            "distance_km": km,
            "pace_sec_per_km": round(pace, 2),
            "pace_formatted": pace_formatted
        })

    sorted_runners = sorted(runners, key=lambda x: x['total_time_sec'])
    return jsonify(sorted_runners), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
