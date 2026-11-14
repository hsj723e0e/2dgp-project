"""The workshop's stations, obstacles, and station catalogues."""

from dataclasses import dataclass
from math import hypot

from player import Rect


WIDTH, HEIGHT = 1280, 720
WALKABLE_ROOM = Rect(58, 65, 1220, 400)


OBSTACLES = (
    Rect(128, 382, 465, 570),
    Rect(45, 130, 208, 420),
    Rect(530, 420, 750, 605),
    Rect(855, 382, 1160, 570),
    Rect(1060, 140, 1228, 420),
    Rect(0, 0, 110, 100),
    Rect(1170, 0, WIDTH, 100),
)


@dataclass(frozen=True)
class Entry:
    name: str
    image: str
    description: str


@dataclass(frozen=True)
class Station:
    name: str
    x: int
    y: int
    subtitle: str
    entries: tuple


EQUIPMENT = (
    Entry("고철 드릴", "eq_drill_01", "초급 드릴 · 재활용 부품 + 전자회로"),
    Entry("보급형 우주복", "eq_suit_01", "초급 우주복 · 재활용 부품 + 전자회로"),
    Entry("소형 산소통", "eq_oxygen_01", "초급 산소 장치 · 재활용 부품 + 전자회로"),
    Entry("합금 드릴", "eq_drill_02", "중급 드릴 · 고급 복합소재 + 전자회로"),
    Entry("강화 우주복", "eq_suit_02", "중급 우주복 · 고급 복합소재 + 전자회로"),
    Entry("순환형 산소통", "eq_oxygen_02", "중급 산소 장치 · 고급 복합소재 + 전자회로"),
)

MATERIALS = (
    Entry("재활용 부품", "mat_01", "기본 재료 1 · 초급 장비의 주재료"),
    Entry("고급 복합소재", "mat_02", "기본 재료 2 · 중급 장비의 주재료"),
    Entry("전자회로", "mat_03", "기본 재료 3 · 초급·중급 장비의 공통 재료"),
)

CUSTOMERS = (
    Entry("초보 작업자", "npc_novice", "대여 성공 보상 · 정밀제어칩"),
    Entry("전문 탐사원", "npc_expert", "대여 성공 보상 · 고출력 코어"),
    Entry("우주 관광객", "npc_tourist", "판매·대여 보상 · 골드"),
    Entry("수상한 손님", "npc_mysterious", "대여 성공 보상 · 미확인 아이템"),
    Entry("정보상", "npc_broker", "공방의 시장 사건 정보를 제공하는 손님"),
)

PERSONAL_EQUIPMENT = (
    Entry("플라스마 드릴", "eq_drill_03", "최상급 드릴 · 고출력 코어 12개로 제작"),
    Entry("첨단 탐사복", "eq_suit_03", "최상급 우주복 · 고출력 코어 12개로 제작"),
    Entry("자급형 생명유지장치", "eq_oxygen_03", "최상급 산소 장치 · 고출력 코어 12개로 제작"),
    Entry("정밀제어칩", "item_chip", "개인 장비 강화 시 3개 사용"),
    Entry("고출력 코어", "item_core", "최상급 장비 제작 시 12개 사용"),
    Entry("미확인 상자", "item_secret", "수상한 손님 대여 보상 · 효과 미정"),
)


STATIONS = (
    Station("작업대", 290, 345,
            "필요 재료를 조합 슬롯에 넣고 제작하세요. 완성품은 자동 회수됩니다.", EQUIPMENT),
    Station("재료 보관대", 255, 230,
            "수량을 선택하고 코인으로 기본 재료를 구매하세요.", MATERIALS),
    Station("주문 게시판", 640, 360,
            "공방을 찾는 손님과 대여 보상을 확인하세요.", CUSTOMERS),
    Station("장비 진열대", 990, 345,
            "장비 종류별 보관함과 캐릭터 가방 사이에서 장비를 옮기세요.", EQUIPMENT),
    Station("강화 장치", 1005, 225,
            "나만의 최상급 장비와 성장 재료를 확인하세요.", PERSONAL_EQUIPMENT),
)


def nearest_station(player):
    if not STATIONS:
        return None
    station = min(STATIONS, key=lambda item: hypot(player.x - item.x, player.y - item.y))
    distance = hypot(player.x - station.x, player.y - station.y)
    return station if distance <= 100 else None
