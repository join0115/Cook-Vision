"""젯슨나노 쪽 공통 설정값. 모두 환경변수로 주입한다 (원본 코드에는 하드코딩되어 있었음)."""

import os

# YOLOv5 저장소 경로 (pip 패키지가 아니라 git clone한 로컬 저장소를 사용)
YOLOV5_REPO_PATH = os.environ.get("YOLOV5_REPO_PATH", "/home/jetson/yolov5")

# 학습된 커스텀 가중치 경로 (클래스: hand, bread, cheese, eggs, friedeggs, ham, lettuce, tomato)
MODEL_WEIGHTS_PATH = os.environ.get(
    "MODEL_WEIGHTS_PATH", "/home/jetson/yolov5/runs/train/sandwich_please3/weights/best.pt"
)

# 라즈베리파이(카메라 부착)가 motionEye로 송출하는 MJPEG 스트림 주소 → 라즈베리파이의 IP를 가리켜야 함
CAMERA_STREAM_URL = os.environ.get("CAMERA_STREAM_URL", "http://127.0.0.1:8081")

# 라즈베리파이와 통신하는 소켓 서버 설정
SOCKET_HOST = os.environ.get("JETSON_SOCKET_HOST", "0.0.0.0")
SOCKET_PORT = int(os.environ.get("JETSON_SOCKET_PORT", "65432"))

CLASS_NAMES = ["hand", "bread", "cheese", "eggs", "friedeggs", "ham", "lettuce", "tomato"]
