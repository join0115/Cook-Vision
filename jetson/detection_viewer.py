"""
기본 YOLO 탐지 뷰어 (젯슨나노)

카메라 스트림을 받아 YOLOv5로 탐지만 하고 화면에 바운딩 박스를 그려 보여주는
가장 단순한 디버그용 스크립트. 손/재료 위치 계산이나 소켓 통신은 하지 않는다.

원본: 베트남 코드/jetson/motioneye.py
    파일 이름 때문에 오해하기 쉬운데, motionEye(카메라 스트리밍 서버 소프트웨어)를
    직접 실행/설정하는 코드가 아니다. motionEye는 카메라가 달린 라즈베리파이 쪽에서
    별도로 떠 있는 스트리밍 서버이고, 이 스크립트(젯슨나노)는 그 스트림 주소를
    OpenCV로 구독만 한다. 그래서 정리하며 실제 역할에 맞게 detection_viewer.py로 이름을 바꿨다.
정리하며 수정한 부분:
  - 하드코딩된 스트림 URL/모델 경로를 config.py(환경변수)로 이동
"""

import sys

import cv2
import numpy as np
import torch

from config import CAMERA_STREAM_URL, MODEL_WEIGHTS_PATH, YOLOV5_REPO_PATH

sys.path.insert(0, YOLOV5_REPO_PATH)
from models.experimental import attempt_load  # noqa: E402
from utils.datasets import letterbox  # noqa: E402
from utils.general import non_max_suppression, scale_coords  # noqa: E402


def main() -> None:
    cap = cv2.VideoCapture(CAMERA_STREAM_URL)
    if not cap.isOpened():
        print("Error: Unable to open video stream.")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = attempt_load(MODEL_WEIGHTS_PATH, map_location=device)
    model.to(device)
    model.eval()

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
