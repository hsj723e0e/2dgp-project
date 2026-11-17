# 나만의 우주공방

기획서의 공방을 내려다보기 시점으로 구현한 Python + pico2d 프로젝트입니다.
작업복·고글 차림의 주인공으로 공방을 이동하며 장비를 제작·판매·대여합니다.
20분 동안 코어와 칩을 모아 개인 최상급 장비를 제작하고 최대 +13까지 강화하는 것이 목표입니다.

## 실행

```powershell
python -m pip install -r requirements.txt
python main.py
```

Windows의 맑은 고딕을 자동으로 사용합니다. 다른 환경에서는 한국어 TTF 폰트의 경로를
`SPACE_WORKSHOP_FONT` 환경 변수로 지정할 수 있습니다.

## 조작

| 입력 | 동작 |
| --- | --- |
| WASD / 방향키 | 상하좌우 이동, 두 방향을 함께 누르면 대각선 이동 |
| E / Enter | 가까운 시설 이용, 근처 시설이 없으면 캐릭터 인벤토리, 열린 화면 닫기 |
| ↑ / ↓ 또는 W / S | 시설 화면의 항목 선택 |
| ← / → | 게시판의 판매 장비 선택 |
| Space | 제작·강화 실행, 판매 장비 선택 확정 |
| 1 / 2 | 작업대 필요 재료 투입 |
| 1 / 2 / 3 | 게시판 판매·정보 구매 / 대여 / 거절 |
| Tab | 게시판 주문·대여 현황, 강화 장치의 분류 전환 |
| F10 | 코인과 기본 재료 1·2·3을 각각 999로 설정 |
| 마우스 왼쪽 버튼 | 항목 선택, 보관함·가방 사이 1개 이동, 돌아가기 |
| 마우스 오른쪽 버튼 | 보관함·가방 사이 10개 이동 |
| Shift + 클릭 | 클릭한 종류의 아이템 전체 이동 |
| Esc | 시설 화면 닫기, 공방 화면에서 종료 |

작업대에서 초급·중급·고급 장비를 제작하고 재료 보관대에서 재료와 보상을 보관합니다.
주문 게시판에서는 판매·대여·거절을 선택하고 진열대에서는 종류별 보관함에 장비를 보관하거나 가방으로 꺼냅니다.
강화 장치에서는 개별 기본 장비 강화, 개인 장비 제작·강화, 성장 재료 확인을 이용할 수 있습니다.
보유·요구 수량 비교에서 충족한 보유량은 청록색, 요구량은 금색, 부족한 보유량은 붉은색으로 강조됩니다.
초기 자금은 100코인이며, 현재 코인은 화면 우상단에 표시됩니다.
새 게임을 시작하면 고철 드릴·보급형 우주복·소형 산소통을 각각 하나씩 가방에 지급합니다.

## 캐릭터 인벤토리와 보관함

근처에 이용할 시설이 없을 때 E / Enter를 누르면 3×3, 총 9칸의 가방이 열립니다.
E / Enter / Esc 또는 닫기 버튼으로 닫습니다. 시설 근처에서는 해당 시설을 우선 이용합니다.
가방이 열려 있는 동안 이동은 멈추고 제작·대여 시간은 계속 흐릅니다.
장비는 한 개당 한 칸을 차지하며 개별 강화 단계가 표시됩니다.
재료와 코어·칩·미확인 상자는 같은 종류끼리 수량 제한 없이 한 칸에 겹쳐 보관합니다.
개인 최상급 장비도 각각 가방 한 칸을 사용합니다. 코인은 칸을 사용하지 않습니다.

장비 진열대 왼쪽에서 9종 장비 중 하나를 선택하면 전용 7×4, 총 28칸 보관함이 열립니다.
보관함과 함께 가방을 표시하며 좌클릭은 1개, 우클릭은 최대 10개, Shift+클릭은
클릭한 종류의 장비 전체를 반대편으로 옮깁니다. 목적지의 빈칸만큼 이동하며 강화 단계를 유지합니다.
선택한 종류의 장비만 해당 보관함에 넣을 수 있습니다. 이동 시 고유 번호와 강화 단계를 유지합니다.
판매·대여와 기본 장비 강화에는 가방에 있는 장비를 사용합니다.
보관함의 장비를 거래하려면 먼저 가방으로 꺼냅니다.
가방이 가득 차면 보관함의 장비나 가방에 없는 종류의 재료·보상을 꺼낼 수 없습니다.
가방에 같은 종류의 재료·보상 묶음이 이미 있으면 수량을 합쳐 꺼낼 수 있습니다.
F10은 코인과 기본 재료 1·2·3을 각각 999로 설정합니다. 새 재료 종류를 위한 칸이 부족하면
필요한 수만큼 가방의 장비를 종류별 보관함으로 옮깁니다. 보관함에도 공간이 없으면
기존 재료·코인만 충전하고 공간 부족을 알립니다.

재료 보관대에는 재활용 부품·고급 복합소재·전자회로·정밀제어칩·고출력 코어·미확인 상자마다
전용 1×1 슬롯이 하나씩 있어 총 6칸을 표시합니다. 가방의 재료·보상을 클릭하면 해당 종류의
보관 칸으로 이동하고, 보관 칸을 클릭하면 가방으로 꺼냅니다. 좌클릭은 1개, 우클릭은 최대 10개,
Shift+클릭은 묶음 전체를 옮깁니다.
재료 목록 선택과 구매 기능은 제거했습니다. 제작·강화에는 가방에 꺼낸 재료·보상을 사용합니다.

## 장비 제작

