# app.py
from flask import Flask, request, jsonify
from utills import sharedData

app = Flask(__name__)

@app.route('/info', methods=['POST'])
def info():
    """시뮬레이터에서 데이터를 받아 마지막 명령어와 연관 짓습니다."""
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    sharedData.set_data(data)
    app.logger.info("Received /info data: %s", data)
    print("Received /info data:", data)
    return jsonify({"status": "success", "message": "Data received"}), 200

@app.route('/get_data', methods=['GET'])
def get_data():
    """저장된 데이터를 반환합니다."""
    data = sharedData.get_data()
    if data is not None:
        return jsonify({"status": "success", "data": data}), 200
    return jsonify({"status": "no_data", "message": "No data available"}), 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)