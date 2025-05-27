import plotly.graph_objects as go
import math

WORLD_SIZE = 300  # 300x300 미터

class vi:
    def visualize_path(self):
        if not self.current_position:
            print("Visualization skipped: No current position available.")
            return

        # Plotly Figure 생성
        fig = go.Figure()

        # 장애물 시각화 (원래 좌표를 사용해 사각형으로 표시)
        for i, obstacle in enumerate(self.grid.original_obstacles):
            x_min = obstacle["x_min"]
            x_max = obstacle["x_max"]
            z_min = obstacle["z_min"]
            z_max = obstacle["z_max"]
            # 사각형의 4개 꼭짓점 정의 (시계 방향)
            x_coords = [x_min, x_max, x_max, x_min, x_min]
            z_coords = [z_min, z_min, z_max, z_max, z_min]
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=z_coords,
                mode='lines',
                fill='toself',
                fillcolor='black',
                line=dict(color='black'),
                opacity=0.6,
                name=f'Obstacle {i+1}'
            ))

        # A* 경로 시각화 (파란 선)
        if self.waypoints:
            path_x = [point[0] for point in self.waypoints]
            path_z = [point[1] for point in self.waypoints]
            fig.add_trace(go.Scatter(x=path_x, y=path_z, mode='lines', line=dict(color='blue'), name='A* Path'))

        # 실제 이동 경로 시각화 (초록 선)
        if self.actual_path:
            actual_x = [point[0] for point in self.actual_path]
            actual_z = [point[1] for point in self.actual_path]
            fig.add_trace(go.Scatter(x=actual_x, y=actual_z, mode='lines', line=dict(color='green'), name='Actual Path'))

        # 전차 위치 (빨간 화살표)
        curr_x, curr_z = self.current_position
        fig.add_trace(go.Scatter(
            x=[curr_x],
            y=[curr_z],
            mode='markers+text',
            marker=dict(color='red', size=10, symbol='arrow', angle=math.degrees(self.current_heading)),
            text=['Tank'],
            textposition="top right",
            name='Tank'
        ))

        # 최종 목적지 (빨간 별)
        if self.waypoints:
            final_goal = self.waypoints[-1]
            fig.add_trace(go.Scatter(x=[final_goal[0]], y=[final_goal[1]], mode='markers', marker=dict(color='red', size=10, symbol='star'), name='Final Goal'))

        # 레이아웃 설정
        fig.update_layout(
            title='Path Visualization',
            xaxis_title='X',
            yaxis_title='Z',
            xaxis=dict(range=[0, WORLD_SIZE]),
            yaxis=dict(range=[0, WORLD_SIZE]),
            showlegend=True,
            width=800,
            height=800
        )

        # HTML 파일로 저장 (Plotly JS를 포함)
        fig.write_html("path_visualization.html", include_plotlyjs='cdn', full_html=True)
        # print("Visualization saved as path_visualization.html")