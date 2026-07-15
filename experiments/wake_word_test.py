"""
[개발 과정 프로토타입 — 최종 파이프라인에는 포함되지 않음]

Picovoice Porcupine 웨이크워드("raspberry") 감지 단독 테스트.

원본: 베트남 코드/pi/porcupine.py (캡스톤 코드 파일/porcupine.py와 완전히 동일한 사본이었음)

🚨 보안: 이 파일에는 실제로 사용 가능한 Picovoice 액세스 키가 평문으로 하드코딩되어 있었다.
  포트폴리오 공개 전 Picovoice 콘솔(https://console.picovoice.ai/)에서 반드시 키를 재발급받아야 한다.
  아래 코드에서는 환경변수로 치환해 원본 키를 완전히 제거했다.

정리하며 수정한 부분:
  - access_key를 환경변수(PICOVOICE_ACCESS_KEY)로 치환
  - keyword_path를 환경변수로 치환
그 외: 감지 도중 마이크 입력을 전부 output.wav에 무제한으로 이어 쓰는 부분은 원본 그대로 남겨뒀다.
  실제 웨이크워드 감지에는 필요 없는 디버그용 녹음 코드였던 것으로 보인다 (디스크가 계속 차오르는 문제 있음).
"""

import os

import numpy as np
import pvporcupine
import pyaudio
import wave

access_key = os.environ["PICOVOICE_ACCESS_KEY"]
keyword_path = os.environ.get(
    "PORCUPINE_KEYWORD_PATH", "/home/pi/Desktop/project/picovoice/raspberry_en_raspberry-pi_v3_0_0.ppn"
)

porcupine = pvporcupine.create(access_key=access_key, keyword_paths=[keyword_path])

CHUNK = porcupine.frame_length
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
DEVICE_INDEX = int(os.environ.get("PI_AUDIO_DEVICE_INDEX", "3"))
p = pyaudio.PyAudio()

wf = wave.open("output.wav", "wb")
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)

try:
    stream = p.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
        input_device_index=DEVICE_INDEX, frames_per_buffer=CHUNK,
    )

    print("Listening for wake word...")

    def process_audio():
        try:
            while True:
                data = stream.read(CHUNK)
                wf.writeframes(data)  # 디버그용: 마이크 입력을 전부 기록 (용량 무제한 증가 — 알려진 이슈)
                pcm = np.frombuffer(data, dtype=np.int16)
                keyword_index = porcupine.process(pcm)

                if keyword_index >= 0:
                    print("Wake word detected!")

        except KeyboardInterrupt:
            print("Stopping...")

        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            porcupine.delete()
            wf.close()

    process_audio()

except IOError as e:
    print(f"Error opening stream: {e}")
