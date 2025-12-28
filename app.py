import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
from project.constant import *   

class VehicleCounter:
    def __init__(self):
        self.cap = cv2.VideoCapture(data_path)
        self.model = YOLO(model_path)

        self.mask = cv2.imread(mask_path)
        self.mask = cv2.resize(self.mask, (1080, 720))

        self.frame_count = 0
        self.skip = 6
        self.allowed_classes = allowed_classes
        self.line_y_red = line_y_red

        self.class_count = defaultdict(int)
        self.crossed_ids = set()


    def process(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (1080, 720))
            masked = cv2.bitwise_and(self.mask, frame)

            if self.frame_count % self.skip == 0:
                result = self.model.track(masked, persist=True)

                if result[0].boxes.data is not None:
                    self.draw_results(frame, result)

            cv2.imshow("YOLO Object Counter", frame)
            self.frame_count += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()


    def draw_results(self, frame, result):
        boxes = result[0].boxes.xyxy.cpu()
        confidence = result[0].boxes.conf.cpu()
        track_ids = result[0].boxes.id.int().cpu().tolist()
        classes = result[0].boxes.cls.int().cpu().tolist()

        cv2.line(frame, (580, self.line_y_red), (990, self.line_y_red), (0, 0, 255), 2)

        for box, conf, id, cls in zip(boxes, confidence, track_ids, classes):
            if cls not in self.allowed_classes:
                continue

            x1, y1, x2, y2 = map(int, box)
            label = self.model.names[cls]  

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 0), 2)
            cv2.putText(frame, f"ID:{id} {label}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 0, 255), 2)

            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            cv2.circle(frame, (cx, cy), 3, (255, 255, 0), -1)

            if cy > self.line_y_red and id not in self.crossed_ids:
                self.crossed_ids.add(id)
                self.class_count[label] += 1

        y = 30
        for name, count in self.class_count.items():
            cv2.putText(frame, f"{name}: {count}", (50, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            y += 30


if __name__ == "__main__":
    counter = VehicleCounter()
    counter.process()
