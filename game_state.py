"""Session currency, inventory, and the workbench's single crafting job."""

from dataclasses import dataclass
from collections import Counter
from math import isfinite
import random
from time import monotonic

from orders import (
    CUSTOMER_NAMES, INFORMATION_PRICE, MARKET_EVENTS, MARKET_INTERVAL,
    RENTAL_DURATIONS, RENTAL_SUCCESS_RATE, SALE_PRICES, RentalContract, create_order,
)
from workshop import EQUIPMENT, PERSONAL_EQUIPMENT


MATERIAL_PRICES = {"mat_01": 8, "mat_02": 12, "mat_03": 4}
CUSTOMER_INTERVAL = 8
MAX_ENHANCEMENT = 13
PERSONAL_CORE_COST = 12
PERSONAL_CHIP_COST = 3
PERSONAL_IDS = tuple(entry.image for entry in PERSONAL_EQUIPMENT[:3])
SESSION_DURATION = 20 * 60
INVENTORY_CAPACITY = 9
CHEST_CAPACITY = 28


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


@dataclass
class EquipmentUnit:
    identifier: int
    equipment: str
    level: int = 0


@dataclass(frozen=True)
class InventoryItem:
    image: str
    quantity: int = 1
    level: int | None = None
    unit_id: int | None = None


@dataclass(frozen=True)
class SessionResult:
    personal_levels: tuple
    coins: int
    sold_orders: int
    rental_successes: int
    rental_losses: int
    pending_rentals: int
    collected_equipment: int


def basic_upgrade_cost(unit):
    base_cost = 8 if unit.equipment.endswith("_01") else 12
    return base_cost * (unit.level + 1)


def rental_success_probability(units):
    average_level = sum(unit.level for unit in units) / len(units) if units else 0
    return min(0.98, RENTAL_SUCCESS_RATE + average_level * 0.01)


