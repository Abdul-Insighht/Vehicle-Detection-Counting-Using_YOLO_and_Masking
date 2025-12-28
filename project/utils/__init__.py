import cv2
import time
import numpy as np
import json
from collections import defaultdict, deque

class VehicleCounter:
    def __init__(self):
        self.class_count = defaultdict(int)
        self.crossed_ids = set()
        self.tracking_history = defaultdict(lambda: deque(maxlen=30))
        self.count_log = []
        self.processing_times = deque(maxlen=100)
        self.start_time = time.time()

       
        self.entry_line_y = 300
        self.exit_line_y = 400

    # ------------------------------
    # Class color mapping
    def get_class_color(self, class_id):
        colors = {
            0: (255, 0, 0),    # car
            1: (0, 255, 0),    # truck
            2: (0, 0, 255),    # motorcycle
            3: (255, 255, 0),  # bus
        }
        return colors.get(class_id, (255, 255, 255))

    def get_class_color_by_name(self, class_name):
        colors = {
            "car": (255, 0, 0),
            "truck": (0, 255, 0),
            "motorcycle": (0, 0, 255),
            "bus": (255, 255, 0),
        }
        return colors.get(class_name.lower(), (255, 255, 255))

    # ------------------------------
    # Draw trail for tracked objects
    def draw_tracking_trail(self, frame, track_id):
        history = self.tracking_history[track_id]
        for i in range(1, len(history)):
            color = (0, 255 - i * 10, 255 - i * 10)
            cv2.line(frame, history[i - 1], history[i], color, 2)

    # ------------------------------
    # Check line crossing (basic)
    def check_line_crossing(self, track_id, current_y):
        if track_id in self.crossed_ids:
            return False
        history = self.tracking_history[track_id]
        if len(history) < 2:
            return False
        prev_y = history[-2][1]
        return prev_y <= self.entry_line_y and current_y > self.entry_line_y

    # ------------------------------
    # Check line crossing with direction
    def check_line_crossing_direction(self, track_id, current_y):
        if track_id in self.crossed_ids:
            return None
        history = self.tracking_history[track_id]
        if len(history) < 2:
            return None
        prev_y = history[-2][1] if len(history) >= 2 else current_y

        if prev_y <= self.entry_line_y and current_y > self.entry_line_y:
            self.crossed_ids.add(track_id)
            return "entered"
        if prev_y >= self.exit_line_y and current_y < self.exit_line_y:
            self.crossed_ids.add(track_id)
            return "exited"
        return None

    # ------------------------------
    # FPS calculation
    def calculate_fps(self, start_time):
        frame_time = time.time() - start_time
        self.processing_times.append(frame_time)
        avg_time = np.mean(self.processing_times)
        return 1.0 / avg_time if avg_time > 0 else 0

    # ------------------------------
    # Log counting events
    def log_count_event(self, class_name, track_id):
        event = {
            'timestamp': time.time() - self.start_time,
            'class': class_name,
            'track_id': track_id,
            'total_count': sum(self.class_count.values())
        }
        self.count_log.append(event)

    # ------------------------------
    # Save results to JSON
    def save_results(self):
        results = {
            'total_count': sum(self.class_count.values()),
            'class_counts': dict(self.class_count),
            'count_log': self.count_log,
            'processing_time': time.time() - self.start_time
        }
        with open('object_detect_count.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("Results saved to object_detect_count.json")

    # ------------------------------
    # Draw statistics panel
    def draw_statistics_panel(self, frame):
        panel_height = 150
        cv2.rectangle(frame, (0, 0), (300, panel_height), (0, 0, 0), -1)
        y = 30
        total_count = sum(self.class_count.values())
        cv2.putText(frame, f"Total: {total_count}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y += 25
        for name, count in self.class_count.items():
            cv2.putText(frame, f"{name}: {count}", (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.get_class_color_by_name(name), 2)
            y += 25
        elapsed_time = time.time() - self.start_time
        cv2.putText(frame, f"Time: {elapsed_time:.1f}s", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)