| 장비 | 주재료 | 전자회로 | 제작 시간 |
| --- | --- | --- | --- |
| 고철 드릴 | 재활용 부품 2개 | 1개 | 10초 |
| 보급형 우주복 | 재활용 부품 3개 | 2개 | 12초 |
| 소형 산소통 | 재활용 부품 2개 | 2개 | 10초 |
| 합금 드릴 | 고급 복합소재 2개 | 1개 | 14초 |
| 강화 우주복 | 고급 복합소재 3개 | 2개 | 16초 |
| 순환형 산소통 | 고급 복합소재 2개 | 2개 | 14초 |
| 초경합금 드릴 | 고급 복합소재 4개 + 정밀제어칩 1개 | 3개 | 20초 |
| 고내압 탐사복 | 고급 복합소재 6개 + 정밀제어칩 1개 | 4개 | 24초 |
| 고효율 산소 재생기 | 고급 복합소재 4개 + 정밀제어칩 1개 | 4개 | 22초 |

작업대 오른쪽 보유 목록에서 장비를 선택합니다. 보유 수량은 캐릭터 가방과 해당 장비 보관함의 수량을 합산합니다.
아래에는 선택 장비의 필요 재료만 표시됩니다. 재료를 클릭하거나 1 / 2 / 3을 누르면
해당 재료의 필요 수량 전체가 조합 슬롯에 들어가며 보유 수량이 즉시 줄어듭니다.
충족한 슬롯은 밝은 청록색 테두리로 강조합니다. 슬롯을 클릭해 해제하거나
장비 선택을 바꾸거나 화면을 닫으면 제작 전 투입한 재료가 반환됩니다.
모든 재료를 넣은 뒤 제작 버튼 또는 Space를 누르면 제작을 시작합니다.
작업대는 한 번에 장비 하나를 제작합니다. 메뉴를 닫고 공방을 이동해도 제작 시간은 흐릅니다.
제작 시간이 끝나면 완성품이 자동으로 캐릭터 가방에 추가됩니다. 가방이 가득 찼다면
완성품은 작업대에서 대기하며, 빈칸이 생기면 자동으로 회수하고 다음 제작을 할 수 있습니다.
장비 진열대의 목록에는 종류별 보관 수량이 표시됩니다.

## 기본 장비 개별 강화

강화 장치의 기본 장비 강화 분류에서 3×3 가방에 있는 장비 한 개를 클릭해 선택합니다.
선택한 장비는 금색 테두리로 강조하며, 오른쪽에 현재·다음 강화 단계와 숫자를 강조한 비용을 표시합니다.
코인으로 강화 버튼 또는 Space를 누르면 선택한 장비의 강화 단계가 올라갑니다.
강화 비용은 다음 강화 단계에 초급 8, 중급 12, 고급 18을 곱한 코인입니다.
기본 장비는 +13까지 강화할 수 있으며, 강화 단계당 대여 성공률이 1%p 증가합니다.
여러 장비를 함께 대여하면 선택한 장비들의 평균 강화 단계로 성공률을 계산하고 최대 98%를 적용합니다.

## 개인 최상급 장비

강화 장치에서 Tab 또는 개인 최상급 장비 분류를 선택합니다.
플라스마 드릴·첨단 탐사복·자급형 생명유지장치를 각각 하나씩 제작할 수 있습니다.
장비 하나를 제작할 때 고출력 코어 12개를 사용하고 +0 개인 장비를 얻습니다.
이후 정밀제어칩 3개를 사용할 때마다 한 단계씩 올라가며 최대 +13까지 강화합니다.
표시 성능은 +0에서 100%, 강화 단계마다 10%p 증가하여 +13에서 230%입니다.
개인 장비는 개인 보유 상태로 관리되며 기본 거래 재고와 구분됩니다.

## 손님 주문

게시판에는 현재 방문한 손님 1명의 주문이 표시됩니다. 첫 손님은 초보 작업자입니다.
거래하거나 주문을 거절하면 8초 후 다음 손님이 방문합니다. 미처리 주문은 손님이 기다리는 동안 유지됩니다.

| 손님 | 요청 |
| --- | --- |
| 초보 작업자 | 초급 3종에서 총 1~2개, 중복 가능 |
| 전문 탐사원 | 중급·고급 6종에서 총 1~2개, 중복 가능 |
| 우주 관광객 | 초급·중급·고급 9종에서 총 4개, 중복 가능 |
| 수상한 손님 | 초급·중급·고급 9종 중 서로 다른 4종을 각 1개 |
| 정보상 | 코인으로 다음 시장 사건 정보 구매 |

게시판은 요청 장비를 `보급형 우주복 × 2`처럼 표시하고, 아래에 보유 아이템의 사진과 수량을 표시합니다.
요청하지 않은 보유 아이템은 사진·종류 배지·수량을 흑백으로 표시하고, 보유량이 0인 요청 품목 옆에는 빨간색 `없음!`을 표시합니다.
오른쪽 보상 영역은 판매·대여 두 칸으로 나누고 코인·칩·코어·상자 이미지와 수량으로 표시합니다.
우상단 보유 코인과 대여 현황의 보상에도 같은 코인·아이템 이미지를 사용합니다.
`1` 판매를 선택하면 ↑ ↓로 요청 항목을 고르고 ← →로 사용할 보유 장비를 선택한 뒤
Space 또는 선택 확정 버튼으로 판매합니다. `2` 대여를 선택하면 3×3 캐릭터 가방이 열립니다.
주문과 관계없는 아이템은 어둡게 표시하며 요구 장비를 수량만큼 클릭하면 즉시 대여를 시작합니다.
선택 중인 장비를 다시 클릭하면 선택을 해제합니다. 같은 장비 한 개를 중복 선택할 수 없습니다.
요청 장비가 모두 준비되어야 거래할 수 있습니다. 판매 시 선택한 장비를 즉시 차감하고 코인을 받습니다.
`3` 또는 거절 버튼으로 주문을 거절합니다.

