# app.py
from flask import Flask, request, jsonify
from control_1 import GameServer  # server.py에서 GameServer 클래스 가져오기
from utills import sharedData, sharedKeyValue
import threading

app = Flask(__name__)

# /info 엔드포인트: 시뮬레이터로부터 데이터 수신
@app.route('/info', methods=['POST'])
def info():
    data = request.get_json(force=True)
    if not data:
        app.logger.error("No JSON received in /info")
        return jsonify({"error": "No JSON received"}), 400
    sharedData.set_data(data)
    app.logger.info("Received /info data: %s", data)
    print("Received /info data:", data)
    return jsonify({"status": "success", "message": "Data received"}), 200

# /update_position 엔드포인트: 위치 업데이트 (기존 코드 유지)
@app.route('/update_position', methods=['POST'])
def update_position():
    data = request.get_json(force=True)
    if not data:
        app.logger.error("No JSON received in /update_position")
        return jsonify({"error": "No JSON received"}), 400
    app.logger.info("Position updated: %s", data)
    return jsonify({"status": "success", "message": "Position updated"}), 200

# /get_data 엔드포인트: server.py에 데이터 제공
@app.route('/get_data', methods=['GET'])
def get_data():
    data = sharedData.get_data()
    if data is not None:
        app.logger.info("Returning /get_data: %s", data)
        return jsonify({"status": "success", "data": data}), 200
    app.logger.warning("No data available for /get_data")
    return jsonify({"status": "no_data", "message": "No data available"}), 404

# /get_move 엔드포인트: 시뮬레이터에 명령 전달
@app.route('/get_move', methods=['GET'])
def get_move():
    move = sharedKeyValue.get_key_value()
    if move is None:
        app.logger.warning("No move command available, returning STOP")
        print("No move command available, returning STOP")
        return jsonify({"move": "STOP"}), 200
    app.logger.info("Returning move command: %s", move)
    print(f"Returning move command: {move}, SharedKeyValue: {sharedKeyValue.get_key_value()}")
    return jsonify({"move": move}), 200

# /get_action 엔드포인트: get_move와 동일
@app.route('/get_action', methods=['GET'])
def get_action():
    return get_move()

if __name__ == "__main__":
    # GameServer를 백그라운드 스레드에서 실행
    server = GameServer()
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    # Flask 앱을 메인 스레드에서 실행
    app.run(host='0.0.0.0', port=5000)