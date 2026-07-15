"""
[개발 과정 프로토타입 — 최종 파이프라인에는 포함되지 않음]

jetson/location_detector.py의 초기 디버그 버전. 영어로 방향을 콘솔에 출력한다.

원본: 베트남 코드/jet_step_4_1.py (파일명의 "step 4.1"은 git 브랜치 대신 파일 접미사로
버전을 관리하던 흔적으로 보인다)

주의: 이 파일에는 jetson/location_detector.py와 동일한 12시 방향 버그가 원본 그대로 남아있다.
  `if 345 <= angle < 15:` 는 파이썬에서 (345 <= angle) and (angle < 15)로 해석되어 항상 False이므로
  12시 방향일 때 `direction` 변수가 할당되지 않고 이후 참조 시 NameError가 난다.
  실험 스크립트 원본 보존 차원에서 일부러 고치지 않았다 (정식 수정본은 jetson/location_detector.py 참고).

정리하며 수정한 부분: 하드코딩된 스트림 URL/모델 경로를 환경변수로 변경 (그 외 로직은 원본 그대로).
"""

import math
import os
import sys

import cv2
import numpy as np
import torch

YOLOV5_REPO_PATH = os.environ.get("YOLOV5_REPO_PATH", "/home/jetson/yolov5")
MODEL_WEIGHTS_PATH = os.environ.get(
    "MODEL_WEIGHTS_PATH", "/home/jetson/yolov5/runs/train/sandwich_please3/weights/best.pt"
)
CAMERA_STREAM_URL = os.environ.get("CAMERA_STREAM_URL", "http://127.0.0.1:8081")

sys.path.insert(0, YOLOV5_REPO_PATH)
from models.experimental import attempt_load  # noqa: E402
from utils.datasets import letterbox  # noqa: E402
from utils.general import non_max_suppression, scale_coords  # noqa: E402

cap = cv2.VideoCapture(CAMERA_STREAM_URL)
if not cap.isOpened():
    print("Error: Unable to open video stream.")
    sys.exit(1)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = attempt_load(MODEL_WEIGHTS_PATH, map_location=device)
model.to(device)
model.eval()

frame_skip = 2
class_names = ["Hand", "Bread", "Cheese", "Eggs", "FriedEggs", "Ham", "Lettuce", "Tomato"]

while True:
    for _ in range(frame_skip):
        ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame.")
        break

    img = letterbox(frame, new_shape=320)[0]
    img = img[:, :, ::-1].transpose(2, 0, 1)
    img = np.ascontiguousarray(img)

    img = torch.from_numpy(img).to(device)
    img = img.float()
    img /= 255.0
    if img.ndimension() == 3:
        img = img.unsqueeze(0)

    with torch.no_grad():
        pred = model(img, augment=False)[0]
    pred = non_max_suppression(pred, 0.5, 0.45, classes=None, agnostic=False)

    hand_position = None
    other_objects = []

    for i, det in enumerate(pred):
        if len(det):
            det[:, :4] = scale_coords(img.shape[2:], det[:, :4], frame.shape).round()
            for *xyxy, conf, cls in reversed(det):
                label = f"{class_names[int(cls)]} {conf:.2f}"
                cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (255, 0, 0), 2)
                cv2.putText(frame, label, (int(xyxy[0]), int(xyxy[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                center_x, center_y = (xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2
                if class_names[int(cls)] == "Hand":
                    hand_position = (center_x, center_y)
                else:
                    other_objects.append((class_names[int(cls)], center_x, center_y))

    if hand_position:
        hand_x, hand_y = hand_position
        for obj_name, obj_x, obj_y in other_objects:
            angle = math.degrees(math.atan2(obj_y - hand_y, obj_x - hand_x)) - 90
            if angle < 0:
                angle += 360

            if 345 <= angle < 15:  # 알려진 버그: 항상 False (위 docstring 참고)
                direction = "12 o'clock"
            elif 15 <= angle < 45:
                direction = "1 o'clock"
            elif 45 <= angle < 75:
                direction = "2 o'clock"
            elif 75 <= angle < 105:
                direction = "3 o'clock"
            elif 105 <= angle < 135:
                direction = "4 o'clock"
            elif 135 <= angle < 165:
                direction = "5 o'clock"
            elif 165 <= angle < 195:
                direction = "6 o'clock"
            elif 195 <= angle < 225:
                direction = "7 o'clock"
            elif 225 <= angle < 255:
                direction = "8 o'clock"
            elif 255 <= angle < 285:
                direction = "9 o'clock"
            elif 285 <= angle < 315:
                direction = "10 o'clock"
            elif 315 <= angle < 345:
                direction = "11 o'clock"

            print(f"{obj_name} is at {direction} relative to the Hand.")

    cv2.imshow("Stream", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
