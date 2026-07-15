"""
재료 위치 안내 서버 (젯슨나노)

라즈베리파이(pi/ingredient_locator_client.py)로부터 소켓으로 재료 이름을 받으면,
카메라 스트림 한 프레임에 대해 YOLOv5로 손(hand)과 재료를 탐지하고,
손을 기준으로 재료가 몇 시 방향에 있는지 계산해서 응답한다.

원본: 베트남 코드/JetDo.py
정리하며 수정한 부분:
  - 하드코딩된 스트림 URL/모델 경로/소켓 host를 config.py(환경변수)로 이동
  - 12시 방향 판정 버그 수정: `if 345 <= angle < 15`는 파이썬 체이닝 비교라서
    (345 <= angle) and (angle < 15)로 해석되어 항상 False였다.
    → `angle >= 345 or angle < 15`로 수정.
  - 클라이언트 1개만 처리하고 끝나던 구조는 원본 동작을 그대로 보존
    (재연결 루프 추가는 기능 확장이라 이번 정리 범위에서 제외, docs/KNOWN_ISSUES.md에 기록)
"""

import math
import socket
import sys

import cv2
import numpy as np
import torch

from config import CAMERA_STREAM_URL, CLASS_NAMES, MODEL_WEIGHTS_PATH, SOCKET_HOST, SOCKET_PORT, YOLOV5_REPO_PATH

sys.path.insert(0, YOLOV5_REPO_PATH)
from models.experimental import attempt_load  # noqa: E402
from utils.datasets import letterbox  # noqa: E402
from utils.general import non_max_suppression, scale_coords  # noqa: E402


def angle_to_clock_direction(angle: float) -> str:
    """손 중심 기준 각도(0~360, 0=12시 방향)를 1~12시 방향 문자열로 변환."""
    if angle >= 345 or angle < 15:
        return "12"
    for hour in range(1, 12):
        lower = 15 + (hour - 1) * 30
        upper = lower + 30
        if lower <= angle < upper:
            return str(hour)
    return "12"  # 부동소수점 경계값 등 예외적인 경우의 안전장치


def main() -> None:
    cap = cv2.VideoCapture(CAMERA_STREAM_URL)
    if not cap.isOpened():
        print("Error: Unable to open video stream.")
        sys.exit(1)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = attempt_load(MODEL_WEIGHTS_PATH, map_location=device)
    model.to(device)
    model.eval()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((SOCKET_HOST, SOCKET_PORT))
        server_socket.listen()
        print(f"서버가 {SOCKET_HOST}:{SOCKET_PORT}에서 실행 중입니다.")

        conn, addr = server_socket.accept()
        print(f"{addr}에서 연결되었습니다.")

        while True:
            ingredient_data = conn.recv(1024).decode().strip()
            if not ingredient_data:
                break
            ingredient_data = ingredient_data.lower()
            print(f"확인할 재료: {ingredient_data}")

            ret, frame = cap.read()
            if not ret:
                conn.sendall(b"Error: Failed to grab frame.")
                continue

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
                        label = CLASS_NAMES[int(cls)].lower()
                        center_x, center_y = (xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2
                        if label == "hand":
                            hand_position = (center_x, center_y)
                        elif label == ingredient_data:
                            other_objects.append((label, center_x, center_y))

            if hand_position and other_objects:
                conn.sendall("재료 있음".encode("utf-8"))
                obj_name, obj_x, obj_y = other_objects[0]
                hand_x, hand_y = hand_position

                angle = math.degrees(math.atan2(obj_y - hand_y, obj_x - hand_x)) - 90
                if angle < 0:
                    angle += 360

                direction = angle_to_clock_direction(angle)
                print(f"{obj_name}는 Hand의 {direction}시 방향에 있습니다.")
                conn.sendall(direction.encode("utf-8"))
            else:
                conn.sendall("재료 없음".encode("utf-8"))

    cap.release()


if __name__ == "__main__":
    main()
