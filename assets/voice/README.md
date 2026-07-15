# 음성 안내 에셋

`pi/ingredient_locator_client.py` 등에서 재생하는 안내 음성(mp3/wav) 모음이다.

## 포함된 폴더

- `clock/` — 1~12시 방향 안내 (24개 = 12 × mp3/wav)
- `ingredient/` — 재료명 안내: bread, cheese, egg, ham, lettuce, tomato (각 mp3/wav)
- `recipe/` — 샌드위치 레시피 안내 1~4단계
- `step_1/`, `step_2/`, `step_3/`, `step_4/` — 단계별 진행 안내

## 원본에서 제외한 것

원본 `베트남 코드/voice/` 안에는 위 폴더들과 거의 동일한 내용이지만 파일명 끝에
공백이 붙은 중복 폴더가 별도로 있었다 (`_clock/`, `_ingredient/`, `_step_1/`~`_step_4/`,
예: `"1 .mp3"`처럼 숫자와 확장자 사이에 공백). OS별 파일 복사 과정에서 생긴 것으로 보이는
사실상 동일한 사본이라 포트폴리오 정리본에는 포함하지 않았다.

## 알려진 불일치 (docs/KNOWN_ISSUES.md 참고)

`베트남 코드/PiDo.py` 원본 코드는 `voice/ingredients/Bread.wav`처럼 **복수형 폴더명 +
대문자 시작 파일명**을 참조하지만, 실제 존재하는 파일은 `voice/ingredient/bread.wav`처럼
**단수형 폴더명 + 소문자 파일명**이다. 또한 `step_4/invalid_ingredient.wav`도 코드에는
참조되지만 실제로는 존재하지 않는다. 프로젝트가 끝까지 통합 테스트되지 못했음을 보여주는
증거라서 임의로 파일명을 바꾸지 않고 그대로 두었다.
