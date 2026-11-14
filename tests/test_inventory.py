import unittest
from unittest.mock import Mock

from game_state import GameState, PERSONAL_IDS
from orders import Order


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.state = GameState(clock=lambda: self.now)

    def test_materials_and_rewards_stack_but_each_equipment_has_its_own_slot(self):
        self.state.materials["mat_01"] = 999
        self.state.rewards["item_core"] = 12
        self.state.add_equipment("eq_drill_01", 2)
        items = self.state.inventory_items()
        self.assertEqual(len(items), 4)
        self.assertEqual(self.state.inventory_free, 5)
        drills = [item for item in items if item.image == "eq_drill_01"]
        self.assertEqual(len({item.unit_id for item in drills}), 2)
        self.assertEqual(items[0].quantity, 999)

    def test_full_bag_rejects_new_material_but_accepts_existing_stack(self):
        self.state.materials["mat_01"] = 1
        self.state.add_equipment("eq_drill_01", 8)
        before = self.state.coins
        self.assertFalse(self.state.purchase("mat_03", 1)[0])
        self.assertEqual(self.state.coins, before)
        self.assertTrue(self.state.purchase("mat_01", 2)[0])
        self.assertEqual(self.state.materials["mat_01"], 3)
        self.assertEqual(len(self.state.inventory_items()), 9)

    def test_storage_preserves_identity_level_and_excludes_stored_items_from_orders(self):
        self.state.add_equipment("eq_drill_01", 1)
        unit = self.state.available_units("eq_drill_01")[0]
        unit.level = 7
        self.assertFalse(self.state.store_equipment("eq_suit_01", unit.identifier)[0])
        self.assertEqual(self.state.equipment["eq_drill_01"], 1)
        self.assertTrue(self.state.store_equipment("eq_drill_01", unit.identifier)[0])
        self.state.current_order = Order(50, "npc_novice", (("eq_drill_01", 1),))
        self.assertFalse(self.state.sell_order(50)[0])
        self.assertFalse(self.state.start_rental(50)[0])
        self.assertTrue(self.state.withdraw_equipment("eq_drill_01", unit.identifier)[0])
        self.assertIs(self.state.available_units("eq_drill_01")[0], unit)
        self.assertEqual(unit.level, 7)
        self.assertTrue(self.state.sell_order(50, (unit.identifier,))[0])

    def test_chest_capacity_and_full_bag_failures_keep_equipment_in_place(self):
        for _ in range(28):
            self.state.add_equipment("eq_drill_01", 1)
            unit = self.state.available_units("eq_drill_01")[0]
            self.assertTrue(self.state.store_equipment("eq_drill_01", unit.identifier)[0])
        self.state.add_equipment("eq_drill_01", 9)
        unit = self.state.available_units("eq_drill_01")[0]
        stored = self.state.storage_units["eq_drill_01"][0]
        self.assertFalse(self.state.store_equipment("eq_drill_01", unit.identifier)[0])
        self.assertFalse(self.state.withdraw_equipment("eq_drill_01", stored.identifier)[0])
        self.assertEqual(len(self.state.chest_items("eq_drill_01")), 28)
        self.assertEqual(self.state.equipment["eq_drill_01"], 9)

    def test_finished_craft_waits_and_enters_bag_once_a_slot_is_freed(self):
        self.state.materials.update(mat_01=2, mat_03=1)
        self.state.start_craft("eq_drill_01")
        self.state.add_equipment("eq_suit_01", 9)
        self.now = 10
        self.assertIsNone(self.state.update_crafting())
        self.assertTrue(self.state.ready_to_collect)
        self.assertFalse(self.state.collect()[0])
        self.assertEqual(self.state.collected_equipment_count, 0)
        unit = self.state.available_units("eq_suit_01")[0]
        self.state.store_equipment("eq_suit_01", unit.identifier)
        self.assertEqual(self.state.update_crafting(), "eq_drill_01")
        self.assertEqual(self.state.inventory_used, 9)
        self.assertIsNone(self.state.update_crafting())
        self.assertEqual(self.state.collected_equipment_count, 1)

    def test_rental_return_waits_and_delivers_units_and_reward_without_reroll(self):
        self.state.add_equipment("eq_drill_01", 1)
        unit = self.state.available_units("eq_drill_01")[0]
        unit.level = 4
        self.state.current_order = Order(51, "npc_novice", (("eq_drill_01", 1),))
        self.state.rng.random = Mock(return_value=0)
        self.state.start_rental(51)
        self.state.add_equipment("eq_suit_01", 9)
        self.now = 25
        self.state.update_rentals()
        contract = self.state.rentals[0]
        self.assertEqual(contract.status, "returning")
        self.assertEqual(contract.returned_count, 0)
        for expected in ("returning", "success"):
            suit = self.state.available_units("eq_suit_01")[0]
            self.state.store_equipment("eq_suit_01", suit.identifier)
            self.state.update_rentals()
            self.assertEqual(contract.status, expected)
        self.assertIs(self.state.available_units("eq_drill_01")[0], unit)
        self.assertEqual(unit.level, 4)
        self.assertEqual(self.state.rewards["item_chip"], 1)
        self.state.update_rentals()
        self.assertEqual(self.state.rewards["item_chip"], 1)
        self.assertEqual(self.state.rng.random.call_count, 1)
        self.assertEqual(self.state.inventory_used, 9)

    def test_staging_reserves_space_for_cancelled_ingredients(self):
        self.state.materials.update(mat_01=2, mat_03=1)
        self.state.add_equipment("eq_suit_01", 7)
        self.state.stage_craft_material("eq_drill_01", "mat_01")
        self.assertEqual(self.state.inventory_free, 0)
        self.assertFalse(self.state.add_equipment("eq_drill_01", 1))
        self.state.clear_craft_materials()
        self.assertEqual(self.state.materials["mat_01"], 2)
        self.assertEqual(self.state.inventory_used, 9)

    def test_personal_equipment_does_not_overfill_bag_when_core_stack_remains(self):
        self.state.rewards["item_core"] = 13
        self.state.add_equipment("eq_drill_01", 8)
        self.assertFalse(self.state.craft_personal(PERSONAL_IDS[0])[0])
        self.assertEqual(self.state.rewards["item_core"], 13)
        self.state.rewards["item_core"] = 12
        self.assertTrue(self.state.craft_personal(PERSONAL_IDS[0])[0])
        self.assertEqual(self.state.inventory_used, 9)

    def test_cheat_fills_all_material_stacks_without_creating_equipment_or_rewards(self):
        self.state.add_equipment("eq_drill_01", 2)
        equipment = self.state.equipment.copy()
        rewards = self.state.rewards.copy()
        self.state.apply_cheat()
        self.state.apply_cheat()
        self.assertEqual(self.state.coins, 999)
        self.assertTrue(all(count == 999 for count in self.state.materials.values()))
        self.assertEqual(self.state.equipment, equipment)
        self.assertEqual(self.state.rewards, rewards)
        self.assertEqual(self.state.inventory_used, 5)

    def test_cheat_stores_only_needed_equipment_and_preserves_levels(self):
        self.state.add_equipment("eq_drill_01", 9)
        units = self.state.available_units("eq_drill_01")
        units[0].level = 7
        self.assertTrue(self.state.apply_cheat()[0])
        self.assertTrue(all(count == 999 for count in self.state.materials.values()))
        self.assertEqual(self.state.inventory_used, 9)
        self.assertEqual(self.state.equipment["eq_drill_01"], 6)
        self.assertEqual(self.state.storage_units["eq_drill_01"], list(units[:3]))
        self.assertEqual(units[0].level, 7)
        self.state.apply_cheat()
        self.assertEqual(len(self.state.storage_units["eq_drill_01"]), 3)

    def test_cheat_skips_full_chests_and_moves_another_equipment_type(self):
        self.state.storage_units["eq_drill_01"] = [self.state.new_equipment_unit("eq_drill_01") for _ in range(28)]
        self.state.add_equipment("eq_drill_01", 6)
        self.state.add_equipment("eq_suit_01", 3)
        self.assertTrue(self.state.apply_cheat()[0])
        self.assertEqual(len(self.state.storage_units["eq_drill_01"]), 28)
        self.assertEqual(len(self.state.storage_units["eq_suit_01"]), 3)
        self.assertEqual(self.state.inventory_used, 9)

    def test_cheat_does_not_overfill_or_partially_move_items_when_storage_is_insufficient(self):
        self.state.storage_units["eq_drill_01"] = [self.state.new_equipment_unit("eq_drill_01") for _ in range(27)]
        self.state.add_equipment("eq_drill_01", 9)
        before = self.state.available_units("eq_drill_01")
        success, message = self.state.apply_cheat()
        self.assertFalse(success)
        self.assertIn("공간 부족", message)
        self.assertEqual(self.state.available_units("eq_drill_01"), before)
        self.assertEqual(len(self.state.storage_units["eq_drill_01"]), 27)
        self.assertEqual(self.state.inventory_used, 9)
        self.assertTrue(all(count == 0 for count in self.state.materials.values()))
        self.state.store_equipment("eq_drill_01", before[0].identifier)
        self.state.take_units(before[1:3])
        self.assertTrue(self.state.apply_cheat()[0])
        self.assertTrue(all(count == 999 for count in self.state.materials.values()))
        self.assertEqual(self.state.inventory_used, 9)

    def test_starter_equipment_is_available_once_without_counting_as_crafted(self):
        state = GameState(starter_equipment=True)
        self.assertEqual(state.inventory_used, 3)
        self.assertEqual([item.image for item in state.inventory_items()],
                         ["eq_drill_01", "eq_suit_01", "eq_oxygen_01"])
        self.assertEqual(len({item.unit_id for item in state.inventory_items()}), 3)
        self.assertEqual(state.collected_equipment_count, 0)
        self.assertEqual(state.coins, 100)

    def test_bulk_equipment_moves_clicked_unit_first_and_respects_capacity(self):
        self.state.add_equipment("eq_drill_01", 9)
        units = self.state.available_units("eq_drill_01")
        units[-1].level = 8
        self.assertTrue(self.state.store_equipment("eq_drill_01", units[-1].identifier, 10)[0])
        self.assertEqual(len(self.state.storage_units["eq_drill_01"]), 9)
        self.assertIs(self.state.storage_units["eq_drill_01"][0], units[-1])
        self.state.materials["mat_01"] = 1
        self.assertTrue(self.state.withdraw_equipment("eq_drill_01", units[-1].identifier, None)[0])
        self.assertEqual(self.state.equipment["eq_drill_01"], 8)
        self.assertEqual(len(self.state.storage_units["eq_drill_01"]), 1)
        self.assertIs(self.state.available_units("eq_drill_01")[0], units[-1])
        self.assertEqual(units[-1].level, 8)
        self.assertEqual(self.state.inventory_used, 9)
        self.assertTrue(self.state.store_equipment("eq_drill_01", units[-1].identifier, 1)[0])
        self.assertEqual(self.state.equipment["eq_drill_01"], 7)

    def test_session_result_includes_pending_returns_and_freezes_delivery(self):
        self.state.add_equipment("eq_drill_01", 1)
        self.state.current_order = Order(52, "npc_novice", (("eq_drill_01", 1),))
        self.state.rng.random = Mock(return_value=0)
        self.state.start_rental(52)
        self.state.add_equipment("eq_suit_01", 9)
        self.now = self.state.session_end_at
        result = self.state.finish_session()
        self.assertEqual(result.pending_rentals, 1)
        self.assertEqual(self.state.rentals[0].status, "returning")
        self.state.equipment["eq_suit_01"] = 0
        self.state.update_rentals()
        self.assertEqual(self.state.equipment["eq_drill_01"], 0)


if __name__ == "__main__":
    unittest.main()