기본 판매가는 고철 드릴 32, 보급형 우주복 50, 소형 산소통 38, 합금 드릴 46,
강화 우주복 70, 순환형 산소통 52코인입니다. 60초마다 시장 사건이 순환하며 영향을 받는
장비 판매가는 1.25배로 증가하며 소수 코인은 버립니다.
사건은 소행성 채굴 구역 개방(드릴), 우주정거장 외벽 점검(우주복·산소 장치),
화물선 운항 중단(중급·고급 장비) 순서입니다.

정보상에게는 `1` 또는 정보 구매 버튼으로 15코인을 지불하고 다음 시장 사건을 확인합니다.
구매한 정보는 게시판 하단에서 다음 시세 갱신까지 확인할 수 있습니다.

## 대여

게시판에서 `2` 또는 대여 버튼으로 주문 전체를 대여합니다. 장비는 즉시 가용 재고에서 차감되며,
메뉴를 닫고 이동하거나 다른 거래를 진행하는 동안에도 대여 시간이 흐릅니다.
계약 종료 시 성공하면 장비와 보상을 캐릭터 가방으로 받고, 실패하면 대여한 장비를 분실합니다.
가방이 가득 차면 반납 대기 상태가 되며 빈칸이 생길 때 장비부터 한 개씩 반환합니다.
장비 반환 후 보상 종류를 넣을 칸이 생기거나 같은 보상 묶음이 이미 있으면 보상을 지급합니다.
반납 대기 중 성공 판정을 다시 하거나 이미 받은 장비·보상을 중복 지급하지 않습니다.
결과는 자동으로 한 번만 처리됩니다. `Tab` 또는 대여 현황 버튼으로 진행 시간·반납·분실 결과를 확인합니다.
대여 현황에서 ↑ ↓ 또는 마우스로 계약을 선택할 수 있습니다.

| 손님 | 대여 시간 | 성공 보상 |
| --- | --- | --- |
| 초보 작업자 | 25초 | 장비 수량만큼 정밀제어칩 |
| 전문 탐사원 | 30초 | 장비 수량만큼 고출력 코어 |
| 우주 관광객 | 35초 | 대여 시작 시 판매가의 60% 코인 |
| 수상한 손님 | 40초 | 미확인 상자 1개 |

기본 성공률은 85%이며, 개별 장비 선택 화면에서 강화 단계를 반영한 성공률을 미리 확인합니다.
계약 시작 시 선택 장비·성공률·보상을 저장하며, 성공 시 같은 장비가 같은 강화 단계로 돌아옵니다.
진열대에서는 종류별 보관 수량과 가방을 확인하고, 강화 장치에서는 칩·코어·미확인 상자의 보유 수량을 확인합니다.
미확인 상자의 효과는 기획서에서 미정으로 되어 있습니다.

## 운영 시간과 결과

한 판은 20분이며 공방 좌상단에서 남은 시간을 확인할 수 있습니다. 마지막 1분은 붉은색으로 표시됩니다.
시간이 끝나면 종료 시점까지 완료된 대여를 정산하고 개인 장비 강화 단계·표시 성능,
판매 건수·제작 회수 수량·대여 성공·분실·미종료 대여와 보유 코인을 결과 화면에 표시합니다.
운영 종료 시점까지 완성되고 가방 공간이 있는 장비는 자동 회수하며 이후 거래·제작·강화가 종료됩니다.
결과 화면에서 R / Enter 또는 새 게임 버튼으로 초기 자금 100코인과 초급 장비 3종을 가진 새 세션을 시작합니다.

## 파일

- `main.py` — pico2d 실행, 입력 처리, 화면과 시설 메뉴 표시
- `player.py` — 이동 속도, 발 위치 충돌, 방향별 걷기 애니메이션
- `workshop.py` — 공방의 이동 영역, 시설 배치와 안내 내용
- `game_state.py` — 가방·보관함 재고, 코인·제작·대여와 공간 대기 처리
- `inventory_panel.py` — 3×3 가방, 종류별 7×4 장비 보관함과 재료·보상 전용 6칸 보관대
- `orders.py` — 손님별 주문 수량·종류 생성
- `customer_board.py` — 현재 손님의 주문 게시판
- `enhancement_panel.py` — 개별 장비 강화, 개인 장비 제작·강화, 성장 재료 화면
- `session_results.py` — 최종 성장 결과와 운영 실적, 새 게임 시작
- `ui.py` — 시설 화면의 공통 색상과 사각형 그리기
- `asset/bg_workshop_room.png` — 내려다보기 공방 배경, 1280×720
- `asset/player_walk.png` — 4방향 주인공 스프라이트 시트, 256×384
- `documents/` — 기획서와 발표 자료

주인공 시트는 위에서부터 아래·왼쪽·오른쪽·위 방향이며, 각 행에 64×96 크기의
대기·걷기·중간·걷기 프레임 4개가 있습니다. 이동 속도는 초당 570픽셀(기존의 3배)이며 대각선도
같은 속도로 이동합니다. 발 아래의 충돌 영역을 기준으로 벽과 가구를 통과하지 못합니다.

배경과 주인공은 ImageGen 내장 도구로 제작했습니다. 배경에는 기존 에셋의 색감과
공방 구성을 참조해 열린 바닥 공간을 가진 내려다보기 시점을 요청했습니다.
주인공에는 초보 작업자 초상화의 작업복·고글 외형과 투명 배경의 4방향 걷기 시트를 요청했습니다.

## 아이템 단계와 종류 표시

| 단계 | 아이템 | 테두리 |
| --- | --- | --- |
| 1 | 재활용 부품·고급 복합소재·전자회로 | 흰색 |
| 2 | 고철 드릴·보급형 우주복·소형 산소통 | 연두색 |
| 3 | 합금 드릴·강화 우주복·순환형 산소통 | 파란색 |
| 4 | 초경합금 드릴·고내압 탐사복·고효율 산소 재생기 | 보라색 |
| 5 | 플라스마 드릴·첨단 탐사복·자급형 생명유지장치 | 노란색 |

