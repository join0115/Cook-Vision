"""
[개발 과정 프로토타입 — 최종 파이프라인에는 포함되지 않음]

ALSA(aplay)로 WAV 파일을 순서대로 재생하는 최소 예제.

원본: 베트남 코드/aplay.py
  고정된 3개 파일만 재생하며, 실제 탐지된 방향(1~12시)과 연동되어 있지 않다 —
  오디오 재생 자체가 되는지만 확인해보던 초기 스모크 테스트로 보인다.

정리하며 수정한 부분: 없음 (원본 그대로 보존, 노출된 비밀정보 없음).
"""

import subprocess

files = [
    "/home/pi/Desktop/voice/clock/1.wav",
    "/home/pi/Desktop/voice/clock/2.wav",
    "/home/pi/Desktop/voice/clock/3.wav",
]

for file in files:
    command = ["aplay", "-D", "plughw:1,0", file]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"파일 {file} 재생 중 오류가 발생했습니다.")
        print(result.stderr.decode())

print("모든 음성 파일이 재생되었습니다.")
