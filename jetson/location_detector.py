"""
손 기준 재료 위치 뷰어 (젯슨나노)

카메라 스트림에서 손(Hand)과 재료를 탐지하고, 손을 기준으로 각 재료가
몇 시 방향에 있는지 계산해 콘솔에 출력한다. 화면에 바운딩 박스도 표시한다.

원본: 베트남 코드/jetson/location_detector.py
정리하며 수정한 부분:
  - 하드코딩된 스트림 URL/모델 경로를 config.py(환경변수)로 이동
  - 12시 방향 판정 버그 수정 (자세한 설명은 ingredient_locator_server.py 참고)

참고(docs/KNOWN_ISSUES.md에도 기록):
  "정리된 버전"으로 보였던 캡스톤 코드 파일/location_detector.py 쪽에는
  3시/9시 방향이 서로 뒤바뀐 별개의 버그가 있었다. 이 파일(베트남 코드 쪽)에는
  해당 버그가 없어서, 이쪽을 기준으로 정리했다.
"""

import math
import sys

import cv2
import numpy as np
import torch

from config import CAMERA_STREAM_URL, CLASS_NAMES, MODEL_WEIGHTS_PATH, YOLOV5_REPO_PATH

sys.path.insert(0, YOLOV5_REPO_PATH)
from models.experimental import attempt_load  # noqa: E402
from utils.datasets import letterbox  # noqa: E402
from utils.general import non_max_suppression, scale_coords  # noqa: E402

DISPLAY_CLASS_NAMES = [name.capitalize() for name in CLASS_NAMES]


def angle_to_clock_label(angle: float) -> str:
    if angle >= 345 or angle < 15:
        return "12시 방향"
    for hour in range(1, 12):
        lower = 15 + (hour - 1) * 30
        upper = lower + 30
        if lower <= angle < upper:
            return f"{hour}시 방향"
    return "12시 방향"


def main() -> None:
    cap = cv2.VideoCapture(CAMERA_STREAM_URL)
    if not cap.isOpened():
        print("Error: Unable to open video stream.")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = attempt_load(MODEL_WEIGHTS_PATH, map_location=device)
    model.to(device)
    model.eval()

    frame_skip = 2

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

        for det in pred:
            if len(det):
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], frame.shape).round()
                for *xyxy, conf, cls in reversed(det):
                    label = f"{DISPLAY_CLASS_NAMES[int(cls)]} {conf:.2f}"
                    cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (255, 0, 0), 2)
                    cv2.putText(frame, label, (int(xyxy[0]), int(xyxy[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                    center_x, center_y = (xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2
                    if DISPLAY_CLASS_NAMES[int(cls)] == "Hand":
                        hand_position = (center_x, center_y)
                    else:
                        other_objects.append((DISPLAY_CLASS_NAMES[int(cls)], center_x, center_y))

        if hand_position:
            hand_x, hand_y = hand_position
            for obj_name, obj_x, obj_y in other_objects:
                angle = math.degrees(math.atan2(obj_y - hand_y, obj_x - hand_x)) - 90
                if angle < 0:
                    angle += 360
                direction = angle_to_clock_label(angle)
                print(f"{obj_name}는 Hand의 {direction}에 있습니다.")

        cv2.imshow("Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
