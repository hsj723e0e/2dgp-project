import random
import unittest

from game_state import GameState
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
