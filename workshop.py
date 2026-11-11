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


STATIONS = (
    Station("작업대", 290, 345,
            "제작 가능한 초급·중급 장비와 재료를 살펴보세요.", EQUIPMENT),
)


def nearest_station(player):
    if not STATIONS:
        return None
    station = min(STATIONS, key=lambda item: hypot(player.x - item.x, player.y - item.y))
    distance = hypot(player.x - station.x, player.y - station.y)
    return station if distance <= 100 else None
