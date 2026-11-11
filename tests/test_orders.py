import random
import unittest

from game_state import CUSTOMER_INTERVAL, GameState
from orders import ALL_EQUIPMENT, BASIC_EQUIPMENT, MEDIUM_EQUIPMENT, create_order


class OrderGenerationTests(unittest.TestCase):
    def test_novice_and_expert_request_one_or_two_within_their_tier(self):
        for customer, allowed in (("npc_novice", BASIC_EQUIPMENT), ("npc_expert", MEDIUM_EQUIPMENT)):
            rng = random.Random(17)
            observed_quantities = set()
            for identifier in range(200):
                order = create_order(identifier, customer, rng)
                observed_quantities.add(order.quantity)
                self.assertTrue(set(dict(order.requirements)) <= set(allowed))
                self.assertIn(order.quantity, (1, 2))
            self.assertEqual(observed_quantities, {1, 2})

    def test_tourist_requests_four_and_can_repeat_equipment(self):
        rng = random.Random(22)
        repeated = False
        for identifier in range(100):
            order = create_order(identifier, "npc_tourist", rng)
            self.assertEqual(order.quantity, 4)
            self.assertTrue(set(dict(order.requirements)) <= set(ALL_EQUIPMENT))
            repeated |= any(quantity > 1 for _, quantity in order.requirements)
        self.assertTrue(repeated)

    def test_mysterious_customer_requests_four_distinct_items(self):
        rng = random.Random(33)
        for identifier in range(100):
            order = create_order(identifier, "npc_mysterious", rng)
            self.assertEqual(order.quantity, 4)
            self.assertEqual(len(order.requirements), 4)
            self.assertTrue(all(quantity == 1 for _, quantity in order.requirements))

    def test_broker_requests_no_equipment(self):
        order = create_order(1, "npc_broker", random.Random(0))
        self.assertEqual(order.quantity, 0)
        self.assertEqual(order.requirements, ())


class CustomerArrivalTests(unittest.TestCase):
    def test_first_customer_is_novice_and_unresolved_order_is_preserved(self):
        state = GameState(clock=lambda: 100, rng=random.Random(2))
        original = state.current_order
        self.assertEqual(original.customer, "npc_novice")
        for _ in range(10):
            state.update_customers()
        self.assertIs(state.current_order, original)

    def test_decline_then_arrival_and_stale_order_rejection(self):
        now = [100.0]
        state = GameState(clock=lambda: now[0], rng=random.Random(2))
        original = state.current_order
        self.assertTrue(state.decline_order(original.identifier)[0])
        self.assertIsNone(state.current_order)
        self.assertFalse(state.decline_order(original.identifier)[0])
        now[0] += CUSTOMER_INTERVAL - 0.01
        state.update_customers()
        self.assertIsNone(state.current_order)
        now[0] += 0.01
        state.update_customers()
        self.assertIsNotNone(state.current_order)
        self.assertNotEqual(state.current_order.identifier, original.identifier)
        self.assertFalse(state.decline_order(original.identifier)[0])
        self.assertEqual(state.coins, 100)
        self.assertEqual(sum(state.equipment.values()), 0)


if __name__ == "__main__":
    unittest.main()
