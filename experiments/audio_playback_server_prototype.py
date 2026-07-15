"""
[개발 과정 프로토타입 — 최종 파이프라인에는 포함되지 않음]

젯슨에서 탐지된 재료 목록(콤마로 구분된 문자열)을 소켓으로 받아, 재료별 안내 음성을
순서대로 재생하는 서버 프로토타입.

원본: 베트남 코드/pi_step_4_1.py
  - 파일은 "베트남 코드" 트리 루트(파이 쪽 로직)에 있었지만, 실제로는 0.0.0.0으로 bind해서
    accept를 기다리는 **서버** 코드라 이름과 달리 "pi_"가 아니라 수신 대기 쪽 로직에 가깝다.
  - 변수명이 `step3_audio_files`인데 실제로는 "step4" 음성을 재생한다 — 이전 단계 코드를
    복사해서 만들다가 이름을 바꾸지 않은 흔적으로 보인다.
  - jetson/ingredient_locator_server.py(JetDo.py)가 이미 재료 탐지+방향 계산+소켓 응답을
    전부 처리하기 때문에, 이 프로토타입은 그 이전 단계에 시도했던 "재료 목록만 받아서
    음성 재생"하는 더 단순한 버전으로 보인다. 최종적으로는 쓰이지 않은 것으로 추정.

정리하며 수정한 부분: 없음 (원본 그대로 보존, 노출된 비밀정보 없음).
"""

import socket
import subprocess

step3_audio_files = {
    "1": "/home/pi/Desktop/voice/step_4/1.wav",
    "2": "/home/pi/Desktop/voice/step_4/2.wav",
    "3": "/home/pi/Desktop/voice/step_4/3.wav",
    "4": "/home/pi/Desktop/voice/step_4/4.wav",
    "5": "/home/pi/Desktop/voice/step_4/5.wav",
    "Bread": "/home/pi/Desktop/voice/ingredient/bread.wav",
    "Cheese": "/home/pi/Desktop/voice/ingredient/cheese.wav",
    "Ham": "/home/pi/Desktop/voice/ingredient/ham.wav",
    "Eggs": "/home/pi/Desktop/voice/ingredient/eggs.wav",
    "FriedEggs": "/home/pi/Desktop/voice/ingredient/friedeggs.wav",
    "Lettuce": "/home/pi/Desktop/voice/ingredient/lettuce.wav",
    "Tomato": "/home/pi/Desktop/voice/ingredient/tomato.wav",
    "clock": "/home/pi/Desktop/voice/clock/1~12.wav",
}

HOST = "0.0.0.0"
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server running on {HOST}:{PORT}")

    conn, addr = s.accept()

    with conn:
        print(f"Connected by {addr}")

        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            ingredients = data.split(",")
            print(f"Received ingredients: {ingredients}")

            for ingredient in ingredients:
                if ingredient == "no_ingredients":
                    print("No ingredients detected.")
                else:
                    file = step3_audio_files.get(ingredient)
                    if file:
                        command = ["aplay", "-D", "plughw:1,0", file]
                        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        if result.returncode != 0:
                            print(f"Error playing file {file}")
                            print(result.stderr.decode())

print("All audio files have been played.")
