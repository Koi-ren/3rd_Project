# server.py
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn
import json
import math
from typing import List, Tuple
import asyncio

app = FastAPI()

WORLD_SIZE = 300  # 300x300 미터

# 더미 데이터 (실제 A* 알고리즘과 장애물 데이터를 대체)
class Tank:
    def __init__(self):
        self.current_position = (0, 0)
        self.current_heading = 0
        self.waypoints = [(0, 0), (100, 100), (200, 200), (300, 300)]  # A* 경로 예시
        self.actual_path = [(0, 0), (50, 50), (100, 100)]  # 실제 경로 예시
        self.grid = type('Grid', (), {'original_obstacles': [
            {'x_min': 50, 'x_max': 100, 'z_min': 50, 'z_max': 100},
            {'x_min': 200, 'x_max': 250, 'z_min': 200, 'z_max': 250}
        ]})()

    async def update_position(self):
        # 전차 위치를 주기적으로 업데이트 (시뮬레이션)
        while True:
            if self.waypoints:
                # 다음 웨이포인트로 이동
                target = self.waypoints[min(len(self.waypoints)-1, len(self.actual_path))]
                curr_x, curr_z = self.current_position
                target_x, target_z = target
                # 간단한 선형 이동
                dx = (target_x - curr_x) * 0.1
                dz = (target_z - curr_z) * 0.1
                self.current_position = (curr_x + dx, curr_z + dz)
                self.actual_path.append(self.current_position)
                if math.hypot(target_x - curr_x, target_z - curr_z) < 5:
                    self.actual_path = self.actual_path[-10:]  # 메모리 절약
            await asyncio.sleep(0.1)

    def get_visualization_data(self):
        return {
            'current_position': self.current_position,
            'current_heading': self.current_heading,
            'waypoints': self.waypoints,
            'actual_path': self.actual_path,
            'obstacles': self.grid.original_obstacles
        }

tank = Tank()

@app.get("/")
async def get():
    with open("index.html", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # 전차 위치 업데이트 태스크 시작
        asyncio.create_task(tank.update_position())
        while True:
            # 클라이언트로부터 목적지 수신
            data = await websocket.receive_text()
            if data:
                goal = json.loads(data)
                # 새 목적지로 웨이포인트 업데이트 (A* 알고리즘 호출 대신 더미 데이터)
                tank.waypoints = [(tank.current_position[0], tank.current_position[1]), (goal['x'], goal['z'])]
            
            # 시각화 데이터 전송
            vis_data = tank.get_visualization_data()
            await websocket.send_json(vis_data)
            await asyncio.sleep(0.1)  # 10fps로 업데이트
    except Exception as e:
        print(f"WebSocket 에러: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)