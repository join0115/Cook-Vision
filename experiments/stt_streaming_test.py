"""
[개발 과정 프로토타입 — 최종 파이프라인에는 포함되지 않음]

Google Cloud Speech-to-Text 실시간 스트리밍 인식만 단독으로 확인해보는 테스트.
인식 결과를 콘솔에 출력만 하고 이후 로직(재료 매핑 등)과는 연결되어 있지 않다.

원본: 베트남 코드/pi/googole_stt.py (파일명에 "googole" 오타 — 원본 그대로 남겨둠)
  캡스톤 코드 파일/googole_stt.py에도 거의 동일한 사본이 있었는데, 그쪽은 sounddevice 대신
  pyaudio를 사용하는 차이만 있었다 (아마 오디오 백엔드를 sounddevice로 바꿔보던 중 버전).

정리하며 수정한 부분: GOOGLE_APPLICATION_CREDENTIALS 하드코딩 경로(실제 GCP 프로젝트 ID 노출)를
환경변수로 치환. 그 외 로직은 원본 그대로.
"""

import os
import queue
import sys
from threading import Thread

import google.cloud.speech as speech
import sounddevice as sd

if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_PATH"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.environ["GOOGLE_APPLICATION_CREDENTIALS_PATH"]

client = speech.SpeechClient()

device_id = int(os.environ.get("PI_AUDIO_DEVICE_INDEX", "2"))
channels = 2
sample_rate = 16000
chunk_size = 2048

audio_queue = queue.Queue(maxsize=10)


def record_audio():
    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        if not audio_queue.full():
            audio_queue.put(indata.copy())

    with sd.InputStream(samplerate=sample_rate, device=device_id, channels=channels, callback=callback, blocksize=chunk_size, dtype="int16"):
        while True:
            pass


def audio_generator():
    while True:
        data = audio_queue.get()
        if data is None:
            break
        yield data.tobytes()


def transcribe_streaming():
    audio_gen = audio_generator()
    requests = (speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in audio_gen)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=sample_rate,
        language_code="en-US",
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

    try:
        responses = client.streaming_recognize(config=streaming_config, requests=requests)
        for response in responses:
            for result in response.results:
                print("Transcript: {}".format(result.alternatives[0].transcript))
    except Exception as e:
        print(f"An error occurred in transcribe_streaming: {e}")


if __name__ == "__main__":
    audio_thread = Thread(target=record_audio)
    audio_thread.start()
    transcribe_streaming()
    audio_queue.put(None)
    audio_thread.join()
