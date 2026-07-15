"""라즈베리파이 쪽 공통 설정값. 모두 환경변수로 주입한다 (원본 코드에는 하드코딩되어 있었음)."""

import os

# Google Cloud 서비스 계정 키 파일 경로.
# 원본 코드에는 실제 GCP 프로젝트 ID가 파일명에 그대로 노출된 절대경로가 박혀 있었다
# (예: /home/pi/Desktop/raspi/key-rider-443318-xxxx.json). 반드시 본인 계정의 키 파일로 교체할 것.
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

JETSON_HOST = os.environ.get("JETSON_HOST", "192.168.0.100")
JETSON_PORT = int(os.environ.get("JETSON_PORT", "65432"))

AUDIO_DEVICE_INDEX = int(os.environ.get("PI_AUDIO_DEVICE_INDEX", "2"))  # ReSpeaker 등 마이크 장치 index
ALSA_PLAYBACK_DEVICE = os.environ.get("PI_ALSA_DEVICE", "plughw:1,0")

VOICE_ASSET_DIR = os.environ.get("VOICE_ASSET_DIR", "../assets/voice")
