import unittest

from game_state import GameState


class MaterialStorageTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.state = GameState(clock=lambda: self.now)

    def test_all_six_resources_merge_and_withdraw_to_their_original_inventory(self):
        self.state.materials.update(mat_01=999, mat_02=12, mat_03=24)
        self.state.rewards.update(item_chip=3, item_core=12, item_secret=2)
        quantities = {**self.state.materials, **self.state.rewards}
        for image, amount in quantities.items():
            self.assertTrue(self.state.store_resource(image)[0])
            self.assertEqual(self.state.resource_storage[image], amount)
        self.assertEqual(self.state.inventory_used, 0)
        self.state.materials["mat_01"] = 1000000
        self.state.store_resource("mat_01")
        quantities["mat_01"] += 1000000
        for image, amount in quantities.items():
            self.assertTrue(self.state.withdraw_resource(image)[0])
            inventory = self.state.materials if image in self.state.materials else self.state.rewards
            self.assertEqual(inventory[image], amount)
            self.assertEqual(self.state.resource_storage[image], 0)
        self.assertEqual(self.state.inventory_used, 6)

    def test_full_bag_rejects_new_resource_type_but_merges_existing_stack(self):
        self.state.materials["mat_01"] = 1
        self.state.add_equipment("eq_drill_01", 8)
        self.state.resource_storage.update(mat_01=20, mat_02=30)
        self.assertFalse(self.state.withdraw_resource("mat_02")[0])
        self.assertEqual(self.state.resource_storage["mat_02"], 30)
        self.assertEqual(self.state.materials["mat_02"], 0)
        self.assertTrue(self.state.withdraw_resource("mat_01")[0])
        self.assertEqual(self.state.materials["mat_01"], 21)
        self.assertEqual(self.state.inventory_used, 9)

    def test_invalid_item_empty_slot_and_repeated_transfer_do_not_duplicate_items(self):
        self.state.add_equipment("eq_drill_01", 1)
        self.assertFalse(self.state.store_resource("eq_drill_01")[0])
        self.assertFalse(self.state.withdraw_resource("unknown")[0])
        self.assertFalse(self.state.withdraw_resource("item_core")[0])
        self.state.rewards["item_core"] = 12
        self.assertTrue(self.state.store_resource("item_core")[0])
        self.assertFalse(self.state.store_resource("item_core")[0])
        self.assertTrue(self.state.withdraw_resource("item_core")[0])
        self.assertFalse(self.state.withdraw_resource("item_core")[0])
        self.assertEqual(self.state.rewards["item_core"], 12)
        self.assertEqual(self.state.equipment["eq_drill_01"], 1)

    def test_staged_material_refund_remains_consistent_with_storage_transfer(self):
        self.state.materials.update(mat_01=5, mat_03=1)
        self.state.stage_craft_material("eq_drill_01", "mat_01")
        self.state.store_resource("mat_01")
        self.assertEqual(self.state.resource_storage["mat_01"], 3)
        self.state.clear_craft_materials()
        self.assertEqual(self.state.materials["mat_01"], 2)
        self.state.withdraw_resource("mat_01")
        self.assertEqual(self.state.materials["mat_01"], 5)

    def test_transfers_stop_at_session_end_and_cheat_keeps_stored_counts(self):
        self.state.materials["mat_01"] = 17
        self.state.store_resource("mat_01")
        self.state.apply_cheat()
        self.assertEqual(self.state.resource_storage["mat_01"], 17)
        before = (self.state.materials.copy(), self.state.resource_storage.copy())
        self.now = self.state.session_end_at
        self.assertFalse(self.state.store_resource("mat_02")[0])
        self.assertFalse(self.state.withdraw_resource("mat_01")[0])
        self.assertEqual((self.state.materials, self.state.resource_storage), before)


if __name__ == "__main__":
    unittest.main()