아이템 우측 상단의 배지로 장비 종류와 기본 재료 3종을 구분합니다.
주황색 드릴 날·하늘색 헬멧·청록색 O₂ 기호를 남색 바탕과 밝은 테두리에 표시합니다.
기본 재료 1·2·3은 황금색 톱니바퀴 배지로 통일합니다.
가방과 보관함의 선택 표시는 단계 테두리 바깥에 별도 테두리로 표시합니다.
인벤토리·보관함·제작·강화·주문·결과 화면에서 같은 표시를 사용합니다.

종류 아이콘은 내장 ImageGen으로 생성한 투명 PNG를 64×64로 정규화했습니다.
에셋은 `asset/ui_category_drill.png`, `asset/ui_category_suit.png`, `asset/ui_category_oxygen.png`입니다.
생성에 사용한 공통 프롬프트와 종류별 subject는 다음과 같습니다.

```text
Create one production-ready square category badge asset matching the bottom row of the supplied approved game UI mockup. The supplied image is a visual reference. ONLY draw the badge, with no inventory tile, item sprite, text captions, or scenery. Dark navy filled square with subtly clipped pixel corners, a clean bright pale outline, and one large flat bold glyph filling most of the interior. Crisp low-detail pixel-art edges, designed to stay readable at 24x24 pixels. Transparent outside the badge silhouette. Keep the three category badges visually consistent. {subject}

drill subject = An orange spiral drill bit pointing diagonally upward-right, matching the bottom-left badge in the reference. Use orange #FFA600. No text.
suit subject = A sky-blue astronaut helmet outline with a bold visor and short flat collar, matching the bottom-middle badge in the reference. Use sky blue #77DAFF. No text.
oxygen subject = A turquoise oxygen-cylinder silhouette with a thick top valve. Bold dark navy O₂ printed clearly on the cylinder body, matching the bottom-right badge in the reference. Use turquoise #24E4D2. The only text is O₂.
```

기본 재료 배지는 `asset/ui_category_parts.png`, `asset/ui_category_composite.png`,
`asset/ui_category_circuit.png`에 저장하며, 기존 종류 배지를 참조해 내장 ImageGen으로 생성했습니다.
생성 프롬프트는 다음과 같습니다.

```text
Create one production-ready square material-category badge matching the supplied existing game badge reference. The reference defines the dark navy filled square, clipped pixel corners and bright pale outline. Only draw this badge with one large flat bold material glyph inside, filling most of the interior. Crisp simple pixel-art edges and strong shapes, readable at 24x24 pixels. Transparent outside the badge silhouette. No scenery, no inventory item sprite, no captions, no letters or numbers. {subject}

parts subject = A warm amber-yellow mechanical cogwheel with a large dark circular centre, indicating recycled mechanical parts. Use amber #FFC45C.
composite subject = Three clearly separated stacked metal plates shown diagonally in isometric view, indicating advanced composite material. Use pale lavender #B6A5FF with a few darker separating edges.
circuit subject = A bright green microchip with a solid square centre and four short thick pins on each side, indicating electronic circuits. Use lime green #A4F56B with a dark square cutout in the centre.
```


코인 에셋 `asset/ui_coin.png`는 내장 ImageGen으로 생성한 투명 PNG를 64×64로 정규화했습니다.
생성 프롬프트는 다음과 같습니다.

```text
Use case: stylized-concept. Asset type: currency icon for a pixel-art space workshop crafting game. Draw ONE gold coin, shown almost front-facing with a slight three-quarter thickness. Bold circular silhouette, warm golden face, bright yellow top-left rim highlight, darker amber stepped rim and a few simple pixel reflections. A single recessed four-point star engraved in the centre suggests space exploration. Crisp chunky pixel-art edges, limited gold palette, strong contrast and simple readable shapes suitable for display at 24x24 or 32x32 pixels. Coin centred and occupying 85 percent of the square canvas. No letters, no numerals, no text, no extra coins, no floating sparkles, no drop shadow, no frame or badge. Genuine transparent background. Production-ready standalone game currency sprite.
```


### 중앙 주문 표지판

주문 게시판은 중앙 바닥의 독립형 표지판입니다. 가까이에서 E 또는 Enter로 이용합니다.
받침대만 이동을 막으며, 캐릭터와 표지판의 앞뒤 위치에 따라 그리는 순서를 바꿉니다.
위치와 크기는 `workshop.py`의 `ORDER_SIGN_POSITION`, `ORDER_SIGN_SIZE`에서 조정합니다.

내장 ImageGen으로 기존 공방 배경을 참조해 생성했습니다.
`asset/bg_workshop_room.png`는 벽 게시판을 제거한 1280×720 배경이며,
`asset/order_sign.png`는 투명 배경의 160×160 표지판입니다.
생성 프롬프트는 다음과 같습니다.

```text
Background edit prompt
Precisely edit the supplied 1280x720 pixel-art space workshop background. Remove ONLY the large dark rectangular noticeboard with cyan side lights in the upper central wall, between the left workbench and right equipment rack. Replace that noticeboard and its frame with matching ordinary dark navy metal wall panels, seams, bolts and the existing warm overhead light. Preserve the room geometry, perspective, floor grid, furniture, shelves, spacecraft window, plants, all other objects, lighting and pixel-art style exactly. The floor remains entirely empty. Do not add a new board or sign anywhere. Keep the original full composition and 16:9 framing, ideally the same 1280x720 dimensions. This is a background cleanup so a separate freestanding sign sprite can be placed on the central floor at runtime.

Sign sprite prompt
Generate a single standalone freestanding order notice sign sprite for the supplied pixel-art space workshop. The supplied room image is a style and perspective reference only. Draw ONLY a small industrial metal noticeboard supported by one sturdy central metal post and a wide stable low base with two short feet. Three-quarter front view matching the room furniture, with the top edge slightly visible. Rectangular board with warm brass metal edging, dark navy display face, a few small pinned cream order cards and tiny teal status lights. No words, letters, numerals, readable text or symbols that resemble writing. The full board, post and feet must be visible. Chunky crisp pixel art, warm amber and cyan lighting, suitable for a 144x144 pixel world prop. Transparent background, no surrounding room, no floor tile, no separate shadow. Square composition, the sign occupies almost the entire height and the feet sit close to the bottom edge with a small transparent margin. One asset only.
```