class GameState:
    def __init__(self, clock=monotonic, rng=None, session_duration=SESSION_DURATION):
        if not isfinite(session_duration) or session_duration <= 0:
            raise ValueError("Session duration must be a positive finite number")
        self.coins = 100
        self.materials = {name: 0 for name in MATERIAL_PRICES}
        self.equipment = {entry.image: 0 for entry in EQUIPMENT}
        self.equipment_units = {entry.image: [] for entry in EQUIPMENT}
        self.storage_units = {entry.image: [] for entry in EQUIPMENT}
        self.next_unit_id = 1
        self.job = None
        self.staged_equipment = None
        self.staged_materials = {}
        self.clock = clock
        self.rng = rng if rng is not None else random.Random()
        self.session_started_at = self.clock()
        self.session_end_at = self.session_started_at + session_duration
        self.market_tip = None
        self.market_tip_period = None
        self.rewards = {"item_chip": 0, "item_core": 0, "item_secret": 0}
        self.personal_equipment = {equipment: None for equipment in PERSONAL_IDS}
        self.rentals = []
        self.current_order = create_order(1, "npc_novice", self.rng)
        self.next_order_id = 2
        self.next_customer_at = None
        self.result = None
        self.sold_order_count = 0
        self.collected_equipment_count = 0

    @property
    def session_remaining(self):
        return max(0.0, self.session_end_at - self.clock())

    @property
    def session_over(self):
        return self.result is not None or self.clock() >= self.session_end_at

    @property
    def effective_time(self):
        return min(self.clock(), self.session_end_at)

    def finish_session(self):
        if self.result is None and self.session_over:
            self.clear_craft_materials()
            self.update_crafting()
            self.update_rentals()
            self.result = SessionResult(
                personal_levels=tuple(self.personal_equipment.items()),
                coins=self.coins,
                sold_orders=self.sold_order_count,
                rental_successes=sum(contract.status == "success" for contract in self.rentals),
                rental_losses=sum(contract.status == "lost" for contract in self.rentals),
                pending_rentals=sum(contract.status in ("active", "returning") for contract in self.rentals),
                collected_equipment=self.collected_equipment_count,
            )
        return self.result

    def apply_cheat(self):
        if self.session_over:
            return
        self.coins = 999
        for material in MATERIAL_PRICES:
            if self.materials[material] > 0 or material in self.staged_materials or self.inventory_free > 0:
                self.materials[material] = 999

    @property
    def inventory_used(self):
        material_slots = sum(quantity > 0 or self.staged_materials.get(image, 0) > 0
                             for image, quantity in self.materials.items())
        return (material_slots + sum(quantity > 0 for quantity in self.rewards.values())
                + sum(self.equipment.values())
                + sum(level is not None for level in self.personal_equipment.values()))

    @property
    def inventory_free(self):
        # Staged ingredients retain their space until crafting starts, so cancellation always fits.
        return max(0, INVENTORY_CAPACITY - self.inventory_used)

    def inventory_items(self):
        items = []
        for image, quantity in self.materials.items():
            if quantity > 0:
                items.append(InventoryItem(image, quantity))
        for image in self.equipment:
            items.extend(InventoryItem(image, level=unit.level, unit_id=unit.identifier)
                         for unit in self.available_units(image))
        for image, quantity in self.rewards.items():
            if quantity > 0:
                items.append(InventoryItem(image, quantity))
        for image, level in self.personal_equipment.items():
            if level is not None:
                items.append(InventoryItem(image, level=level))
        return tuple(items)

    def chest_items(self, equipment):
        return tuple(InventoryItem(unit.equipment, level=unit.level, unit_id=unit.identifier)
                     for unit in self.storage_units[equipment])

    def store_equipment(self, equipment, unit_id):
        if self.session_over:
            return False, "운영 시간이 종료되었습니다."
        if equipment not in self.storage_units:
            return False, "존재하지 않는 보관함입니다."
        unit = next((unit for unit in self.available_units(equipment)
                     if unit.identifier == unit_id), None)
        if unit is None:
            return False, "선택한 종류의 장비만 보관할 수 있습니다."
        if len(self.storage_units[equipment]) >= CHEST_CAPACITY:
            return False, "보관함 28칸이 가득 찼습니다."
        self.take_units((unit,))
        self.storage_units[equipment].append(unit)
        return True, "장비를 보관했습니다."

    def withdraw_equipment(self, equipment, unit_id):
        if self.session_over:
            return False, "운영 시간이 종료되었습니다."
        if equipment not in self.storage_units:
            return False, "존재하지 않는 보관함입니다."
        unit = next((unit for unit in self.storage_units[equipment]
                     if unit.identifier == unit_id), None)
        if unit is None:
            return False, "꺼낼 장비가 없습니다."
        if not self.return_units((unit,)):
            return False, "가방 9칸이 가득 찼습니다."
        self.storage_units[equipment].remove(unit)
        return True, "장비를 가방으로 옮겼습니다."

    def new_equipment_unit(self, equipment):
        unit = EquipmentUnit(self.next_unit_id, equipment)
        self.next_unit_id += 1
        return unit

    def available_units(self, equipment):
        units = self.equipment_units[equipment]
        count = self.equipment[equipment]
        # Count-only inventories created by earlier callers become +0 units.
        while len(units) < count:
            units.append(self.new_equipment_unit(equipment))
        del units[count:]
        return tuple(units)

    def add_equipment(self, equipment, quantity):
        if equipment not in self.equipment or type(quantity) is not int or quantity < 0:
            return False
        if quantity > self.inventory_free:
            return False
        self.available_units(equipment)
        self.equipment[equipment] += quantity
        self.available_units(equipment)
        return True

    def order_units(self, order, unit_ids=None):
        available = {}
        defaults = []
        for equipment, quantity in order.requirements:
            units = self.available_units(equipment)
            available.update((unit.identifier, unit) for unit in units)
            defaults.extend(units[:quantity])
        if unit_ids is None:
            return tuple(defaults)
        if len(unit_ids) != order.quantity or len(set(unit_ids)) != len(unit_ids):
            raise ValueError("요청 수량에 맞게 서로 다른 장비를 선택하세요.")
        if any(identifier not in available for identifier in unit_ids):
            raise ValueError("선택한 장비를 현재 사용할 수 없습니다.")
        units = tuple(available[identifier] for identifier in unit_ids)
        if Counter(unit.equipment for unit in units) != Counter(dict(order.requirements)):
            raise ValueError("주문에서 요구한 종류의 장비를 선택하세요.")
        return units

    def take_units(self, units):
        for unit in units:
            self.equipment_units[unit.equipment].remove(unit)
            self.equipment[unit.equipment] -= 1

    def return_units(self, units):
        if len(units) > self.inventory_free:
            return False
        for unit in units:
            self.available_units(unit.equipment)
            self.equipment_units[unit.equipment].append(unit)
            self.equipment[unit.equipment] += 1
        return True

    def basic_upgrade_status(self, equipment, unit_id):
        if self.session_over:
            return False, "운영 시간이 종료되었습니다."
        if equipment not in self.equipment:
            return False, "강화할 수 없는 장비입니다."
        unit = next((item for item in self.available_units(equipment) if item.identifier == unit_id), None)
        if unit is None:
            return False, "강화할 보유 장비를 선택하세요."
        if unit.level >= MAX_ENHANCEMENT:
            return False, "최대 강화 단계입니다."
        if self.coins < basic_upgrade_cost(unit):
            return False, "코인이 부족합니다."
        return True, ""

    def enhance_basic(self, equipment, unit_id):
        available, reason = self.basic_upgrade_status(equipment, unit_id)
        if not available:
            return False, reason
        unit = next(item for item in self.available_units(equipment) if item.identifier == unit_id)
        self.coins -= basic_upgrade_cost(unit)
        unit.level += 1
        return True, f"선택한 장비를 +{unit.level}로 강화했습니다."

    def personal_craft_status(self, equipment):
        if self.session_over:
            return False, "운영 시간이 종료되었습니다."
        if equipment not in self.personal_equipment:
            return False, "제작할 수 없는 개인 장비입니다."
        if self.personal_equipment[equipment] is not None:
            return False, "이미 보유한 개인 장비입니다."
        if self.rewards["item_core"] < PERSONAL_CORE_COST:
            return False, "고출력 코어가 부족합니다."
        if self.inventory_free == 0 and self.rewards["item_core"] > PERSONAL_CORE_COST:
            return False, "개인 장비를 넣을 가방 공간이 부족합니다."
        return True, ""

    def craft_personal(self, equipment):
        available, reason = self.personal_craft_status(equipment)
        if not available:
            return False, reason
        self.rewards["item_core"] -= PERSONAL_CORE_COST
        self.personal_equipment[equipment] = 0
        return True, "개인 최상급 장비를 제작했습니다."

    def personal_upgrade_status(self, equipment):
        if self.session_over:
            return False, "운영 시간이 종료되었습니다."
        if equipment not in self.personal_equipment or self.personal_equipment[equipment] is None:
            return False, "먼저 개인 장비를 제작하세요."
        if self.personal_equipment[equipment] >= MAX_ENHANCEMENT:
            return False, "최대 강화 +13에 도달했습니다."
        if self.rewards["item_chip"] < PERSONAL_CHIP_COST:
            return False, "정밀제어칩이 부족합니다."
        return True, ""

    def enhance_personal(self, equipment):
        available, reason = self.personal_upgrade_status(equipment)
        if not available:
            return False, reason
        self.rewards["item_chip"] -= PERSONAL_CHIP_COST
        self.personal_equipment[equipment] += 1
        return True, f"개인 장비를 +{self.personal_equipment[equipment]}로 강화했습니다."

    def personal_performance(self, equipment):
        level = self.personal_equipment[equipment]
        return None if level is None else 100 + level * 10

    @property
    def next_customer_in(self):
        if self.current_order is not None or self.next_customer_at is None:
            return 0.0
        return max(0.0, self.next_customer_at - self.clock())

    def update_customers(self):
        if self.session_over:
            return
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
        if self.session_over:
            return False, "운영 시간이 종료되었습니다."
        if self.current_order is None or self.current_order.identifier != order_id:
            return False, "이미 처리된 주문입니다."
        self.finish_order()
        return True, "주문을 거절했습니다. 다음 손님을 기다려 주세요."

    @property
    def market_period(self):
        return int(max(0, self.effective_time - self.session_started_at) // MARKET_INTERVAL)

    @property
    def market_event(self):
        period = self.market_period
        return MARKET_EVENTS[(period - 1) % len(MARKET_EVENTS)] if period else None

    @property
    def next_market_event(self):
        return MARKET_EVENTS[self.market_period % len(MARKET_EVENTS)]

    @property
    def market_remaining(self):
        elapsed = max(0, self.effective_time - self.session_started_at)
        return MARKET_INTERVAL - elapsed % MARKET_INTERVAL

    @property
    def known_next_event(self):
        if self.market_tip_period == self.market_period + 1:
            return self.market_tip
        return None

    def sale_value(self, order):
        event = self.market_event
        total = 0
        for equipment, quantity in order.requirements:
            price = SALE_PRICES[equipment]
            if event is not None and equipment in event.equipment:
                price = price * 125 // 100
            total += price * quantity
        return total

    def order_status(self, order_id, unit_ids=None):
        if self.session_over:
            return False, "운영 시간이 종료되었습니다."
        order = self.current_order
        if order is None or order.identifier != order_id:
            return False, "이미 처리된 주문입니다."
        if order.customer == "npc_broker":
            return False, "정보상에게는 코인으로 정보를 구매하세요."
        if any(name not in self.equipment for name, _ in order.requirements):
            return False, "거래할 수 없는 장비가 포함되어 있습니다."
        if any(self.equipment[name] < quantity for name, quantity in order.requirements):
            return False, "장비 재고가 부족합니다."
        if unit_ids is not None:
            try:
                self.order_units(order, unit_ids)
            except ValueError as error:
                return False, str(error)
        return True, ""

    def sell_order(self, order_id, unit_ids=None):
        available, reason = self.order_status(order_id, unit_ids)
        if not available:
            return False, reason
        order = self.current_order
        coins = self.sale_value(order)
        self.take_units(self.order_units(order, unit_ids))
        self.coins += coins
        self.sold_order_count += 1
        self.finish_order()
        return True, f"판매 완료 · {coins} 코인을 받았습니다."

    def information_status(self, order_id):
        if self.session_over:
            return False, "운영 시간이 종료되었습니다."
        order = self.current_order
        if order is None or order.identifier != order_id:
            return False, "이미 처리된 주문입니다."
        if order.customer != "npc_broker":
            return False, "정보상에게서 정보를 구매할 수 있습니다."
        if self.coins < INFORMATION_PRICE:
            return False, "코인이 부족합니다."
        return True, ""

    def buy_information(self, order_id):
        available, reason = self.information_status(order_id)
        if not available:
            return False, reason
        period = self.market_period
        tip = MARKET_EVENTS[period % len(MARKET_EVENTS)].name
        self.coins -= INFORMATION_PRICE
        self.market_tip = tip
        self.market_tip_period = period + 1
        self.finish_order()
        return True, f"{INFORMATION_PRICE} 코인으로 시장 정보를 구매했습니다."

    def rental_reward(self, order):
        if order.customer == "npc_novice":
            return "item_chip", order.quantity
        if order.customer == "npc_expert":
            return "item_core", order.quantity
        if order.customer == "npc_tourist":
            return "coins", max(1, self.sale_value(order) * 60 // 100)
        if order.customer == "npc_mysterious":
            return "item_secret", 1
        raise ValueError("The information broker has no rental contract")

    def start_rental(self, order_id, unit_ids=None):
        available, reason = self.order_status(order_id, unit_ids)
        if not available:
            return False, reason
        order = self.current_order
        reward_item, reward_amount = self.rental_reward(order)
        units = self.order_units(order, unit_ids)
        contract = RentalContract(
            order=order,
            due_at=self.clock() + RENTAL_DURATIONS[order.customer],
            success_probability=rental_success_probability(units),
            reward_item=reward_item,
            reward_amount=reward_amount,
            units=units,
        )
        self.take_units(units)
        self.rentals.append(contract)
        self.finish_order()
        return True, "대여를 시작했습니다. 대여 현황에서 결과를 확인하세요."

    def update_rentals(self):
        if self.result is not None:
            return
        now = self.effective_time
        for contract in self.rentals:
            if contract.status == "active" and now >= contract.due_at:
                if self.rng.random() >= contract.success_probability:
                    contract.status = "lost"
                    continue
                contract.status = "returning"
                if not contract.units:
                    contract.units = tuple(self.new_equipment_unit(equipment)
                                           for equipment, quantity in contract.order.requirements
                                           for _ in range(quantity))
            if contract.status != "returning":
                continue
            count = min(self.inventory_free, len(contract.units) - contract.returned_count)
            units = contract.units[contract.returned_count:contract.returned_count + count]
            self.return_units(units)
            contract.returned_count += count
            if contract.returned_count < len(contract.units):
                continue
            remaining_reward = contract.reward_amount - contract.received_reward
            if contract.reward_item == "coins":
                self.coins += remaining_reward
                contract.received_reward += remaining_reward
            else:
                if self.rewards[contract.reward_item] > 0 or self.inventory_free > 0:
                    self.rewards[contract.reward_item] += remaining_reward
                    contract.received_reward += remaining_reward
            if contract.received_reward == contract.reward_amount:
                contract.status = "success"

    def purchase_status(self, material, quantity):
        if self.session_over:
            return False, "운영 시간이 종료되었습니다."
        if material not in MATERIAL_PRICES:
            return False, "구매할 수 없는 재료입니다."
        if type(quantity) is not int or quantity < 1:
            return False, "구매 수량은 1개 이상이어야 합니다."
        cost = MATERIAL_PRICES[material] * quantity
        if self.coins < cost:
            return False, "코인이 부족합니다."
        if self.materials[material] == 0 and material not in self.staged_materials and self.inventory_free == 0:
            return False, "가방의 빈칸이 부족합니다."
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

    def stage_craft_material(self, equipment, material):
        if self.session_over:
            return False, "운영 시간이 종료되었습니다."
        if self.job is not None:
            return False, "작업대에서 장비를 제작 중입니다."
        if equipment not in RECIPES or material not in RECIPES[equipment].ingredients:
            return False, "해당 장비에 필요한 재료가 아닙니다."
        if self.staged_equipment not in (None, equipment):
            return False, "기존 조합 재료를 먼저 반환하세요."
        if material in self.staged_materials:
            return True, ""
        required = RECIPES[equipment].ingredients[material]
        if self.materials[material] < required:
            return False, "재료가 부족합니다."
        self.materials[material] -= required
        self.staged_equipment = equipment
        self.staged_materials[material] = required
        return True, ""

    def unstage_craft_material(self, material):
        quantity = self.staged_materials.pop(material, 0)
        if quantity:
            self.materials[material] += quantity
        if not self.staged_materials:
            self.staged_equipment = None

    def clear_craft_materials(self):
        for material in tuple(self.staged_materials):
            self.unstage_craft_material(material)

    def craft_status(self, equipment):
        if self.session_over:
            return False, "운영 시간이 종료되었습니다."
        if equipment not in RECIPES:
            return False, "제작할 수 없는 장비입니다."
        if self.job is not None:
            if self.ready_to_collect:
                return False, "가방을 비우면 완성품이 자동으로 회수됩니다."
            return False, "작업대에서 장비를 제작 중입니다."
        ingredients = RECIPES[equipment].ingredients
        staged = self.staged_materials if self.staged_equipment == equipment else {}
        if any(self.materials[name] + staged.get(name, 0) < quantity
               for name, quantity in ingredients.items()):
            return False, "재료가 부족합니다."
        return True, ""

    def start_craft(self, equipment):
        available, reason = self.craft_status(equipment)
        if not available:
            return False, reason
        recipe = RECIPES[equipment]
        ready_at = self.clock() + recipe.seconds
        if self.staged_equipment != equipment:
            self.clear_craft_materials()
        for name, quantity in recipe.ingredients.items():
            self.materials[name] -= quantity - self.staged_materials.get(name, 0)
        self.staged_materials.clear()
        self.staged_equipment = None
        self.job = CraftJob(equipment, ready_at)
        return True, "제작을 시작했습니다. 완성품은 자동으로 회수됩니다."

    def collect(self):
        if self.session_over:
            return False, "운영 시간이 종료되었습니다."
        if self.job is None:
            return False, "회수할 완성품이 없습니다."
        if not self.ready_to_collect:
            return False, "아직 제작 중입니다."
        if self.update_crafting() is None:
            return False, "가방이 가득 찼습니다. 빈칸이 생기면 자동 회수됩니다."
        return True, "완성된 장비 1개를 회수했습니다."

    def update_crafting(self):
        """Settle a completed job once, including completions at the session deadline."""
        if self.result is not None or self.job is None:
            return None
        if self.job.ready_at > self.effective_time:
            return None
        equipment = self.job.equipment
        if not self.add_equipment(equipment, 1):
            return None
        self.collected_equipment_count += 1
        self.job = None
        return equipment
