import json
import math

def load_walls(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data['obstacles']

def get_bounding_box(wall):
    x, z = wall['position']['x'], wall['position']['z']
    rot_y = wall['rotation']['y']
    if abs(rot_y) < 0.1:  # 가로
        return (x - 5, x + 5, z - 1, z + 1)
    else:  # 세로
        return (x - 1, x + 1, z - 5, z + 5)

def check_overlap(box1, box2):
    x1_min, x1_max, z1_min, z1_max = box1
    x2_min, x2_max, z2_min, z2_max = box2
    return x1_min < x2_max and x1_max > x2_min and z1_min < z2_max and z1_max > z2_min

def adjust_walls(walls):
    for i in range(len(walls)):
        for j in range(i + 1, len(walls)):
            box1 = get_bounding_box(walls[i])
            box2 = get_bounding_box(walls[j])
            if check_overlap(box1, box2):
                # 겹침 해결: 한 벽을 이동
                walls[j]['position']['x'] += 10  # 예시 이동
            # 맞닿음 정렬: z 좌표 정렬 (가로 벽 기준)
            if walls[i]['rotation']['y'] == walls[j]['rotation']['y'] == 0:
                if abs(walls[i]['position']['z'] - walls[j]['position']['z']) < 1:
                    walls[j]['position']['z'] = walls[i]['position']['z']
                    # 끝점 연결
                    if abs(walls[i]['position']['x'] + 5 - walls[j]['position']['x'] + 5) < 2:
                        walls[j]['position']['x'] = walls[i]['position']['x'] + 10

def save_walls(walls, output_path):
    data = {"terrainIndex": 3, "obstacles": walls}
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)

# 실행
walls = load_walls("./map.json")
adjust_walls(walls)
save_walls(walls, 'output.json')