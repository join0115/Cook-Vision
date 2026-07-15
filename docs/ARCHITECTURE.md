# 시스템 구성

## 하드웨어

안경(웨어러블) 쪽에는 카메라와 라즈베리파이가 함께 붙어있고, 연산이 무거운 YOLO 추론만
별도의 젯슨나노가 담당하는 역할 분담 구조였습니다.

- **Raspberry Pi** (+ 카메라, + ReSpeaker 2 Mics Pi HAT) — 3가지 역할을 겸했습니다.
  1. 카메라로 영상을 캡처
  2. motionEye로 그 영상을 MJPEG 스트림으로 송출 (`http://<Pi IP>:8081`)
  3. 마이크 입력, 음성 인식/출력, 스피커 재생 (`pi/ingredient_locator_client.py`)
- **Jetson Nano** — 라즈베리파이가 송출한 스트림을 `cv2.VideoCapture()`로 받아와 YOLOv5로
  재료/손 탐지만 전담합니다. 카메라나 motionEye를 직접 실행하지는 않습니다.

즉 카메라를 "들고 있는" 쪽과 "영상을 분석하는" 쪽이 물리적으로 분리되어 있어, 안경(라즈베리파이
+ 카메라)은 가볍게 사용자가 착용하고, 연산이 무거운 젯슨나노는 별도로(가방 등에) 둘 수 있는
구조였던 것으로 보입니다.

## 의도된 전체 흐름

```
[Raspberry Pi + 카메라] --motionEye로 캡처/송출--> MJPEG 스트림 (http://<Pi IP>:8081)
                                                        │
                                                        ▼
                                              [Jetson Nano]
                                    │  스트림을 가져와 YOLOv5로 hand + 재료
                                    │  (bread/cheese/eggs/friedeggs/ham/lettuce/tomato) 탐지
                                    │  소켓 서버로 대기 (0.0.0.0:65432)
                                    │
                                    ▼
[Raspberry Pi] --마이크 입력--> Google STT --재료명--> 소켓으로 Jetson에 전송
      │                                                        │
      │                              <--"있음/없음" + n시 방향-- │
      ▼
  안내 음성(mp3/wav) 재생 (재료명 → 방향 순서)
```

같은 라즈베리파이가 위쪽(카메라 송출)과 아래쪽(음성 인식/출력) 역할을 동시에 맡는 구조라,
`jetson/config.py`의 `CAMERA_STREAM_URL`은 실제로는 라즈베리파이의 IP를 가리켜야 합니다.

## 검증된(실제 동작이 확인되는) 흐름

- `jetson/ingredient_locator_server.py` (원본 JetDo.py) — 소켓 **서버**입니다. 재료명을
  받아 YOLOv5 탐지 후 "재료 있음/없음" + 시 방향을 응답합니다.
- `pi/ingredient_locator_client.py` (원본 PiDo.py) — 소켓 **클라이언트**입니다. Google
  STT로 재료명을 인식해 서버에 전송하고, 응답을 받아 안내 음성을 재생합니다.

두 파일은 host/port, 요청·응답 프로토콜이 정확히 맞물리는 유일한 조합이라, 실제로
전원을 켜면 자동 실행되던 조합이었을 가능성이 가장 높습니다. (단, 사용자 본인 확인으로도
"기능을 완성시키지는 못했다"고 하여, 끝까지 안정적으로 통합·디버깅되었는지는 불확실합니다.)

## 미완성으로 남은 흐름

`experiments/wake_word_assistant.py` (원본 end/pi_1.py)는 "웨이크워드 → STT 명령 인식
→ TTS 응답"까지 파이 쪽에서 전부 처리하려던 더 발전된 버전으로 보입니다. 하지만 이 파일은
파이 쪽도 소켓 **서버**로 열어놓기 때문에, 역시 서버인 `ingredient_locator_server.py`와는
애초에 연결될 수 없는 구조입니다. 즉 두 컴포넌트 모두 "연결을 기다리기만" 하고 있어 실제로는
서로 대화가 불가능했습니다. `handle_command()` 함수도 "where is" 명령을 인식만 하고 실제
동작은 비어 있는 TODO 상태였습니다.

정리하면, 이 프로젝트는 (1) YOLOv5 기반 손-재료 상대 위치 탐지, (2) Google STT 기반 음성
명령 인식, (3) Porcupine 웨이크워드 감지, (4) TCP 소켓 기반 Jetson↔Pi 통신, (5) 음성
안내 재생까지 각 요소 기술은 개별적으로 구현했지만, 이 모든 것을 하나의 안정적인
자동 실행 파이프라인으로 완전히 통합하는 마지막 단계는 마치지 못한 상태로 남아 있습니다.
자세한 근거는 [KNOWN_ISSUES.md](./KNOWN_ISSUES.md)를 참고해 주세요.
