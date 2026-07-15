"""
재료 위치 안내 클라이언트 (라즈베리파이)

마이크로 재료 이름을 듣고(Google STT) 젯슨나노(jetson/ingredient_locator_server.py)에
소켓으로 전송, 응답(있음/없음 + 시 방향)을 받아 안내 음성을 재생한다.

원본: 베트남 코드/PiDo.py
정리하며 수정한 부분:
  - GCP 인증 파일 경로, 젯슨 IP/포트, 오디오 장치 index를 config.py(환경변수)로 이동
    → 원본에는 실제 GCP 프로젝트 ID가 파일명에 노출된 절대경로가 하드코딩되어 있었음 (스크러빙 완료)
  - busy-wait(`while True: pass`)로 스레드를 살려두던 record_audio()를 유지하되 주석으로 한계 명시

docs/KNOWN_ISSUES.md에 기록된 미해결 사항:
  - 음성 안내 파일 경로가 실제 assets/voice 폴더 구조와 일부 어긋난다.
    (예: 코드는 "voice/ingredients/Bread.wav"를 찾지만 실제 파일은 "voice/ingredient/bread.wav")
    이 프로젝트가 끝까지 통합 테스트되지 못했다는 증거 중 하나라서, 임의로 고치지 않고
    원본 그대로 남겨두었다. 실제 재현 시에는 아래 VOICE_* 경로를 실제 파일명에 맞게 조정해야 한다.
"""

import os
import queue
from threading import Thread

import google.cloud.speech as speech
import sounddevice as sd

from config import (
    ALSA_PLAYBACK_DEVICE,
    AUDIO_DEVICE_INDEX,
    GOOGLE_APPLICATION_CREDENTIALS,
    JETSON_HOST,
    JETSON_PORT,
    VOICE_ASSET_DIR,
)
import socket
import subprocess

if GOOGLE_APPLICATION_CREDENTIALS:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

client = speech.SpeechClient()
sample_rate = 16000
channels = 2
chunk_size = 2048
audio_queue = queue.Queue(maxsize=10)


def voice_path(*parts: str) -> str:
    return os.path.join(VOICE_ASSET_DIR, *parts)


def play_audio(file_path: str) -> None:
    command = ["aplay", "-D", ALSA_PLAYBACK_DEVICE, file_path]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def record_audio() -> None:
    def callback(indata, frames, time, status):
        if status:
            print(status)
        if not audio_queue.full():
            audio_queue.put(indata.copy())

    with sd.InputStream(
        samplerate=sample_rate, device=AUDIO_DEVICE_INDEX, channels=channels,
        callback=callback, blocksize=chunk_size, dtype="int16",
    ):
        while True:
            pass  # 원본 그대로: 별도 스레드를 계속 살려두기 위한 busy-wait (CPU 낭비, 알려진 이슈)


def transcribe_streaming():
    audio_gen = (audio_queue.get().tobytes() for _ in iter(int, 1))
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code="en-US",
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=False)

    responses = client.streaming_recognize(
        config=streaming_config,
        requests=(speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in audio_gen),
    )
    for response in responses:
        for result in response.results:
            if result.is_final:
                return result.alternatives[0].transcript
    return None


ingredient_mapping = {
    "bread": "Bread",
    "cheese": "Cheese",
    "ham": "Ham",
    "egg": "Egg",
    "fried egg": "FriedEgg",
    "lettuce": "Lettuce",
    "tomato": "Tomato",
}


def main() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print("Jetson Nano 연결 시도 중...")
        s.connect((JETSON_HOST, JETSON_PORT))
        print("Jetson Nano 연결 성공!")

        while True:
            play_audio(voice_path("step_4", "1.wav"))

            ingredient_command = transcribe_streaming()
            if ingredient_command:
                ingredient_command = ingredient_command.lower()
                ingredient = ingredient_mapping.get(ingredient_command, None)

                if ingredient is None:
                    play_audio(voice_path("step_4", "invalid_ingredient.wav"))
                    continue

                print(f"선택된 재료: {ingredient}")
                s.sendall(ingredient.encode())

                try:
                    response = s.recv(1024).decode().strip()
                    print(f"서버 응답: {response}")

                    if response == "재료 있음":
                        play_audio(voice_path("step_4", "2.wav"))
                        direction = s.recv(1024).decode().strip()
                        print(f"{ingredient} 방향: {direction}")

                        play_audio(voice_path("ingredients", f"{ingredient}.wav"))
                        play_audio(voice_path("step_4", "3.wav"))
                        play_audio(voice_path("clock", f"{direction}.wav"))
                    else:
                        play_audio(voice_path("step_4", "4.wav"))
                        break
                except socket.error:
                    print("서버와의 연결이 끊어졌습니다.")
                    break
            else:
                print("음성 인식 실패: 재료가 인식되지 않았습니다.")
                play_audio(voice_path("step_4", "invalid_ingredient.wav"))

        play_audio(voice_path("step_4", "5.wav"))
        print("end")


if __name__ == "__main__":
    audio_thread = Thread(target=record_audio, daemon=True)
    audio_thread.start()
    main()
