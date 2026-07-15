"""
[개발 과정 프로토타입 — 최종 파이프라인에는 포함되지 않음]

젯슨나노에 소켓으로 연결이 되는지 확인하기 위한 최소 클라이언트 테스트.

원본: 베트남 코드/pi/pi_socket.py
정리하며 수정한 부분:
  - 하드코딩된 젯슨 IP를 환경변수로 변경
  - 원본 파일 하단에 통째로 주석 처리되어 있던 실험용 대체 구현(WAV 파일 재생 버전)은
    죽은 코드라 삭제했다 (필요하면 pi/ingredient_locator_client.py의 play_audio()를 참고할 것).
"""

import os
import socket

HOST = os.environ.get("JETSON_HOST", "192.168.0.100")  # 젯슨 나노의 IP 주소
PORT = int(os.environ.get("JETSON_PORT", "65432"))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    message = "안녕하세요, 젯슨 나노!"
    s.sendall(message.encode())
    data = s.recv(1024)

print(f"서버로부터 응답: {data.decode()}")
