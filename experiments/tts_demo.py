"""
[개발 과정 프로토타입 — 최종 파이프라인에는 포함되지 않음]

espeak-ng TTS 라이브러리 동작 확인용 데모.

원본: 베트남 코드/pi/espeak_ng.py
정리하며 수정한 부분: 사용하지 않는 import(sleep) 제거, 주석 처리된 죽은 코드(독일어 예시) 삭제.
"""

from espeakng import ESpeakNG

esng = ESpeakNG()
esng.pitch = 32
esng.speed = 150
esng.say("Hello World!")
