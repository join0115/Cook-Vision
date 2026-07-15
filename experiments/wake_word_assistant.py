"""
[개발 과정 프로토타입 — 최종 파이프라인에는 포함되지 않음]

웨이크워드(Porcupine) + STT + TTS + 소켓 서버를 한 파일에 통합하려던 시도.

원본: 베트남 코드/end/pi_1.py

왜 실험 폴더에 있는가 (docs/KNOWN_ISSUES.md 참고):
  이 파일은 라즈베리파이 쪽도 소켓 **서버**로 열어놓는다 (`start_server()`가 0.0.0.0:65432에서 accept).
  그런데 젯슨나노 쪽(jetson/ingredient_locator_server.py, 원본 JetDo.py)도 소켓 서버로 열려있어서
  둘 다 "누가 먼저 연결해 오길 기다리는" 역할이 되어버려 애초에 서로 연결될 수 없는 구조다.
  실제로 동작했던 조합은 jetson(서버) + pi/ingredient_locator_client.py(클라이언트) 쪽이고,
  이 파일은 그와는 다른 아키텍처를 시도하다 완성하지 못한 것으로 보인다.
  handle_command()도 "where is" 명령을 받으면 안내 문구만 말하고 실제 로직은 비어있는 스텁(TODO)이다.

정리하며 수정한 부분:
  - 실제로 노출되어 있던 Picovoice 액세스 키를 코드에서 완전히 제거하고 환경변수로 변경
    (원본 키는 노출된 채로 발견되어 재발급을 권장했음)
  - GOOGLE_APPLICATION_CREDENTIALS 하드코딩 경로를 환경변수로 변경
그 외 로직/구조는 원본을 그대로 보존했다 (미완성 상태 자체가 기록할 가치가 있는 정보라서).
"""

import os
import socket
from threading import Thread

import numpy as np
import pvporcupine
import pyaudio
from espeakng import ESpeakNG
from google.cloud import speech

if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_PATH"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.environ["GOOGLE_APPLICATION_CREDENTIALS_PATH"]

esng = ESpeakNG()
esng.pitch = 32
esng.speed = 150

client = speech.SpeechClient()

# Picovoice 콘솔(https://console.picovoice.ai/)에서 발급받은 키를 환경변수로 주입할 것.
# 원본 코드에는 실제 키가 하드코딩되어 있었음 — 반드시 새로 발급받아 사용해야 한다.
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

import queue  # noqa: E402

audio_queue = queue.Queue()


def speak(text):
    esng.say(text)


def record_audio():
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    try:
        while True:
            data = stream.read(CHUNK)
            audio_queue.put(data)
    except Exception as e:
        print(f"An error occurred in record_audio: {e}")


def audio_generator():
    while True:
        data = audio_queue.get()
        if data is None:
            break
        yield data


def transcribe_streaming():
    audio_gen = audio_generator()
    requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in audio_gen)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="ko-KR",
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

    try:
        responses = client.streaming_recognize(config=streaming_config, requests=requests)
        for response in responses:
            for result in response.results:
                if result.is_final:
                    transcript = result.alternatives[0].transcript
                    print(f"Transcript: {transcript}")
                    return transcript
    except Exception as e:
        print(f"An error occurred in transcribe_streaming: {e}")


def process_audio():
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    print("Listening for wake word...")
    try:
        while True:
            data = stream.read(CHUNK)
            pcm = np.frombuffer(data, dtype=np.int16)
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("Wake word detected!")
                speak("호출어가 감지되었습니다. 명령을 입력하세요.")
                transcript = transcribe_streaming()
                if transcript:
                    handle_command(transcript)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        porcupine.delete()


def handle_command(command):
    """TODO(원본 미완성): "where is" 명령을 인식은 하지만 실제 위치 안내 로직은 연결되지 않았다."""
    if "where is" in command:
        speak("위치 확인 기능을 수행합니다.")
    else:
        speak("다른 명령을 인식했습니다.")


def start_server():
    HOST = "0.0.0.0"
    PORT = int(os.environ.get("PI_SOCKET_PORT", "65432"))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"서버가 {HOST}:{PORT}에서 실행 중입니다.")

        conn, addr = s.accept()
        with conn:
            print(f"{addr}에서 연결되었습니다.")
            speak("시스템이 준비되었습니다.")

            Thread(target=record_audio, daemon=True).start()
            Thread(target=process_audio, daemon=True).start()

            while True:
                data = conn.recv(1024)
                if not data:
                    break
                command = data.decode()
                print(f"수신한 데이터: {command}")
                # TODO(원본 미완성): 여기서 받은 명령을 처리하는 로직이 채워지지 않았다.


if __name__ == "__main__":
    start_server()
