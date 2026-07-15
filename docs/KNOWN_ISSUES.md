# 정리 과정에서 발견한 이슈

원본 코드(하드웨어 오류로 실행 환경은 소실, 소스 사본만 남아있던 상태)를 분석하며 발견한
버그/보안 이슈/구조적 문제를 정리한 기록입니다. 포트폴리오 코드 자체에서 고친 것과, 일부러
원본 그대로 남겨둔 것을 구분해서 적었습니다.

## 1. 수정한 버그

### 12시 방향 판정 버그 (체이닝 비교)
`jetson/ingredient_locator_server.py`, `jetson/location_detector.py` 등 여러 파일에
아래와 같은 코드가 있었습니다.

```python
if 345 <= angle < 15:
    direction = "12"
```

파이썬에서 `345 <= angle < 15`는 `(345 <= angle) and (angle < 15)`로 해석됩니다.
`angle`은 0~360 범위의 값이라 이 두 조건을 동시에 만족하는 값은 존재하지 않습니다.
즉 12시 방향 분기가 **항상 실행되지 않는** 죽은 코드였고, 각도가 345~360 또는 0~15
범위일 때는 `direction` 변수가 아예 할당되지 않아 이후 코드에서 `NameError`가 나거나
(`ingredient_locator_server.py`) `direction`이 없는 채로 넘어가는 상황이 발생했습니다.

→ `angle >= 345 or angle < 15`로 수정했습니다 (jetson/ 폴더의 정식 버전에만 적용).
`experiments/location_detector_debug_viewer.py`(원본 jet_step_4_1.py)는 프로토타입
원본 보존 차원에서 버그를 그대로 남겨두고 주석으로만 설명했습니다.

### "정리된" 버전에만 있던 3시/9시 스왑 버그
`캡스톤 코드 파일/location_detector.py`(정리된 듯 보였던 사본)에는 `베트남 코드` 쪽
원본에는 없는 별도의 버그가 있었습니다 — 3시 방향과 9시 방향 판정 각도 구간이 서로
뒤바뀌어 있었습니다. 그래서 포트폴리오 정리본은 `베트남 코드/jetson/location_detector.py`를
기준으로 삼았습니다.

## 2. 스크러빙한 보안 이슈 (🚨 실제 노출된 값)

| 항목 | 원본 위치 | 조치 |
|---|---|---|
| Picovoice(Porcupine) 액세스 키 (평문) | `pi/porcupine.py`, `캡스톤 코드 파일/porcupine.py`, `end/pi_1.py` (총 3곳, 전부 동일한 키) | 환경변수 `PICOVOICE_ACCESS_KEY`로 치환. **원본 키는 코드에서 완전히 제거했으며, 실제 프로젝트에서 재사용 중이라면 Picovoice 콘솔에서 재발급을 권장합니다** |
| Google Cloud 프로젝트 ID가 노출된 인증 파일 경로 (`key-rider-443318-h3-...json`) | `PiDo.py`, `pi/googole_stt.py`, `pi/STTest.py` (파일마다 경로가 조금씩 다름) | 환경변수 `GOOGLE_APPLICATION_CREDENTIALS`로 치환 |
| 젯슨/카메라 내부 네트워크 IP 4~5개 (`10.2.76.67`, `192.168.6.235`, `192.168.0.19`, `10.2.74.234`, `192.168.6.191`, `10.2.79.121`) | 거의 모든 파일 | 환경변수(`CAMERA_STREAM_URL`, `JETSON_HOST` 등)로 치환 |

## 3. 구조적 문제 (원본 그대로 두고 문서화만 함)

- **Pi가 서버 역할을 하는 버전과 클라이언트 역할을 하는 버전이 공존**: `PiDo.py`(클라이언트)와
  `end/pi_1.py`(서버) 두 가지 아키텍처 시도가 있었는데, 젯슨 쪽(`JetDo.py`)이 항상 서버였기
  때문에 `end/pi_1.py` 쪽은 애초에 연결이 불가능했습니다. → `docs/ARCHITECTURE.md` 참고.
- **`jetson/main.py`가 양쪽 폴더 모두 빈 파일(0바이트)**: 각 기능(YOLO 탐지, 소켓 서버)을
  하나로 묶는 진입점을 만들 계획이었으나 구현되지 않았고, 대신 `JetDo.py`가 사실상 그
  역할을 대신한 것으로 보입니다. 포트폴리오에서는 존재하지 않았던 통합을 지어내지 않고,
  `jetson/ingredient_locator_server.py`를 진입점으로 명시했습니다.
- **음성 파일 경로 불일치**: `PiDo.py`는 `voice/ingredients/Bread.wav`(복수형 폴더 +
  대문자)를 참조하지만 실제 에셋은 `voice/ingredient/bread.wav`(단수형 + 소문자)이고,
  `step_4/invalid_ingredient.wav`는 아예 존재하지 않습니다. → `assets/voice/README.md` 참고.
  실제 재현 시 조정이 필요한 부분이라 일부러 고치지 않았습니다.
- **`STTest.py`의 "next" vs "where is" 불일치**: 안내 문구는 "next"라고 말하라고 하지만
  실제 판정 로직은 "where is" 포함 여부만 검사합니다. `experiments/stt_two_stage_test.py`에
  주석으로 남겨두고 수정하지 않았습니다.

## 4. 중복 파일 정리

`베트남 코드/jetson/`과 `캡스톤 코드 파일/`에 `ingredient_detector.py`, `motioneye.py`,
`socket.py`가 스트림 IP만 다른 채 거의 동일하게 중복되어 있었습니다. `pi/porcupine.py`는
두 폴더에 완전히 동일한(byte-identical) 사본으로 존재했습니다. 포트폴리오에는 각각 한 벌만
남기고, 중복이었다는 사실만 이 문서에 기록했습니다.

## 5. 기타 정리한 죽은 코드

- `jetson/ingredient_detector.py`(원본)의 어디에서도 쓰이지 않던 `required_ingredients`
  리스트를 제거했습니다.
- `pi/pi_socket.py`(원본) 하단에 통째로 주석 처리되어 있던 실험용 대체 구현을 삭제했습니다.
- `pi/espeak_ng.py`(원본)의 미사용 `sleep` import, 주석 처리된 독일어 예시를 삭제했습니다.
- `jetson/socket.py` → `experiments/socket_echo_test.py`로 리네임했습니다 (표준 라이브러리
  `socket` 모듈과 이름이 겹쳐 import 충돌을 일으킬 수 있는 문제였습니다).
