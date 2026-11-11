import unittest

from game_state import GameState


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


if __name__ == "__main__":
    unittest.main()
