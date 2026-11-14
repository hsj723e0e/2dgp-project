"""Customer orders generated from the workshop's equipment catalogue."""

from collections import Counter
from dataclasses import dataclass

from workshop import CUSTOMERS, EQUIPMENT


BASIC_EQUIPMENT = tuple(entry.image for entry in EQUIPMENT[:3])
MEDIUM_EQUIPMENT = tuple(entry.image for entry in EQUIPMENT[3:])
ALL_EQUIPMENT = BASIC_EQUIPMENT + MEDIUM_EQUIPMENT
CUSTOMER_NAMES = {entry.image: entry.name for entry in CUSTOMERS}
SALE_PRICES = {
    "eq_drill_01": 32, "eq_suit_01": 50, "eq_oxygen_01": 38,
    "eq_drill_02": 46, "eq_suit_02": 70, "eq_oxygen_02": 52,
}
INFORMATION_PRICE = 15
MARKET_INTERVAL = 60
RENTAL_SUCCESS_RATE = 0.85
RENTAL_DURATIONS = {"npc_novice": 25, "npc_expert": 30, "npc_tourist": 35, "npc_mysterious": 40}
REWARD_NAMES = {"coins": "코인", "item_chip": "정밀제어칩", "item_core": "고출력 코어", "item_secret": "미확인 상자"}


@dataclass(frozen=True)
class MarketEvent:
    name: str
    equipment: tuple


MARKET_EVENTS = (
    MarketEvent("소행성 채굴 구역 개방", ("eq_drill_01", "eq_drill_02")),
    MarketEvent("우주정거장 외벽 점검", ("eq_suit_01", "eq_suit_02", "eq_oxygen_01", "eq_oxygen_02")),
    MarketEvent("화물선 운항 중단", MEDIUM_EQUIPMENT),
)


@dataclass(frozen=True)
class Order:
    identifier: int
    customer: str
    requirements: tuple

    @property
    def quantity(self):
        return sum(quantity for _, quantity in self.requirements)


@dataclass
class RentalContract:
    order: Order
    due_at: float
    success_probability: float
    reward_item: str
    reward_amount: int
    status: str = "active"
    units: tuple = ()
    returned_count: int = 0
    received_reward: int = 0


def create_order(identifier, customer, rng):
    if customer not in CUSTOMER_NAMES:
        raise ValueError(f"Unknown customer: {customer}")
    if customer == "npc_broker":
        requested = []
    elif customer in ("npc_novice", "npc_expert"):
        pool = BASIC_EQUIPMENT if customer == "npc_novice" else MEDIUM_EQUIPMENT
        requested = rng.choices(pool, k=rng.randint(1, 2))
    elif customer == "npc_tourist":
        requested = rng.choices(ALL_EQUIPMENT, k=4)
    else:
        requested = rng.sample(ALL_EQUIPMENT, k=4)
    counts = Counter(requested)
    requirements = tuple((equipment, counts[equipment]) for equipment in ALL_EQUIPMENT if counts[equipment])
    return Order(identifier, customer, requirements)
