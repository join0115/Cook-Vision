"""
[개발 과정 프로토타입 — 최종 파이프라인에는 포함되지 않음]

젯슨-파이 간 소켓 연결이 되는지 확인하기 위한 최소 에코 서버.

원본: 베트남 코드/jetson/socket.py
  파일명을 `socket.py`로 두면 파이썬 표준 라이브러리 `socket` 모듈을 가려버린다.
  이 폴더가 sys.path/PYTHONPATH에 잡혀있는 상태로 다른 스크립트에서 `import socket`을
  하면 이 파일이 대신 로드되어 원인 파악이 어려운 버그로 이어질 수 있어 파일명을 바꿨다.

정리하며 수정한 부분: 파일명 변경 + host/port 환경변수화. 로직은 원본 그대로.
"""

import os
import socket

HOST = os.environ.get("SOCKET_TEST_HOST", "0.0.0.0")
PORT = int(os.environ.get("SOCKET_TEST_PORT", "65432"))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"서버가 {HOST}:{PORT}에서 실행 중입니다.")

    conn, addr = s.accept()

    with conn:
        print(f"{addr}에서 연결되었습니다.")

        while True:
            data = conn.recv(1024)
            if not data:
                break

            print(f"수신한 데이터: {data.decode()}")
            conn.sendall(data)
