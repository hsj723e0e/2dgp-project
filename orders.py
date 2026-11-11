"""Customer orders generated from the workshop's equipment catalogue."""

from collections import Counter
from dataclasses import dataclass

from workshop import CUSTOMERS, EQUIPMENT


BASIC_EQUIPMENT = tuple(entry.image for entry in EQUIPMENT[:3])
MEDIUM_EQUIPMENT = tuple(entry.image for entry in EQUIPMENT[3:])
ALL_EQUIPMENT = BASIC_EQUIPMENT + MEDIUM_EQUIPMENT
CUSTOMER_NAMES = {entry.image: entry.name for entry in CUSTOMERS}


@dataclass(frozen=True)
class Order:
    identifier: int
    customer: str
    requirements: tuple

    @property
    def quantity(self):
        return sum(quantity for _, quantity in self.requirements)


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
