# app.py
import aiohttp
import asyncio
from control_1 import GameServer
from utils import sharedData, sharedKeyValue

async def run_flask():
    from flask import Flask, request, jsonify
    app = Flask(__name__)

    @app.route('/info', methods=['POST'])
    async def info():
        data = request.get_json(force=True)
        if not data:
            app.logger.error("No JSON received in /info")
            return jsonify({"error": "No JSON received"}), 400
        sharedData.set_data(data)
        app.logger.info("Received /info data: %s", data)
        print("Received /info data:", data)
        return jsonify({"status": "success", "message": "Data received"}), 200

    @app.route('/update_position', methods=['POST'])
    async def update_position():
        data = request.get_json(force=True)
        if not data:
            app.logger.error("No JSON received in /update_position")
            return jsonify({"error": "No JSON received"}), 400
        app.logger.info("Position updated: %s", data)
        return jsonify({"status": "success", "message": "Position updated"}), 200

    @app.route('/get_data', methods=['GET'])
    async def get_data():
        data = sharedData.get_data()
        if data is not None:
            app.logger.info("Returning /get_data: %s", data)
            return jsonify({"status": "success", "data": data}), 200
        app.logger.warning("No data available for /get_data")
        return jsonify({"status": "no_data", "message": "No data available"}), 404

    @app.route('/get_move', methods=['GET'])
    async def get_move():
        move = sharedKeyValue.get_key_value()
        if move is None:
            app.logger.warning("No move command available, returning STOP")
            print("No move command available, returning STOP")
            return jsonify({"move": "STOP"}), 200
        app.logger.info("Returning move command: %s", move)
        print(f"Returning move command: {move}, SharedKeyValue: {sharedKeyValue.get_key_value()}")
        return jsonify({"move": move}), 200

    @app.route('/get_action', methods=['GET'])
    async def get_action():
        return await get_move()

    # Flask를 비동기적으로 실행
    from flask_cors import CORS
    CORS(app)
    import hypercorn.config
    import hypercorn.asyncio
    config = hypercorn.config.Config()
    config.bind = ["0.0.0.0:5000"]
    await hypercorn.asyncio.serve(app, config)

async def main():
    server = GameServer()
    server_task = asyncio.create_task(asyncio.to_thread(server.run))
    flask_task = asyncio.create_task(run_flask())
    await asyncio.gather(server_task, flask_task)

if __name__ == "__main__":
    asyncio.run(main())