고급 장비의 기본 판매 가격은 초경합금 드릴 94, 고내압 탐사복 138, 고효율 산소 재생기 110코인입니다.
시세 사건의 종류별 수요 증가에도 고급 장비를 포함합니다.


### 고급 장비 에셋 생성 기록

내장 ImageGen으로 같은 종류의 중급 장비를 스타일 참조하여 각각 생성한 뒤,
128×128 투명 PNG로 정규화했습니다.
저장 경로는 `asset/eq_drill_advanced.png`, `asset/eq_suit_advanced.png`,
`asset/eq_oxygen_advanced.png`입니다.

```text
drill
Use case: stylized-concept. Production-ready equipment inventory sprite for a pixel-art space workshop game. The supplied image is a style and same-category reference only. Create ONE new higher-grade item. Subject: A heavy-duty tungsten-carbide industrial handheld drill, spiral pointed carbide bit facing left, dark gunmetal body with violet armor panels and small cyan indicators. Sturdy pistol grip. Clearly stronger than the reference alloy drill, using a physical metal bit. Match the reference chunky pixel-art outlines, limited palette, stepped highlights, item scale and perspective. Entire item centered, fill 85 percent of square canvas, all parts inside the frame. Transparent background. No floor, no shadow, no text, no category badge, no border, no yellow legendary styling. Crisp silhouette readable at 48 pixels.

suit
Use case: stylized-concept. Production-ready equipment inventory sprite for a pixel-art space workshop game. The supplied image is a style and same-category reference only. Create ONE new higher-grade item. Subject: A high-pressure exploration spacesuit shown front-facing, empty display suit with helmet, reinforced violet and charcoal pressure armor, pale grey joint seals and a large dark blue visor. Compact practical industrial protective suit. Match the reference chunky pixel-art outlines, limited palette, stepped highlights, item scale and perspective. Entire item centered, fill 85 percent of square canvas, all parts inside the frame. Transparent background. No floor, no shadow, no text, no category badge, no border, no yellow legendary styling. Crisp silhouette readable at 48 pixels.

oxygen
Use case: stylized-concept. Production-ready equipment inventory sprite for a pixel-art space workshop game. The supplied image is a style and same-category reference only. Create ONE new higher-grade item. Subject: A high-efficiency oxygen regenerator backpack, front three-quarter view, two compact violet and silver cylinders, central filtration cartridge, dark flexible hose connecting the valves, small cyan indicator lights. Readable breathing equipment silhouette. Match the reference chunky pixel-art outlines, limited palette, stepped highlights, item scale and perspective. Entire item centered, fill 85 percent of square canvas, all parts inside the frame. Transparent background. No floor, no shadow, no text, no category badge, no border, no yellow legendary styling. Crisp silhouette readable at 48 pixels.
```


## 행성 탐사

공방 화면 오른쪽 위의 **행성 항로 / 우주선 출입** 버튼으로 탐사 준비 화면을 엽니다.
목적지를 선택한 뒤 가방에서 드릴·우주복·산소 장치를 하나씩 직접 선택합니다.
기본·중급·고급·개인 최상급 장비 모두 사용할 수 있습니다.
장비가 가방에 있어야 출발하며, 보관함의 장비는 먼저 꺼냅니다.
비행 시작을 누르면 행성별 이동 시간이 흐르고 도착 알림이 표시됩니다.
도착한 뒤 **우주선 밖으로**를 누르면 해당 행성의 채집 지대로 나갑니다.
공방 시설은 비행 중에도 이용할 수 있습니다. 탐사에 나가기 전 선택 장비를 다시 확인합니다.

| 목적지 | 채집 자원 | 비행 |
| --- | --- | --- |
| 수성 | 재활용 부품·전자회로 | 4초 |
| 금성 | 재활용 부품·전자회로 | 5초 |
| 지구 | 전자회로 | 3초 |
| 화성 | 재활용 부품·전자회로 | 5초 |
| 목성 | 고급 복합소재·재활용 부품 | 7초 |
| 토성 | 고급 복합소재·재활용 부품 | 8초 |
| 천왕성 | 정밀제어칩·고급 복합소재 | 9초 |
| 해왕성 | 정밀제어칩·고급 복합소재 | 10초 |
| 태양 | 고출력 코어 | 12초 |

목성·토성·천왕성·해왕성·태양은 걸어서 탐사할 수 있는 SF 채굴 지대로 표현합니다.
각 목적지마다 별도의 1280×720 픽셀아트 배경을 사용합니다.

### 탐사 조작

| 입력 | 동작 |
| --- | --- |
| WASD / 방향키 | 이동 |
| E 길게 누르기 | 가까운 광맥 채집, 이동하면 중단 |
| Space / 좌클릭 | 드릴 근접 공격 |
| I / 인벤토리 버튼 | 가방 열기·닫기 |
| 착륙선 입구에서 E / Enter | 우주선으로 귀환 |
| Esc | 가방 닫기, 귀환 안내 |

