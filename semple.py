from flask import Flask, request, jsonify
import math
import random
import time
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List
import heapq

app = Flask(__name__)

current_position = None
destination = None
path = []
obstacles_list = []

@dataclass
class NavigationConfig:
    MOVE_STEP: float = 0.1
    TOLERANCE: float = 15.0
    LOOKAHEAD_MIN: float = 1.0
    LOOKAHEAD_MAX: float = 10.0
    HEADING_SMOOTHING: float = 0.8
    STEERING_SMOOTHING: float = 0.7
    GOAL_WEIGHT: float = 2.0
    SLOW_RADIUS: float = 50.0
    MAX_SPEED: float = 1.0
    MIN_SPEED: float = 0.1
    SPEED_FACTOR: float = 0.8
    WEIGHT_FACTORS: Dict[str, float] = None

    def __post_init__(self):
        if self.WEIGHT_FACTORS is None:
            self.WEIGHT_FACTORS = {"D": 0.5, "A": 0.5, "W": 0.5, "S": 1.0}

class NavigationController:
    def __init__(self, config: NavigationConfig):
        self.config = config
        self.current_position: Optional[Tuple[float, float]] = None
        self.current_heading: float = 0.0
        self.destination: Optional[Tuple[float, float]] = None
        self.last_command: Optional[str] = None
        self.last_steering: float = 0.0
        self.last_update_time: float = time.time()
        self.initial_distance: Optional[float] = None
        self.waypoints: List[Tuple[float, float]]
        self.current_waypoint_idx: int = 0
        self.completed: bool = False  # 경로 완료 여부 추적

    def update_position(self, position: str) -> Dict:
        try:
            x, y, z = map(float, position.split(","))
            new_position = (x, z)
            now = time.time()
            dt = now - self.last_update_time
            self.last_update_time = now

            if self.current_position:
                prev_x, prev_z = self.current_position
                dx, dz = x - prev_x, z - prev_z
                distance_moved = math.sqrt(dx**2 + dz**2)
                if distance_moved > 0.01:
                    new_heading = math.atan2(dx, dz)
                    self.current_heading = (
                        self.config.HEADING_SMOOTHING * self.current_heading +
                        (1 - self.config.HEADING_SMOOTHING) * new_heading
                    )
                    self.current_heading = math.atan2(
                        math.sin(self.current_heading), math.cos(self.current_heading)
                    )

            self.current_position = new_position
            return {
                "status": "OK",
                "current_position": self.current_position,
                "heading": math.degrees(self.current_heading)
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def update_waypoints(self, waypoints):
        self.waypoints = waypoints

    def set_destination(self, destination: str) -> Dict:
        try:
            x, y, z = map(float, destination.split(","))
            self.destination = (x, z)
            if self.current_position:
                curr_x, curr_z = self.current_position
                self.initial_distance = math.sqrt((x - curr_x) ** 2 + (z - curr_z) ** 2)
            return {
                "status": "OK",
                "destination": {"x": x, "y": y, "z": z},
                "initial_distance": self.initial_distance
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def _calculate_lookahead(self, distance: float) -> float:
        return min(
            self.config.LOOKAHEAD_MAX,
            max(self.config.LOOKAHEAD_MIN, distance * 0.5 + 5.0)
        )

    def _calculate_steering(self, curr_x: float, curr_z: float, dest_x: float, dest_z: float, lookahead_distance: float) -> Tuple[float, float]:
        goal_vector = np.array([dest_x - curr_x, dest_z - curr_z])
        goal_distance = np.linalg.norm(goal_vector)
        if goal_distance > 0:
            goal_vector = goal_vector / goal_distance

        target_vector = goal_vector * self.config.GOAL_WEIGHT
        target_vector_norm = np.linalg.norm(target_vector)
        if target_vector_norm > 0:
            target_vector = target_vector / target_vector_norm
            target_heading = math.atan2(target_vector[0], target_vector[1])
        else:
            target_heading = math.atan2(goal_vector[0], goal_vector[1])

        lookahead_x = curr_x + target_vector[0] * lookahead_distance
        lookahead_z = curr_z + target_vector[1] * lookahead_distance
        dx, dz = lookahead_x - curr_x, lookahead_z - curr_z
        target_heading = math.atan2(dx, dz)

        heading_error = target_heading - self.current_heading
        heading_error = math.atan2(math.sin(heading_error), math.cos(heading_error))
        curvature = 2.0 * math.sin(heading_error) / max(lookahead_distance, 0.01)
        steering = (
            self.config.STEERING_SMOOTHING * self.last_steering +
            (1 - self.config.STEERING_SMOOTHING) * curvature
        )
        return steering, heading_error

    def _calculate_speed(self, distance: float, abs_steering: float) -> float:
        base_speed = self.config.MAX_SPEED - abs_steering * self.config.SPEED_FACTOR
        if distance < self.config.SLOW_RADIUS * 0.5:
            speed = self.config.MAX_SPEED * distance / (self.config.SLOW_RADIUS * 0.5)
        else:
            speed = base_speed
        return max(self.config.MIN_SPEED, min(self.config.MAX_SPEED, speed))

    def _calculate_weights(self, steering: float, speed: float, heading_error: float, progress: float) -> Dict[str, float]:
        abs_steering = abs(steering)
        dynamic_weights = {
            "D": self.config.WEIGHT_FACTORS["D"] * (1 + abs_steering * 2) if steering > 0 else 0.0,
            "A": self.config.WEIGHT_FACTORS["A"] * (1 + abs_steering * 2) if steering < 0 else 0.0,
            "W": self.config.WEIGHT_FACTORS["W"] * speed,
            "S": self.config.WEIGHT_FACTORS["S"] if heading_error > math.pi * 0.6 else 0.0
        }
        for cmd in dynamic_weights:
            if dynamic_weights[cmd] > 0:
                dynamic_weights[cmd] *= (1 + progress * 0.5)
        return dynamic_weights

    def _update_position(self, speed: float, command: str, curr_x: float, curr_z: float) -> None:
        move_distance = self.config.MOVE_STEP * speed
        new_x, new_z = curr_x, curr_z
        if command == "D":
            new_x += move_distance * math.cos(self.current_heading + math.pi/2)
            new_z += move_distance * math.sin(self.current_heading + math.pi/2)
        elif command == "A":
            new_x += move_distance * math.cos(self.current_heading - math.pi/2)
            new_z += move_distance * math.sin(self.current_heading - math.pi/2)
        elif command == "W":
            new_x += move_distance * math.sin(self.current_heading)
            new_z += move_distance * math.cos(self.current_heading)
        elif command == "S":
            new_x -= move_distance * math.sin(self.current_heading)
            new_z -= move_distance * math.cos(self.current_heading)
        self.current_position = (new_x, new_z)

    def get_move(self) -> Dict:
        if self.current_position is None or self.completed:
            return {"move": "STOP", "weight": 1.0, "current_waypoint": self.current_waypoint_idx, "completed": self.completed}

        if self.destination is None:
            self.destination = self.waypoints[self.current_waypoint_idx]

        curr_x, curr_z = self.current_position
        dest_x, dest_z = self.destination
        distance = math.sqrt((dest_x - curr_x) ** 2 + (dest_z - curr_z) ** 2)

        # 목표 waypoint에 도달하면 다음 waypoint로 전환 또는 종료
        if distance < self.config.TOLERANCE:
            if self.current_waypoint_idx == len(self.waypoints) - 1:
                # 마지막 waypoint 도달 시 종료
                self.completed = True
                self.destination = None
                self.initial_distance = None
                return {
                    "move": "STOP",
                    "weight": 1.0,
                    "current_waypoint": self.current_waypoint_idx,
                    "completed": self.completed
                }
            else:
                # 다음 waypoint로 전환
                self.current_waypoint_idx += 1
                self.destination = self.waypoints[self.current_waypoint_idx]
                self.initial_distance = None
                dest_x, dest_z = self.destination
                distance = math.sqrt((dest_x - curr_x) ** 2 + (dest_z - curr_z) ** 2)

        lookahead_distance = self._calculate_lookahead(distance)
        steering, heading_error = self._calculate_steering(curr_x, curr_z, dest_x, dest_z, lookahead_distance)
        self.last_steering = steering
        speed = self._calculate_speed(distance, abs(steering))

        progress = max(0, 1 - distance / self.initial_distance) if self.initial_distance and distance > 0 else 0.0
        dynamic_weights = self._calculate_weights(steering, speed, heading_error, progress)

        commands = [cmd for cmd, w in dynamic_weights.items() if w > 0]
        if not commands:
            return {"move": "STOP", "weight": 1.0, "current_waypoint": self.current_waypoint_idx, "completed": self.completed}

        weights = [dynamic_weights[cmd] for cmd in commands]
        chosen_cmd = random.choices(commands, weights=weights, k=1)[0]
        self.last_command = chosen_cmd

        if chosen_cmd:
            self._update_position(speed, chosen_cmd, curr_x, curr_z)

        return {
            "move": chosen_cmd,
            "weight": dynamic_weights[chosen_cmd],
            "current_waypoint": self.current_waypoint_idx,
            "completed": self.completed
        }

class Node:
    def __init__(self, grid_x, grid_z):
        self.grid_x = grid_x
        self.grid_z = grid_z
        self.g_cost = 0
        self.h_cost = 0
        self.parent = None
        self.is_obstacle = False

    @property
    def f_cost(self):
        return self.g_cost + self.h_cost

    def __lt__(self, other):
        return self.f_cost < other.f_cost

class Grid:
    def __init__(self, width=300, height=300):
        self.width = width
        self.height = height
        self.grid = [[Node(x, z) for z in range(height)] for x in range(width)]

    def node_from_world_point(self, world_x, world_z):
        grid_x = max(0, min(int(world_x), self.width - 1))
        grid_z = max(0, min(int(world_z), self.height - 1))
        return self.grid[grid_x][grid_z]

    def set_obstacle(self, x_min, x_max, z_min, z_max):
        """사각형 영역을 장애물로 설정."""
        x_min = max(0, min(int(x_min), self.width - 1))
        x_max = max(0, min(int(x_max), self.width - 1))
        z_min = max(0, min(int(z_min), self.height - 1))
        z_max = max(0, min(int(z_max), self.height - 1))
        for x in range(x_min, x_max + 1):
            for z in range(z_min, z_max + 1):
                self.grid[x][z].is_obstacle = True

    def get_neighbors(self, node):
        neighbors = []
        for dx, dz in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_x, new_z = node.grid_x + dx, node.grid_z + dz
            if 0 <= new_x < self.width and 0 <= new_z < self.height:
                neighbor = self.grid[new_x][new_z]
                if not neighbor.is_obstacle:
                    neighbors.append((neighbor, dx, dz))
        return neighbors

class Pathfinding:
    def find_path(self, start_pos, target_pos, grid):
        start_node = grid.node_from_world_point(start_pos[0], start_pos[1])
        target_node = grid.node_from_world_point(target_pos[0], target_pos[1])
        
        if start_node.is_obstacle or target_node.is_obstacle:
            print("Warning: Start or target position is on an obstacle.")
            return []

        open_set = []
        heapq.heappush(open_set, (start_node.f_cost, id(start_node), start_node))
        open_set_nodes = {start_node}
        closed_set = set()

        while open_set:
            _, _, current_node = heapq.heappop(open_set)
            open_set_nodes.remove(current_node)
            closed_set.add(current_node)

            if current_node.grid_x == target_node.grid_x and current_node.grid_z == target_node.grid_z:
                return self.retrace_path(start_node, current_node)

            for neighbor, dx, dz in grid.get_neighbors(current_node):
                if neighbor in closed_set:
                    continue
                move_cost = 10
                new_cost = current_node.g_cost + move_cost
                if new_cost < neighbor.g_cost or neighbor not in open_set_nodes:
                    neighbor.g_cost = new_cost
                    dx_h = abs(neighbor.grid_x - target_node.grid_x)
                    dz_h = abs(neighbor.grid_z - target_node.grid_z)
                    neighbor.h_cost = (dx_h + dz_h) * 10
                    neighbor.parent = current_node
                    if neighbor not in open_set_nodes:
                        open_set_nodes.add(neighbor)
                        heapq.heappush(open_set, (neighbor.f_cost, id(neighbor), neighbor))
        return []

    def retrace_path(self, start_node, end_node):
        path = []
        current_node = end_node
        while current_node != start_node:
            path.append(current_node)
            current_node = current_node.parent
        path.append(start_node)
        path.reverse()
        return [(node.grid_x, node.grid_z) for node in path]

# Grid와 Pathfinding 초기화
pathfinding = Pathfinding()
grid = Grid(width=300, height=300)

# Flask 라우팅
nav_controller = NavigationController(NavigationConfig())

@app.route('/info', methods=['POST'])
def info():
    global current_position
    data = request.get_json()
    try:
        player_pos = data["playerPos"]
        x, z = float(player_pos["x"]), float(player_pos["z"])
        current_position = (x, z)
        print(f"/info received: playerPos={player_pos}")
    except (KeyError, ValueError, TypeError) as e:
        print(f"Error in /info: {e}")
        return jsonify({"status": "ERROR", "message": "Invalid data"}), 400

    return jsonify({"status": "OK"})

@app.route('/update_position', methods=['POST'])
def update_position():
    global current_position
    data = request.get_json()
    try:
        if "position" in data:
            x, y, z = map(float, data["position"].split(","))
            x = max(0, min(x, 300.0))
            z = max(0, min(z, 300.0))
            current_position = (x, z)
            print(f"/update_position received: position={current_position}")
            result = nav_controller.update_position(data["position"])
        return jsonify(result), 200
    except (KeyError, ValueError):
        print(f"Error in /update_position: Invalid position data")
        return jsonify({"status": "ERROR", "message": "Invalid position"}), 400

@app.route('/update_obstacle', methods=['POST'])
def update_obstacle():
    global grid, obstacles_list
    data = request.get_json()
    try:
        obstacles = data["obstacles"]
        # 동적 업데이트 시 기존 장애물 유지하고 추가
        for obstacle in obstacles:
            x_min = float(obstacle["x_min"])
            x_max = float(obstacle["x_max"])
            z_min = float(obstacle["z_min"])
            z_max = float(obstacle["z_max"])
            grid.set_obstacle(x_min, x_max, z_min, z_max)
            obstacles_list.append({
                "x_min": x_min,
                "x_max": x_max,
                "z_min": z_min,
                "z_max": z_max
            })
        print(f"Obstacles Updated: {obstacles_list}")
        return jsonify({"status": "OK"})
    except (KeyError, ValueError, TypeError) as e:
        print(f"Error in /update_obstacle: {e}")
        return jsonify({"status": "ERROR", "message": "Invalid obstacle data"}), 400

@app.route('/set_destination', methods=['POST'])
def set_destination():
    global destination, path
    data = request.get_json()
    try:
        x_dest, y_dest, z_dest = map(float, data["destination"].split(","))
        x_dest = max(0, min(x_dest, 300.0))
        z_dest = max(0, min(z_dest, 300.0))
        destination = (x_dest, z_dest)
        path = []
        if current_position:
            path = pathfinding.find_path(current_position, destination, grid)
            print(f"Start Position: {current_position}")
            print(f"Goal Position: {destination}")
            print(f"Waypoints: {path}")
        return jsonify({"status": "OK"})
    except (KeyError, ValueError):
        return jsonify({"status": "ERROR", "message": "Invalid destination"}), 400

@app.route('/get_move', methods=['GET'])
def get_move():
    return jsonify(nav_controller.get_move())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006)