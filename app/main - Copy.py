from flask import Flask, request, jsonify, render_template, Response
import pymysql
import redis
import csv
import io

app = Flask(__name__)

# MySQL povezava (RDS)
db = pymysql.connect(
    host='marathon-db.cz4kumcau3h2.eu-central-1.rds.amazonaws.com',
    user='admin',
    password='rdsmysql',
    database='leaderboard_db'
)

# POSODOBI IP, če se spremeni Redis EC2
r = redis.Redis(host='10.0.2.190', port=6379, decode_responses=True)

distance_km = {
    "5km": 5,
    "10km": 10,
    "21km": 21.1,
    "30km": 30,
    "finish": 42.2
}

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.get_json()
        name = data['name']
        checkpoint = data['checkpoint']
        time_val = float(data['time'])

        # Redis zapis
        r.hset(f"runner:{name}", checkpoint, time_val)

        # MySQL zapis
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO checkpoints (runner_name, checkpoint, time_seconds) VALUES (%s, %s, %s)",
                (name, checkpoint, time_val)
            )
        db.commit()

        return jsonify({"message": f"Checkpoint {checkpoint} recorded for {name}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    runners = []
    for key in r.scan_iter("runner:*"):
        name = key.split(":")[1]
        checkpoints = r.hgetall(key)
        checkpoints = {cp: float(t) for cp, t in checkpoints.items() if cp in distance_km}
        if not checkpoints:
            continue
        longest_cp = max(checkpoints.keys(), key=lambda cp: distance_km.get(cp, 0))
        finish_time = checkpoints[longest_cp]
        km = distance_km.get(longest_cp, 0)
        if km == 0:
            continue
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

@app.route('/leaderboard/csv', methods=['GET'])
def leaderboard_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Distance (km)', 'Total Time (s)', 'Pace (min/km)', 'Checkpoints'])

    for key in r.scan_iter("runner:*"):
        name = key.split(":")[1]
        checkpoints = r.hgetall(key)
        checkpoints = {cp: float(t) for cp, t in checkpoints.items() if cp in distance_km}
        if not checkpoints:
            continue
        longest_cp = max(checkpoints.keys(), key=lambda cp: distance_km.get(cp, 0))
        finish_time = checkpoints[longest_cp]
        km = distance_km.get(longest_cp, 0)
        if km == 0:
            continue
        pace = finish_time / km
        pace_min = int(pace // 60)
        pace_sec = int(pace % 60)
        pace_formatted = f"{pace_min}:{pace_sec:02d} min/km"
        cp_str = "; ".join([f"{k}: {int(v)}s" for k, v in checkpoints.items()])
        writer.writerow([name, km, int(finish_time), pace_formatted, cp_str])

    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=leaderboard.csv"})

@app.route('/leaderboard.html')
def leaderboard_page():
    return render_template('leaderboard.html')

@app.route('/reset', methods=['POST'])
def reset_all():
    # Redis reset
    redis_deleted = 0
    for key in r.scan_iter("runner:*"):
        r.delete(key)
        redis_deleted += 1

    # MySQL reset
    try:
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM checkpoints")
        db.commit()
    except Exception as e:
        return jsonify({"error": f"MySQL error: {str(e)}"}), 500

    return jsonify({
        "message": f"Reset complete. Redis: {redis_deleted} runners deleted. MySQL: all rows deleted."
    }), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
