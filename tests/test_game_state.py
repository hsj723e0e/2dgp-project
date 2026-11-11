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
        for equipment, recipe in RECIPES.items():
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

    def test_failed_craft_keeps_every_material(self):
        state = GameState()
        state.purchase("mat_01", 2)
        materials = state.materials.copy()
        for equipment in ("eq_drill_01", "eq_drill_02", "unknown"):
            self.assertFalse(state.start_craft(equipment)[0])
            self.assertEqual(state.materials, materials)
            self.assertIsNone(state.job)


if __name__ == "__main__":
    unittest.main()
