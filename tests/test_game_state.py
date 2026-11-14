import unittest

from game_state import GameState, RECIPES


class MaterialPurchaseTests(unittest.TestCase):
    def test_new_session_and_bulk_purchase(self):
        state = GameState()
        self.assertEqual(state.coins, 100)
        self.assertEqual(state.materials, {"mat_01": 0, "mat_02": 0, "mat_03": 0})
        self.assertTrue(state.purchase("mat_01", 3)[0])
        self.assertEqual(state.coins, 76)
        self.assertEqual(state.materials["mat_01"], 3)

    def test_exact_balance_and_insufficient_funds(self):
        state = GameState()
        self.assertTrue(state.purchase("mat_03", 25)[0])
        self.assertEqual(state.coins, 0)
        self.assertFalse(state.purchase("mat_01", 1)[0])
        self.assertEqual(state.materials["mat_01"], 0)
        self.assertEqual(state.materials["mat_03"], 25)

    def test_invalid_purchase_keeps_currency_and_inventory(self):
        state = GameState()
        for material, quantity in [("unknown", 1), ("mat_01", 0), ("mat_01", -2),
                                   ("mat_01", 1.5), ("mat_01", True)]:
            with self.subTest(material=material, quantity=quantity):
                self.assertFalse(state.purchase(material, quantity)[0])
                self.assertEqual(state.coins, 100)
                self.assertEqual(sum(state.materials.values()), 0)


class CraftingTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.state = GameState(clock=lambda: self.now)
        self.state.purchase("mat_01", 7)
        self.state.purchase("mat_03", 5)

    def test_all_three_recipes_and_manual_collection(self):
        for equipment in ("eq_drill_01", "eq_suit_01", "eq_oxygen_01"):
            recipe = RECIPES[equipment]
            with self.subTest(equipment=equipment):
                materials_before = self.state.materials.copy()
                self.assertTrue(self.state.start_craft(equipment)[0])
                for name, quantity in recipe.ingredients.items():
                    self.assertEqual(self.state.materials[name], materials_before[name] - quantity)
                self.assertFalse(self.state.collect()[0])
                self.now += recipe.seconds
                self.assertTrue(self.state.ready_to_collect)
                self.assertEqual(self.state.equipment[equipment], 0)
                self.assertTrue(self.state.collect()[0])
                self.assertEqual(self.state.equipment[equipment], 1)
                self.assertIsNone(self.state.job)
                self.assertFalse(self.state.collect()[0])
        self.assertEqual(self.state.coins, 24)
        self.assertEqual(self.state.materials["mat_01"], 0)
        self.assertEqual(self.state.materials["mat_03"], 0)

    def test_running_and_uncollected_job_prevent_another_craft(self):
        self.state.start_craft("eq_drill_01")
        job = self.state.job
        materials = self.state.materials.copy()
        self.assertFalse(self.state.start_craft("eq_suit_01")[0])
        self.now += 10
        self.assertFalse(self.state.start_craft("eq_suit_01")[0])
        self.assertEqual(self.state.job, job)
        self.assertEqual(self.state.materials, materials)
        self.assertTrue(self.state.collect()[0])
        self.assertTrue(self.state.start_craft("eq_suit_01")[0])

    def test_completion_boundary_and_no_automatic_inventory_addition(self):
        self.state.start_craft("eq_drill_01")
        self.now = 109.999
        self.assertFalse(self.state.ready_to_collect)
        self.assertFalse(self.state.collect()[0])
        self.now = 110
        self.assertEqual(self.state.remaining, 0)
        self.assertTrue(self.state.ready_to_collect)
        self.assertEqual(sum(self.state.equipment.values()), 0)
        self.now = 1000
        self.assertEqual(sum(self.state.equipment.values()), 0)
        self.assertTrue(self.state.collect()[0])
        self.assertFalse(self.state.collect()[0])
        self.assertEqual(sum(self.state.equipment.values()), 1)

    def test_automatic_collection_at_completion_boundary_is_idempotent(self):
        self.state.start_craft("eq_drill_01")
        self.now = 109.999
        self.assertIsNone(self.state.update_crafting())
        self.assertEqual(self.state.equipment["eq_drill_01"], 0)
        self.now = 110
        self.assertEqual(self.state.update_crafting(), "eq_drill_01")
        self.assertEqual(self.state.equipment["eq_drill_01"], 1)
        self.assertEqual(len(self.state.available_units("eq_drill_01")), 1)
        self.assertEqual(self.state.collected_equipment_count, 1)
        self.assertIsNone(self.state.update_crafting())
        self.assertEqual(self.state.equipment["eq_drill_01"], 1)
        self.assertTrue(self.state.start_craft("eq_suit_01")[0])

    def test_delayed_frame_collects_only_jobs_due_by_session_end(self):
        for duration, expected in ((10, 1), (9, 0)):
            with self.subTest(duration=duration):
                now = [0.0]
                state = GameState(clock=lambda: now[0], session_duration=duration)
                state.materials.update(mat_01=2, mat_03=1)
                self.assertTrue(state.start_craft("eq_drill_01")[0])
                now[0] = 100
                result = state.finish_session()
                self.assertEqual(result.collected_equipment, expected)
                self.assertEqual(state.equipment["eq_drill_01"], expected)
                self.assertIsNone(state.update_crafting())
                self.assertEqual(state.equipment["eq_drill_01"], expected)

    def test_failed_craft_keeps_every_material(self):
        state = GameState()
        state.purchase("mat_01", 2)
        materials = state.materials.copy()
        for equipment in ("eq_drill_01", "eq_drill_02", "unknown"):
            self.assertFalse(state.start_craft(equipment)[0])
            self.assertEqual(state.materials, materials)
            self.assertIsNone(state.job)

    def test_medium_recipes_use_composite_materials_and_can_be_collected(self):
        for equipment in ("eq_drill_02", "eq_suit_02", "eq_oxygen_02"):
            with self.subTest(equipment=equipment):
                state = GameState(clock=lambda: self.now)
                recipe = RECIPES[equipment]
                for name, quantity in recipe.ingredients.items():
                    self.assertTrue(state.purchase(name, quantity)[0])
                self.assertTrue(state.start_craft(equipment)[0])
                self.now += recipe.seconds
                self.assertTrue(state.collect()[0])
                self.assertEqual(state.equipment[equipment], 1)
                self.assertEqual(sum(state.materials.values()), 0)


class CraftMaterialStagingTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.state = GameState(clock=lambda: self.now)
        self.state.materials.update(mat_01=3, mat_03=2)

    def test_exact_inventory_stages_once_and_is_not_spent_again_at_start(self):
        for material in ("mat_01", "mat_03"):
            self.assertTrue(self.state.stage_craft_material("eq_suit_01", material)[0])
            self.assertEqual(self.state.materials[material], 0)
            self.assertTrue(self.state.stage_craft_material("eq_suit_01", material)[0])
            self.assertEqual(self.state.materials[material], 0)
        self.assertTrue(self.state.craft_status("eq_suit_01")[0])
        self.assertTrue(self.state.start_craft("eq_suit_01")[0])
        self.assertFalse(self.state.staged_materials)
        self.state.clear_craft_materials()
        self.assertEqual(sum(self.state.materials.values()), 0)
        self.assertFalse(self.state.start_craft("eq_suit_01")[0])
        self.assertFalse(self.state.stage_craft_material("eq_suit_01", "mat_01")[0])
        self.now = 12
        self.state.update_crafting()
        self.assertEqual(self.state.equipment["eq_suit_01"], 1)
        self.assertEqual(sum(self.state.materials.values()), 0)

    def test_unstage_and_reset_return_only_reserved_quantities_once(self):
        before = self.state.materials.copy()
        self.state.stage_craft_material("eq_suit_01", "mat_01")
        self.state.stage_craft_material("eq_suit_01", "mat_03")
        self.state.unstage_craft_material("mat_01")
        self.state.unstage_craft_material("mat_01")
        self.assertEqual(self.state.materials["mat_01"], 3)
        self.assertEqual(self.state.materials["mat_03"], 0)
        self.state.clear_craft_materials()
        self.state.clear_craft_materials()
        self.assertEqual(self.state.materials, before)
        self.assertIsNone(self.state.staged_equipment)

    def test_failed_staging_and_crafting_preserve_partial_reservation(self):
        self.state.materials["mat_03"] = 0
        self.state.stage_craft_material("eq_suit_01", "mat_01")
        before = self.state.materials.copy()
        staged = self.state.staged_materials.copy()
        for equipment, material in (("eq_suit_01", "mat_03"), ("eq_suit_01", "mat_02"),
                                    ("eq_drill_01", "mat_01"), ("unknown", "mat_01")):
            self.assertFalse(self.state.stage_craft_material(equipment, material)[0])
        self.assertFalse(self.state.start_craft("eq_suit_01")[0])
        self.assertEqual(self.state.materials, before)
        self.assertEqual(self.state.staged_materials, staged)

    def test_session_end_refunds_staged_materials_and_blocks_new_staging(self):
        before = self.state.materials.copy()
        self.state.stage_craft_material("eq_suit_01", "mat_01")
        self.now = self.state.session_end_at
        self.state.finish_session()
        self.assertEqual(self.state.materials, before)
        self.assertFalse(self.state.staged_materials)
        self.assertFalse(self.state.stage_craft_material("eq_suit_01", "mat_01")[0])

    def test_cheat_clears_reservation_before_setting_inventory(self):
        self.state.stage_craft_material("eq_suit_01", "mat_01")
        self.state.apply_cheat()
        self.state.clear_craft_materials()
        self.assertEqual(self.state.materials["mat_01"], 999)
        self.assertFalse(self.state.staged_materials)


if __name__ == "__main__":
    unittest.main()
