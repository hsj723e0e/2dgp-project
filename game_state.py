"""Session currency, inventory, and the workbench's single crafting job."""

from dataclasses import dataclass
import random
from time import monotonic

from orders import CUSTOMER_NAMES, create_order
from workshop import EQUIPMENT


MATERIAL_PRICES = {"mat_01": 8, "mat_02": 12, "mat_03": 4}
CUSTOMER_INTERVAL = 8


@dataclass(frozen=True)
class Recipe:
    ingredients: dict
    seconds: float


RECIPES = {
    "eq_drill_01": Recipe({"mat_01": 2, "mat_03": 1}, 10),
    "eq_suit_01": Recipe({"mat_01": 3, "mat_03": 2}, 12),
    "eq_oxygen_01": Recipe({"mat_01": 2, "mat_03": 2}, 10),
    "eq_drill_02": Recipe({"mat_02": 2, "mat_03": 1}, 14),
    "eq_suit_02": Recipe({"mat_02": 3, "mat_03": 2}, 16),
    "eq_oxygen_02": Recipe({"mat_02": 2, "mat_03": 2}, 14),
}


@dataclass(frozen=True)
class CraftJob:
    equipment: str
    ready_at: float


class GameState:
    def __init__(self, clock=monotonic, rng=None):
        self.coins = 100
        self.materials = {name: 0 for name in MATERIAL_PRICES}
        self.equipment = {entry.image: 0 for entry in EQUIPMENT}
        self.job = None
        self.clock = clock
        self.rng = rng if rng is not None else random.Random()
        self.current_order = create_order(1, "npc_novice", self.rng)
        self.next_order_id = 2
        self.next_customer_at = None

    @property
    def next_customer_in(self):
        if self.current_order is not None or self.next_customer_at is None:
            return 0.0
        return max(0.0, self.next_customer_at - self.clock())

    def update_customers(self):
        if self.current_order is not None or self.next_customer_at is None:
            return
        if self.clock() < self.next_customer_at:
            return
        customer = self.rng.choices(tuple(CUSTOMER_NAMES), weights=(45, 20, 20, 10, 5), k=1)[0]
        self.current_order = create_order(self.next_order_id, customer, self.rng)
        self.next_order_id += 1
        self.next_customer_at = None

    def finish_order(self):
        next_customer_at = self.clock() + CUSTOMER_INTERVAL
        self.current_order = None
        self.next_customer_at = next_customer_at

    def decline_order(self, order_id):
        if self.current_order is None or self.current_order.identifier != order_id:
            return False, "이미 처리된 주문입니다."
        self.finish_order()
        return True, "주문을 거절했습니다. 다음 손님을 기다려 주세요."

    def purchase_status(self, material, quantity):
        if material not in MATERIAL_PRICES:
            return False, "구매할 수 없는 재료입니다."
        if type(quantity) is not int or quantity < 1:
            return False, "구매 수량은 1개 이상이어야 합니다."
        cost = MATERIAL_PRICES[material] * quantity
        if self.coins < cost:
            return False, "코인이 부족합니다."
        return True, ""

    def purchase(self, material, quantity):
        available, reason = self.purchase_status(material, quantity)
        if not available:
            return False, reason
        self.coins -= MATERIAL_PRICES[material] * quantity
        self.materials[material] += quantity
        return True, f"재료 {quantity}개를 구매했습니다."

    @property
    def remaining(self):
        if self.job is None:
            return 0.0
        return max(0.0, self.job.ready_at - self.clock())

    @property
    def ready_to_collect(self):
        return self.job is not None and self.remaining <= 0

    def craft_status(self, equipment):
        if equipment not in RECIPES:
            return False, "제작할 수 없는 장비입니다."
        if self.job is not None:
            if self.ready_to_collect:
                return False, "완성품을 먼저 회수하세요."
            return False, "작업대에서 장비를 제작 중입니다."
        ingredients = RECIPES[equipment].ingredients
        if any(self.materials[name] < quantity for name, quantity in ingredients.items()):
            return False, "재료가 부족합니다."
        return True, ""

    def start_craft(self, equipment):
        available, reason = self.craft_status(equipment)
        if not available:
            return False, reason
        recipe = RECIPES[equipment]
        ready_at = self.clock() + recipe.seconds
        for name, quantity in recipe.ingredients.items():
            self.materials[name] -= quantity
        self.job = CraftJob(equipment, ready_at)
        return True, "제작을 시작했습니다. 완성 후 회수하세요."

    def collect(self):
        if self.job is None:
            return False, "회수할 완성품이 없습니다."
        if not self.ready_to_collect:
            return False, "아직 제작 중입니다."
        self.equipment[self.job.equipment] += 1
        self.job = None
        return True, "완성된 장비 1개를 회수했습니다."
