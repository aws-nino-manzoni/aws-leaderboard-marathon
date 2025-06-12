from flask import Flask, request, jsonify
import redis

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    name = data['name']
    time = float(data['time'])
    r.zadd('leaderboard', {name: time})
    return jsonify({'message': 'Result submitted'}), 200

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    top = r.zrange('leaderboard', 0, -1, withscores=True)
    return jsonify(top), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
