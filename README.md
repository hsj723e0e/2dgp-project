# 나만의 우주공방

기획서의 공방을 내려다보기 시점으로 구현한 Python + pico2d 프로젝트입니다.
작업복·고글 차림의 주인공으로 공방을 이동할 수 있습니다.

## 실행

```powershell
python -m pip install -r requirements.txt
python main.py
```

Windows의 맑은 고딕을 자동으로 사용합니다. 다른 환경에서는 한국어 TTF 폰트의 경로를
`SPACE_WORKSHOP_FONT` 환경 변수로 지정할 수 있습니다.

## 조작

WASD / 방향키로 이동하고 Esc로 종료합니다.

가까운 시설에서 E / Enter로 메뉴를 열 수 있습니다.
↑ ↓ 또는 마우스로 항목을 선택하고 E / Esc로 닫습니다.

이용 가능한 시설은 작업대, 재료 보관대입니다.

발 위치를 기준으로 벽·가구와 충돌하며, 대각선 이동 속도도 동일합니다.
