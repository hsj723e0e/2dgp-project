import unittest
from types import SimpleNamespace

import sdl2

from customer_board import CustomerBoard, RENTAL_INVENTORY_ORIGIN
from game_state import GameState
from inventory_panel import slot_bounds
from orders import Order


class RentalInventorySelectionTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState()
        self.game = SimpleNamespace(state=self.state, feedback="", feedback_success=True)
        self.board = CustomerBoard(self.game)

    def click_unit(self, identifier):
        index = next(index for index, item in enumerate(self.state.inventory_items())
                     if item.unit_id == identifier)
        left, bottom, right, top = slot_bounds(RENTAL_INVENTORY_ORIGIN, index, 3)
        self.board.handle_click((left + right) / 2, (bottom + top) / 2)

    def test_complete_click_selection_starts_rental_of_exact_units_without_confirmation(self):
        self.state.add_equipment("eq_suit_01", 3)
        self.state.add_equipment("eq_drill_01", 1)
        first, second, third = self.state.available_units("eq_suit_01")
        third.level = 4
        unrelated = self.state.available_units("eq_drill_01")[0]
        self.state.current_order = Order(60, "npc_novice", (("eq_suit_01", 2),))
        self.board.rent()
        self.assertEqual(self.board.chosen_units, [])
        self.click_unit(unrelated.identifier)
        self.assertEqual(self.board.chosen_units, [])
        self.click_unit(first.identifier)
        self.assertFalse(self.state.rentals)
        self.board.handle_key(sdl2.SDLK_RETURN)
        self.assertFalse(self.state.rentals)
        self.click_unit(first.identifier)
        self.assertFalse(self.board.chosen_units)
        self.click_unit(second.identifier)
        self.click_unit(third.identifier)
        self.assertIsNone(self.board.unit_action)
        self.assertIsNone(self.state.current_order)
        self.assertEqual(len(self.state.rentals), 1)
        self.assertEqual(self.state.rentals[0].units, (second, third))
        self.assertAlmostEqual(self.state.rentals[0].success_probability, .87)
        self.assertEqual(self.state.available_units("eq_suit_01"), (first,))

    def test_per_type_quota_blocks_extra_items_until_other_requested_type_is_selected(self):
        self.state.add_equipment("eq_drill_01", 2)
        self.state.add_equipment("eq_suit_01", 1)
        first, extra = self.state.available_units("eq_drill_01")
        suit = self.state.available_units("eq_suit_01")[0]
        self.state.current_order = Order(61, "npc_novice", (("eq_drill_01", 1), ("eq_suit_01", 1)))
        self.board.rent()
        self.click_unit(first.identifier)
        self.click_unit(extra.identifier)
        self.assertEqual(self.board.chosen_units, [first.identifier])
        self.assertFalse(self.state.rentals)
        self.click_unit(suit.identifier)
        self.assertEqual(self.state.rentals[0].units, (first, suit))

    def test_missing_inventory_blocks_selection_and_escape_cancels_without_consumption(self):
        self.state.current_order = Order(62, "npc_novice", (("eq_suit_01", 2),))
        self.state.add_equipment("eq_suit_01", 1)
        self.board.rent()
        self.assertIsNone(self.board.unit_action)
        self.state.add_equipment("eq_suit_01", 1)
        first = self.state.available_units("eq_suit_01")[0]
        self.board.rent()
        self.click_unit(first.identifier)
        self.board.handle_key(sdl2.SDLK_ESCAPE)
        self.assertIsNone(self.board.unit_action)
        self.assertEqual(self.state.equipment["eq_suit_01"], 2)
        self.assertFalse(self.state.rentals)

    def test_sale_still_uses_explicit_confirmation(self):
        self.state.add_equipment("eq_drill_01", 1)
        self.state.current_order = Order(63, "npc_novice", (("eq_drill_01", 1),))
        self.board.sell()
        self.assertEqual(self.board.unit_action, "sell")
        self.assertEqual(self.state.coins, 100)
        self.board.confirm_selection()
        self.assertEqual(self.state.coins, 132)
        self.assertIsNone(self.state.current_order)


if __name__ == "__main__":
    unittest.main()
