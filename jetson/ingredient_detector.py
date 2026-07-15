"""
재료 탐지 뷰어 (젯슨나노)

카메라 스트림에서 YOLOv5로 탐지된 재료 목록을 1초마다 콘솔에 출력하고,
화면에 바운딩 박스를 그려서 보여준다. 'q'를 누르면 종료.

원본: 베트남 코드/jetson/ingredient_detector.py
    (거의 동일한 사본이 캡스톤 코드 파일/ingredient_detector.py에도 있었음 — 스트림 IP만 다름)
정리하며 수정한 부분:
  - 하드코딩된 스트림 URL/모델 경로를 config.py(환경변수)로 이동
  - 어디에서도 사용되지 않던 required_ingredients 리스트(죽은 코드) 제거
"""

import sys
import time

import cv2
import numpy as np
import torch

from config import CAMERA_STREAM_URL, MODEL_WEIGHTS_PATH, YOLOV5_REPO_PATH

sys.path.insert(0, YOLOV5_REPO_PATH)
from models.experimental import attempt_load  # noqa: E402
from utils.datasets import letterbox  # noqa: E402
from utils.general import non_max_suppression, scale_coords  # noqa: E402


def check_ingredients(detections, model) -> set:
    found_ingredients = set()
    for det in detections:
        if len(det):
            for *xyxy, conf, cls in det:
                ingredient_name = model.names[int(cls)]
                if ingredient_name != "hand":
                    found_ingredients.add(ingredient_name)
    return found_ingredients


def main() -> None:
    cap = cv2.VideoCapture(CAMERA_STREAM_URL)
    if not cap.isOpened():
        print("Error: Unable to open video stream.")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = attempt_load(MODEL_WEIGHTS_PATH, map_location=device)
    model.to(device)
    model.eval()

    last_print_time = time.time()
    frame_skip = 5

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

        found_ingredients = check_ingredients(pred, model)

        current_time = time.time()
        if current_time - last_print_time >= 1.0:
            if found_ingredients:
                print("있는 재료:", ", ".join(found_ingredients))
            else:
                print("재료가 하나도 없습니다.")
            last_print_time = current_time

        for det in pred:
            if len(det):
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], frame.shape).round()
                for *xyxy, conf, cls in reversed(det):
                    label = f"{model.names[int(cls)]} {conf:.2f}"
                    cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (255, 0, 0), 2)
                    cv2.putText(frame, label, (int(xyxy[0]), int(xyxy[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        cv2.imshow("Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
