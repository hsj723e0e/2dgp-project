import random
import unittest

from game_state import GameState, PERSONAL_IDS, rental_success_probability
from orders import Order


class EquipmentUnitTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.state = GameState(clock=lambda: self.now, rng=random.Random(1))

    def test_count_only_inventory_and_specific_unit_sale(self):
        self.state.equipment["eq_drill_01"] = 2
        first, second = self.state.available_units("eq_drill_01")
        self.assertNotEqual(first.identifier, second.identifier)
        second.level = 3
        self.state.current_order = Order(30, "npc_novice", (("eq_drill_01", 1),))
        self.assertTrue(self.state.sell_order(30, (first.identifier,))[0])
        self.assertEqual(self.state.available_units("eq_drill_01"), (second,))
        self.assertEqual(second.level, 3)

    def test_rental_returns_the_same_unit_and_level(self):
        self.state.equipment["eq_drill_01"] = 1
        unit = self.state.available_units("eq_drill_01")[0]
        unit.level = 4
        self.state.current_order = Order(31, "npc_novice", (("eq_drill_01", 1),))
        self.assertTrue(self.state.start_rental(31, (unit.identifier,))[0])
        self.state.rng.random = lambda: 0
        self.now = 25
        self.state.update_rentals()
        self.assertIs(self.state.available_units("eq_drill_01")[0], unit)
        self.assertEqual(unit.level, 4)

    def test_duplicate_or_wrong_unit_selection_keeps_inventory(self):
        self.state.equipment["eq_drill_01"] = 2
        unit = self.state.available_units("eq_drill_01")[0]
        self.state.current_order = Order(32, "npc_novice", (("eq_drill_01", 2),))
        for identifiers in ((unit.identifier, unit.identifier), (9999, 9998)):
            self.assertFalse(self.state.sell_order(32, identifiers)[0])
            self.assertEqual(self.state.equipment["eq_drill_01"], 2)
            self.assertEqual(self.state.coins, 100)

    def test_upgrade_charges_coins_and_changes_only_selected_unit(self):
        self.state.equipment["eq_drill_01"] = 2
        first, second = self.state.available_units("eq_drill_01")
        self.assertTrue(self.state.enhance_basic("eq_drill_01", second.identifier)[0])
        self.assertEqual(self.state.coins, 92)
        self.assertEqual((first.level, second.level), (0, 1))
        self.assertTrue(self.state.enhance_basic("eq_drill_01", second.identifier)[0])
        self.assertEqual(self.state.coins, 76)
        self.assertEqual(second.level, 2)

    def test_upgrade_rejects_missing_unit_low_funds_and_max_level(self):
        self.state.equipment["eq_drill_01"] = 1
        unit = self.state.available_units("eq_drill_01")[0]
        self.state.coins = 0
        self.assertFalse(self.state.enhance_basic("eq_drill_01", unit.identifier)[0])
        self.assertEqual(unit.level, 0)
        self.state.coins = 999
        unit.level = 13
        self.assertFalse(self.state.enhance_basic("eq_drill_01", unit.identifier)[0])
        self.assertFalse(self.state.enhance_basic("eq_drill_01", 9999)[0])
        self.assertEqual(self.state.coins, 999)

    def test_rental_uses_selected_average_level_and_freezes_probability(self):
        self.state.equipment["eq_drill_01"] = 2
        first, second = self.state.available_units("eq_drill_01")
        second.level = 4
        self.state.current_order = Order(41, "npc_novice", (("eq_drill_01", 2),))
        self.assertTrue(self.state.start_rental(41, (first.identifier, second.identifier))[0])
        contract = self.state.rentals[-1]
        self.assertAlmostEqual(contract.success_probability, .87)
        second.level = 13
        self.assertAlmostEqual(contract.success_probability, .87)
        self.assertAlmostEqual(rental_success_probability((second,)), .98)


class PersonalEquipmentTests(unittest.TestCase):
    def test_each_personal_type_uses_twelve_cores_and_stays_separate_from_stock(self):
        state = GameState()
        state.rewards["item_core"] = 36
        for equipment in PERSONAL_IDS:
            self.assertTrue(state.craft_personal(equipment)[0])
            self.assertEqual(state.personal_equipment[equipment], 0)
            self.assertNotIn(equipment, state.equipment)
        self.assertEqual(state.rewards["item_core"], 0)
        self.assertEqual(sum(state.equipment.values()), 0)

    def test_missing_cores_duplicate_and_unknown_personal_craft_are_atomic(self):
        state = GameState()
        state.rewards["item_core"] = 11
        self.assertFalse(state.craft_personal(PERSONAL_IDS[0])[0])
        self.assertEqual(state.rewards["item_core"], 11)
        state.rewards["item_core"] = 24
        self.assertTrue(state.craft_personal(PERSONAL_IDS[0])[0])
        self.assertFalse(state.craft_personal(PERSONAL_IDS[0])[0])
        self.assertFalse(state.craft_personal("eq_drill_01")[0])
        self.assertEqual(state.rewards["item_core"], 12)

    def test_personal_upgrade_uses_three_chips_and_stops_at_thirteen(self):
        state = GameState()
        state.rewards["item_core"] = 12
        state.rewards["item_chip"] = 39
        equipment = PERSONAL_IDS[0]
        state.craft_personal(equipment)
        for level in range(1, 14):
            self.assertTrue(state.enhance_personal(equipment)[0])
            self.assertEqual(state.personal_equipment[equipment], level)
        self.assertEqual(state.personal_performance(equipment), 230)
        self.assertEqual(state.rewards["item_chip"], 0)
        state.rewards["item_chip"] = 3
        self.assertFalse(state.enhance_personal(equipment)[0])
        self.assertEqual(state.rewards["item_chip"], 3)

    def test_personal_upgrade_cannot_use_coins_or_unowned_equipment(self):
        state = GameState()
        state.coins = 999
        self.assertFalse(state.enhance_personal(PERSONAL_IDS[0])[0])
        state.rewards["item_core"] = 12
        state.craft_personal(PERSONAL_IDS[0])
        self.assertFalse(state.enhance_personal(PERSONAL_IDS[0])[0])
        self.assertEqual(state.personal_equipment[PERSONAL_IDS[0]], 0)
        self.assertEqual(state.coins, 999)
