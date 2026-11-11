"""Session currency, inventory, and the workbench's single crafting job."""

from dataclasses import dataclass
from time import monotonic

from workshop import EQUIPMENT


MATERIAL_PRICES = {"mat_01": 8, "mat_02": 12, "mat_03": 4}


@dataclass(frozen=True)
class Recipe:
    ingredients: dict
    seconds: float


RECIPES = {
    "eq_drill_01": Recipe({"mat_01": 2, "mat_03": 1}, 10),
    "eq_suit_01": Recipe({"mat_01": 3, "mat_03": 2}, 12),
    "eq_oxygen_01": Recipe({"mat_01": 2, "mat_03": 2}, 10),
}


@dataclass(frozen=True)
class CraftJob:
    equipment: str
    ready_at: float


class GameState:
    def __init__(self, clock=monotonic):
        self.coins = 100
        self.materials = {name: 0 for name in MATERIAL_PRICES}
        self.equipment = {entry.image: 0 for entry in EQUIPMENT}
        self.job = None
        self.clock = clock

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
