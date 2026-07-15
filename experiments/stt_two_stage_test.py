"""
[개발 과정 프로토타입 — 최종 파이프라인에는 포함되지 않음]

"웨이크 명령 → 실제 명령"의 2단계 음성 인식을 시도해보던 테스트.

원본: 베트남 코드/pi/STTest.py ("STT test")

알려진 버그 (docs/KNOWN_ISSUES.md 참고, 일부러 고치지 않고 원본 그대로 보존):
  콘솔 안내 문구는 "next"라고 말하라고 하지만, transcribe_streaming() 내부 판정 로직은
  "where is"라는 문자열이 포함되어 있는지만 검사한다. 즉 1단계(웨이크 명령)와 2단계(실제 명령)가
  똑같은 "where is" 판정 함수를 재사용하고 있어서, 안내 문구와 실제 동작이 서로 다르다.
  이런 불일치가 남아있다는 것 자체가 이 프로젝트의 음성 파이프라인이 끝까지 다듬어지지
  못했다는 증거라 그대로 두었다.
  또한 result.is_final을 확인하지 않고 첫 인식 결과에서 바로 return하기 때문에,
  중간(비확정) 인식 결과에도 반응할 수 있다.

정리하며 수정한 부분: GOOGLE_APPLICATION_CREDENTIALS 하드코딩 경로를 환경변수로 치환.
"""

import os
import queue
import sys
import time
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


def record_audio(duration):
    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        if not audio_queue.full():
            audio_queue.put(indata.copy())

    with sd.InputStream(samplerate=sample_rate, device=device_id, channels=channels, callback=callback, blocksize=chunk_size, dtype="int16"):
        print("명령해주세요")
        time.sleep(duration)


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
                if "where is" in result.alternatives[0].transcript.lower():
                    print("정확하게 'where is' 인식. 작업 실행.")
                    return True
                else:
                    print("명령을 인식하지 못했습니다.")
                    return False
    except Exception as e:
        print(f"An error occurred in transcribe_streaming: {e}")
        return False


if __name__ == "__main__":
    while True:
        print("Please say 'next' to start listening for commands.")
        audio_thread = Thread(target=record_audio, args=(5,))
        audio_thread.start()
        audio_thread.join()

        if transcribe_streaming():
            print("Please provide a command.")
            audio_thread = Thread(target=record_audio, args=(5,))
            audio_thread.start()
            audio_thread.join()

            if transcribe_streaming():
                print("명령어가 성공적으로 실행되었습니다.")
            else:
                print("명령어 인식 실패. 다시 시도해 주세요.")
        else:
            print("다시 시도해 주세요.")