채집 자원은 기존 가방에 바로 합쳐집니다. 같은 자원 묶음은 수량을 합치며 새 종류에는 빈칸이 필요합니다.
빈칸이 없으면 해당 광맥 채집을 중단합니다. 귀환 후 보관·제작·강화에 사용할 수 있습니다.
가방을 열어도 산소와 위험 요소의 시간은 흐릅니다.
체력이 0이 되면 공방으로 구조되고 이번 탐사 채집물을 잃습니다.
출발 전 보유 자원과 장비는 보존합니다. 정상 귀환 시 채집물이 유지됩니다.
우주선에서 다시 하선하면 체력·산소가 충전되고 새 광맥을 탐사합니다.
기존 20분 운영 시간은 비행·탐사 중에도 계속 흐릅니다.

### 장비 성능과 위험 요소

장비 등급 값은 초급 1, 중급 2, 고급 3, 개인 최상급 4입니다.
채집 속도 배율은 `1 + (드릴 등급 - 1) × 0.55 + 강화 단계 × 0.04`입니다.
광맥은 기본 1.6초마다 자원 1개를 지급하고, 채집 속도 배율에 따라 빨라집니다.
우주복의 피해 배율은 `1 / (1 + (등급 - 1) × 0.25 + 강화 단계 × 0.035)`입니다.
산소 최대량은 `90 + 산소 장치 등급 × 35 + 강화 단계 × 4`입니다.
행성 위험도는 지구 0, 수성·화성 1, 금성 2, 목성·토성 3, 천왕성·해왕성 4, 태양 5입니다.
산소는 초당 `1 + 위험도 × 0.16`씩 감소합니다.

- 외계 생물은 650픽셀 안의 채집 소리에 반응해 8초 동안 추적합니다. 접근하면 공격하며 드릴로 처치할 수 있습니다.
- 가스 분출 지점은 11초 주기이며 분출 전 2초간 노란 전조를 표시합니다. 분출은 1.5초 지속되고 원 밖으로 피할 수 있습니다.
- 불안정 광맥은 노란 원으로 구분합니다. 누적 채집 2초 후 균열 경고가 뜨고 1.5초 뒤 폭발합니다. 폭발 반경은 115픽셀입니다.
- 산소가 0이면 초당 체력 9를 잃습니다. 체력이 남아 있을 때 착륙선으로 돌아가 귀환할 수 있습니다.

### 탐사 에셋 생성 기록

내장 ImageGen으로 참고 화면의 픽셀아트 시점·색감에 맞춰 생성했습니다.
9개 배경은 `asset/bg_planet_*.png`, 투명 소품은 `asset/explore_ship.png`,
`asset/explore_deposit.png`, `asset/explore_alien.png`입니다.
우주복 4방향 이동 시트는 `asset/player_exploration.png`이며 256×384, 64×96 셀 16개입니다.
드릴 효과음 `asset/explore_drill.wav`는 코드로 합성한 0.2초 기계음입니다.

생성 프롬프트는 다음과 같습니다.

