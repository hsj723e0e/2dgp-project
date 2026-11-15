import random
import unittest

from game_state import GameState, RECIPES, basic_upgrade_cost
from orders import ADVANCED_EQUIPMENT, Order, create_order


class AdvancedEquipmentTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.state = GameState(clock=lambda: self.now, rng=random.Random(1))

    def test_each_recipe_stages_chip_and_completes_once(self):
        for equipment in ADVANCED_EQUIPMENT:
            with self.subTest(equipment=equipment):
                recipe = RECIPES[equipment]
                self.state.materials.update(mat_02=20, mat_03=20)
                self.state.rewards['item_chip'] = 2
                for image, quantity in recipe.ingredients.items():
                    before = self.state.resource_inventory(image)[image]
                    self.assertTrue(self.state.stage_craft_material(equipment, image)[0])
                    self.assertEqual(self.state.resource_inventory(image)[image], before - quantity)
                self.assertTrue(self.state.start_craft(equipment)[0])
                self.assertEqual(self.state.rewards['item_chip'], 1)
                self.now += recipe.seconds
                self.assertEqual(self.state.update_crafting(), equipment)
                self.assertIsNone(self.state.update_crafting())
                self.assertEqual(self.state.equipment[equipment], 1)

    def test_staged_chip_reserves_slot_and_cancel_refunds_into_full_bag(self):
        self.state.materials.update(mat_02=4, mat_03=3)
        self.state.rewards['item_chip'] = 1
        self.state.add_equipment('eq_drill_01', 6)
        self.assertTrue(self.state.stage_craft_material('eq_drill_advanced', 'item_chip')[0])
        self.assertEqual(self.state.inventory_free, 0)
        self.assertEqual(self.state.rewards['item_chip'], 0)
        self.assertFalse(self.state.add_equipment('eq_suit_advanced', 1))
        self.state.clear_craft_materials()
        self.assertEqual(self.state.rewards['item_chip'], 1)
        self.assertEqual(self.state.inventory_used, 9)

    def test_missing_chip_keeps_all_ingredients(self):
        self.state.materials.update(mat_02=20, mat_03=20)
        before = self.state.materials.copy()
        self.assertFalse(self.state.start_craft('eq_drill_advanced')[0])
        self.assertEqual(self.state.materials, before)
        self.assertIsNone(self.state.job)

    def test_each_chest_preserves_unit_and_individual_upgrade(self):
        for equipment in ADVANCED_EQUIPMENT:
            self.state.add_equipment(equipment, 1)
            unit = self.state.available_units(equipment)[0]
            self.assertEqual(basic_upgrade_cost(unit), 18)
            self.state.coins = 999
            self.assertTrue(self.state.enhance_basic(equipment, unit.identifier)[0])
            self.assertEqual(unit.level, 1)
            self.assertEqual(basic_upgrade_cost(unit), 36)
            self.assertTrue(self.state.store_equipment(equipment, unit.identifier)[0])
            self.assertIs(self.state.storage_units[equipment][0], unit)
            self.assertTrue(self.state.withdraw_equipment(equipment, unit.identifier)[0])
            self.assertIs(self.state.available_units(equipment)[0], unit)
            self.assertEqual(unit.level, 1)

    def test_sales_and_rentals_accept_all_advanced_items(self):
        requirements = tuple((image, 1) for image in ADVANCED_EQUIPMENT)
        for image in ADVANCED_EQUIPMENT:
            self.state.add_equipment(image, 1)
        self.state.current_order = Order(90, 'npc_expert', requirements)
        value = self.state.sale_value(self.state.current_order)
        self.assertTrue(self.state.sell_order(90)[0])
        self.assertEqual(self.state.coins, 100 + value)
        for image in ADVANCED_EQUIPMENT:
            self.state.add_equipment(image, 1)
        units = tuple(self.state.available_units(image)[0] for image in ADVANCED_EQUIPMENT)
        self.state.current_order = Order(91, 'npc_expert', requirements)
        self.assertTrue(self.state.start_rental(91, tuple(unit.identifier for unit in units))[0])
        self.state.rng.random = lambda: 0
        self.now = 30
        self.state.update_rentals()
        for unit in units:
            self.assertIs(self.state.available_units(unit.equipment)[0], unit)

    def test_all_three_customer_pools_can_request_each_advanced_item(self):
        for customer in ('npc_expert', 'npc_tourist', 'npc_mysterious'):
            rng = random.Random(71)
            seen = set()
            for identifier in range(200):
                seen.update(image for image, _ in create_order(identifier, customer, rng).requirements)
            self.assertTrue(set(ADVANCED_EQUIPMENT) <= seen)
