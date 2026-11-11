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


STATIONS = (

)


def nearest_station(player):
    if not STATIONS:
        return None
    station = min(STATIONS, key=lambda item: hypot(player.x - item.x, player.y - item.y))
    distance = hypot(player.x - station.x, player.y - station.y)
    return station if distance <= 100 else None