```text
asset/bg_planet_mercury.png
Use case: stylized-concept. Asset type: playable 1280x720 wide pixel-art space mining game background. The supplied screenshot is only a perspective and pixel-art style reference. Theme: Mercury, charcoal grey cratered rock, harsh white sunlight, scorched cliffs, sparse amber glints. Three-quarter top-down view with NO horizon. One broad rectangular traversable mining plateau filling the canvas. The central 85 percent is flat continuous ground with subtle small cracks, pebbles and surface texture ONLY, spacious enough for player and runtime resource sprites. Jagged low cliff edges and decorative rocks stay inside outermost 6 percent of image. Keep the landing area at left-center and all paths across center empty. Crisp chunky pixel art, dark navy outlines, clear navigable ground. No spaceship, no people, no creatures, no large crystal nodes, no interface, no minimap, no text, no labels, no icons, no foreground obstacles in playable center. 16:9 landscape.

asset/bg_planet_venus.png
Use case: stylized-concept. Asset type: playable 1280x720 wide pixel-art space mining game background. The supplied screenshot is only a perspective and pixel-art style reference. Theme: Venus, yellow ochre volcanic rock and sulphur haze, ochre cliffs, distant orange glowing fissures restricted to edges. Three-quarter top-down view with NO horizon. One broad rectangular traversable mining plateau filling the canvas. The central 85 percent is flat continuous ground with subtle small cracks, pebbles and surface texture ONLY, spacious enough for player and runtime resource sprites. Jagged low cliff edges and decorative rocks stay inside outermost 6 percent of image. Keep the landing area at left-center and all paths across center empty. Crisp chunky pixel art, dark navy outlines, clear navigable ground. No spaceship, no people, no creatures, no large crystal nodes, no interface, no minimap, no text, no labels, no icons, no foreground obstacles in playable center. 16:9 landscape.

asset/bg_planet_earth.png
Use case: stylized-concept. Asset type: playable 1280x720 wide pixel-art space mining game background. The supplied screenshot is only a perspective and pixel-art style reference. Theme: Earth, abandoned blue-green industrial scrapyard on rocky ground, tiny circuit fragments, sparse moss and broken machinery confined to map edges. Three-quarter top-down view with NO horizon. One broad rectangular traversable mining plateau filling the canvas. The central 85 percent is flat continuous ground with subtle small cracks, pebbles and surface texture ONLY, spacious enough for player and runtime resource sprites. Jagged low cliff edges and decorative rocks stay inside outermost 6 percent of image. Keep the landing area at left-center and all paths across center empty. Crisp chunky pixel art, dark navy outlines, clear navigable ground. No spaceship, no people, no creatures, no large crystal nodes, no interface, no minimap, no text, no labels, no icons, no foreground obstacles in playable center. 16:9 landscape.

asset/bg_planet_mars.png
Use case: stylized-concept. Asset type: playable 1280x720 wide pixel-art space mining game background. The supplied screenshot is only a perspective and pixel-art style reference. Theme: Mars, rust-red rocky desert, red sandstone cliffs, fine dust, distant dark basalt debris. Three-quarter top-down view with NO horizon. One broad rectangular traversable mining plateau filling the canvas. The central 85 percent is flat continuous ground with subtle small cracks, pebbles and surface texture ONLY, spacious enough for player and runtime resource sprites. Jagged low cliff edges and decorative rocks stay inside outermost 6 percent of image. Keep the landing area at left-center and all paths across center empty. Crisp chunky pixel art, dark navy outlines, clear navigable ground. No spaceship, no people, no creatures, no large crystal nodes, no interface, no minimap, no text, no labels, no icons, no foreground obstacles in playable center. 16:9 landscape.

asset/bg_planet_jupiter.png
Use case: stylized-concept. Asset type: playable 1280x720 wide pixel-art space mining game background. The supplied screenshot is only a perspective and pixel-art style reference. Theme: Jupiter fictional science-fiction solid mining island above swirling cream and orange gas clouds, brown layered rock terrain, gas clouds around edges. Three-quarter top-down view with NO horizon. One broad rectangular traversable mining plateau filling the canvas. The central 85 percent is flat continuous ground with subtle small cracks, pebbles and surface texture ONLY, spacious enough for player and runtime resource sprites. Jagged low cliff edges and decorative rocks stay inside outermost 6 percent of image. Keep the landing area at left-center and all paths across center empty. Crisp chunky pixel art, dark navy outlines, clear navigable ground. No spaceship, no people, no creatures, no large crystal nodes, no interface, no minimap, no text, no labels, no icons, no foreground obstacles in playable center. 16:9 landscape.

asset/bg_planet_saturn.png
Use case: stylized-concept. Asset type: playable 1280x720 wide pixel-art space mining game background. The supplied screenshot is only a perspective and pixel-art style reference. Theme: Saturn fictional science-fiction solid mining island above pale golden gas clouds, warm beige stone ground, ring fragments and gas clouds visible beyond outer edges. Three-quarter top-down view with NO horizon. One broad rectangular traversable mining plateau filling the canvas. The central 85 percent is flat continuous ground with subtle small cracks, pebbles and surface texture ONLY, spacious enough for player and runtime resource sprites. Jagged low cliff edges and decorative rocks stay inside outermost 6 percent of image. Keep the landing area at left-center and all paths across center empty. Crisp chunky pixel art, dark navy outlines, clear navigable ground. No spaceship, no people, no creatures, no large crystal nodes, no interface, no minimap, no text, no labels, no icons, no foreground obstacles in playable center. 16:9 landscape.

asset/bg_planet_uranus.png
Use case: stylized-concept. Asset type: playable 1280x720 wide pixel-art space mining game background. The supplied screenshot is only a perspective and pixel-art style reference. Theme: Uranus fictional solid frozen mining island, turquoise ice and pale cyan rock, dark teal crevices confined to edges, cold stars beyond cliffs. Three-quarter top-down view with NO horizon. One broad rectangular traversable mining plateau filling the canvas. The central 85 percent is flat continuous ground with subtle small cracks, pebbles and surface texture ONLY, spacious enough for player and runtime resource sprites. Jagged low cliff edges and decorative rocks stay inside outermost 6 percent of image. Keep the landing area at left-center and all paths across center empty. Crisp chunky pixel art, dark navy outlines, clear navigable ground. No spaceship, no people, no creatures, no large crystal nodes, no interface, no minimap, no text, no labels, no icons, no foreground obstacles in playable center. 16:9 landscape.

asset/bg_planet_neptune.png
Use case: stylized-concept. Asset type: playable 1280x720 wide pixel-art space mining game background. The supplied screenshot is only a perspective and pixel-art style reference. Theme: Neptune fictional solid frozen mining island, deep cobalt and indigo rock, blue ice, edge cliffs above dark storm clouds. Three-quarter top-down view with NO horizon. One broad rectangular traversable mining plateau filling the canvas. The central 85 percent is flat continuous ground with subtle small cracks, pebbles and surface texture ONLY, spacious enough for player and runtime resource sprites. Jagged low cliff edges and decorative rocks stay inside outermost 6 percent of image. Keep the landing area at left-center and all paths across center empty. Crisp chunky pixel art, dark navy outlines, clear navigable ground. No spaceship, no people, no creatures, no large crystal nodes, no interface, no minimap, no text, no labels, no icons, no foreground obstacles in playable center. 16:9 landscape.

asset/bg_planet_sun.png
Use case: stylized-concept. Asset type: playable 1280x720 wide pixel-art space mining game background. The supplied screenshot is only a perspective and pixel-art style reference. Theme: Sun fictional shielded dark basalt mining island above solar plasma, black-red rock terrain, fiery golden plasma beyond outer cliffs, orange light around edges. Three-quarter top-down view with NO horizon. One broad rectangular traversable mining plateau filling the canvas. The central 85 percent is flat continuous ground with subtle small cracks, pebbles and surface texture ONLY, spacious enough for player and runtime resource sprites. Jagged low cliff edges and decorative rocks stay inside outermost 6 percent of image. Keep the landing area at left-center and all paths across center empty. Crisp chunky pixel art, dark navy outlines, clear navigable ground. No spaceship, no people, no creatures, no large crystal nodes, no interface, no minimap, no text, no labels, no icons, no foreground obstacles in playable center. 16:9 landscape.

asset/explore_ship.png
Use case: stylized-concept. Create a single standalone transparent PNG game sprite. The reference is a visual style reference for a space mining game. A small landed industrial spaceship with silver armored hull, amber cockpit and a warm glowing open front hatch, two landing feet and short ramp extending toward bottom-right. Three-quarter top-down view. One complete standalone spaceship. No ground or shadow. Crisp chunky pixel-art edges, dark outline, sparse highlights, navy shadows, amber/cyan accents matching the reference. Centered square composition, all parts visible, use 85 percent of canvas. No HUD, no words, no letters, no border, no surrounding scene.

asset/explore_deposit.png
Use case: stylized-concept. Create a single standalone transparent PNG game sprite. The reference is a visual style reference for a space mining game. One compact jagged dark rock outcrop with vivid teal mineral crystals embedded in it, suitable for a mineable resource node in a top-down game. Chunky silhouette and a few bright crystal facets. No floor or shadow. Crisp chunky pixel-art edges, dark outline, sparse highlights, navy shadows, amber/cyan accents matching the reference. Centered square composition, all parts visible, use 85 percent of canvas. No HUD, no words, no letters, no border, no surrounding scene.

asset/explore_alien.png
Use case: stylized-concept. Create a single standalone transparent PNG game sprite. The reference is a visual style reference for a space mining game. One small hostile alien beetle with magenta-purple armored carapace, four squat legs, glowing orange eyes and small pointed mandibles, facing down-right in three-quarter top-down view. Readable full creature silhouette. No floor or shadow. Crisp chunky pixel-art edges, dark outline, sparse highlights, navy shadows, amber/cyan accents matching the reference. Centered square composition, all parts visible, use 85 percent of canvas. No HUD, no words, no letters, no border, no surrounding scene.

asset/player_exploration.png
Edit this pixel-art player walk sprite sheet into a space exploration version of the same protagonist. Preserve EXACTLY the 4 columns by 4 rows grid, all 16 frame positions, frame dimensions and direction rows. Top row faces down, second faces left, third faces right, fourth faces up. Within each row frame 1 standing, frames 2-4 walking. Replace work clothes with a compact pale silver spacesuit, dark navy joints, amber helmet rim, clear blue visor revealing the same brown-haired face and goggles in front frames, small oxygen backpack on back frames. Keep exact body size, foot baseline, pose silhouettes, pixel scale and transparent margins of each original cell. No rearranging, no overlapping adjacent cells, no text, no borders. Genuine transparent background, sheet aspect ratio 2:3. Each cell logically 64x96, full sheet 256x384. Crisp pixel art matching the original.
Transparency cleanup
Remove the entire grey-brown gradient background from this sprite sheet, making all space outside the 16 astronaut silhouettes genuinely transparent. Preserve every astronaut pixel, all exact positions, the 4 by 4 grid, the full canvas framing, aspect ratio, colors, poses and cell baselines. Do not redraw, scale or move characters. No shadows or glows outside the figures. Deliver a transparent PNG sprite sheet.
```


