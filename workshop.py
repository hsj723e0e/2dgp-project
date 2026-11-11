"""The workshop's stations, obstacles, and read-only station panels."""

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


STATIONS = (
    Station("작업대", 290, 345,
            "제작 가능한 초급·중급 장비와 재료를 살펴보세요.", EQUIPMENT),
    Station("재료 보관대", 255, 230,
            "장비 제작에 사용하는 기본 재료 3종입니다.", MATERIALS),
    Station("주문 게시판", 640, 360,
            "공방을 찾는 손님과 대여 보상을 확인하세요.", CUSTOMERS),
)


def nearest_station(player):
    if not STATIONS:
        return None
    station = min(STATIONS, key=lambda item: hypot(player.x - item.x, player.y - item.y))
    distance = hypot(player.x - station.x, player.y - station.y)
    return station if distance <= 100 else None