### 체력·산소 상태 게이지 에셋

내장 ImageGen으로 제작한 `asset/ui_mining_health.png`와 `asset/ui_mining_oxygen.png`를 사용합니다.
두 파일은 투명 여백을 정리한 320×78 PNG입니다.
하트와 산소통 아이콘으로 게이지를 구분하고 실제 체력·산소량에 따라 내부 채움과 현재·최대 숫자가 바뀝니다.
산소 부족 상태는 붉은색으로 강조합니다.

생성 프롬프트는 다음과 같습니다.

```text

asset/ui_mining_health.png
Use case: stylized-concept. Asset type: a single empty horizontal HUD meter frame for a pixel-art sci-fi mining game. A clearly recognizable bright red pixel heart icon in the left badge. Pale silver frame with warm brass tiny corner rivets and red accent notches. Draw one compact wide rectangular industrial meter frame with a larger square icon badge on the left, connected to a long horizontal EMPTY dark navy inset meter well on the right. Crisp chunky pixel-art, clean 2-3 pixel stepped outer edges, high readability, restrained mechanical detail. Overall frame silhouette approximately six times wider than tall. The empty meter well is a SIMPLE straight rectangular region, starts 25 percent from the left, ends 95 percent from left, spans 32 to 68 percent of the total height. Keep that exact clear rectangular region uninterrupted so runtime code can draw a colored fill over it. No filled colored meter, no bars inside, no numerals, no captions, no words other than the O₂ symbol if specified. One complete frame only, no variants, no sheet. Center the frame on genuine transparent background with no scenery, no drop shadow or glow outside. Wide composition.

asset/ui_mining_oxygen.png
Use case: stylized-concept. Asset type: a single empty horizontal HUD meter frame for a pixel-art sci-fi mining game. A clearly recognizable small cyan oxygen cylinder with dark navy O₂ symbol in the left badge. Pale silver frame with cyan accent notches and tiny brass corner rivets. Draw one compact wide rectangular industrial meter frame with a larger square icon badge on the left, connected to a long horizontal EMPTY dark navy inset meter well on the right. Crisp chunky pixel-art, clean 2-3 pixel stepped outer edges, high readability, restrained mechanical detail. Overall frame silhouette approximately six times wider than tall. The empty meter well is a SIMPLE straight rectangular region, starts 25 percent from the left, ends 95 percent from left, spans 32 to 68 percent of the total height. Keep that exact clear rectangular region uninterrupted so runtime code can draw a colored fill over it. No filled colored meter, no bars inside, no numerals, no captions, no words other than the O₂ symbol if specified. One complete frame only, no variants, no sheet. Center the frame on genuine transparent background with no scenery, no drop shadow or glow outside. Wide composition.
```

## 발표 영상

1차 발표: https://www.youtube.com/watch?v=1Wmip-6BfUY

2차 발표: https://www.youtube.com/watch?v=sCiKfOYbg6U

📎 **발표 자료**: [개발진행보고 PPT](documents/%EA%B0%9C%EB%B0%9C%EC%A7%84%ED%96%89%EB%B3%B4%EA%B3%A0.pptx) · [발표자료 PDF](documents/%EB%B0%9C%ED%91%9C%EC%9E%90%EB%A3%8C.pdf) · [기획서 PDF](documents/%EA%B8%B0%ED%9A%8D%EC%84%9C.pdf)
