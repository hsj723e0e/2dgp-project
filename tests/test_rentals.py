import random
import unittest
from unittest.mock import Mock, patch

from game_state import GameState
from orders import Order, RENTAL_DURATIONS, RENTAL_SUCCESS_RATE, create_order


class RentalTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.state = GameState(clock=lambda: self.now, rng=random.Random(8))
        self.state.rng.random = Mock(return_value=0.0)

    def supply_order(self, customer, identifier=40):
        order = create_order(identifier, customer, random.Random(identifier))
        self.state.current_order = order
        for equipment, quantity in order.requirements:
            self.state.equipment[equipment] += quantity
        return order

    def test_each_customer_returns_items_and_receives_only_their_reward_once(self):
        for index, customer in enumerate(RENTAL_DURATIONS, 40):
            with self.subTest(customer=customer):
                order = self.supply_order(customer, index)
                inventory = self.state.equipment.copy()
                coins = self.state.coins
                rewards = self.state.rewards.copy()
                reward, amount = self.state.rental_reward(order)
                self.assertTrue(self.state.start_rental(order.identifier)[0])
                contract = self.state.rentals[-1]
                self.assertEqual(contract.success_probability, RENTAL_SUCCESS_RATE)
                for equipment, quantity in order.requirements:
                    self.assertEqual(self.state.equipment[equipment], inventory[equipment] - quantity)
                self.assertEqual(self.state.coins, coins)
                self.now += RENTAL_DURATIONS[customer]
                self.state.update_rentals()
                self.assertEqual(contract.status, "success")
                self.assertEqual(self.state.equipment, inventory)
                expected_coins = coins + amount if reward == "coins" else coins
                self.assertEqual(self.state.coins, expected_coins)
                if reward != "coins":
                    rewards[reward] += amount
                self.assertEqual(self.state.rewards, rewards)
                self.state.update_rentals()
                self.assertEqual(self.state.equipment, inventory)
                self.assertEqual(self.state.coins, expected_coins)
                self.assertEqual(self.state.rewards, rewards)
        self.assertEqual(self.state.rng.random.call_count, 4)

    def test_failure_loses_only_rented_items_and_never_awards_rewards(self):
        order = self.supply_order("npc_mysterious")
        self.state.equipment["eq_drill_01"] += 3
        self.state.rng.random.return_value = 0.99
        self.assertTrue(self.state.start_rental(order.identifier)[0])
        loaned_inventory = self.state.equipment.copy()
        self.now = 40
        self.state.update_rentals()
        self.assertEqual(self.state.rentals[-1].status, "lost")
        self.assertEqual(self.state.equipment, loaned_inventory)
        self.assertEqual(self.state.coins, 100)
        self.assertEqual(sum(self.state.rewards.values()), 0)
        self.state.update_rentals()
        self.assertEqual(self.state.rng.random.call_count, 1)

    def test_timer_boundary_does_not_settle_early(self):
        order = self.supply_order("npc_novice")
        self.state.start_rental(order.identifier)
        self.now = RENTAL_DURATIONS["npc_novice"] - .001
        self.state.update_rentals()
        self.assertEqual(self.state.rentals[-1].status, "active")
        self.assertEqual(self.state.rng.random.call_count, 0)
        self.now += .001
        self.state.update_rentals()
        self.assertEqual(self.state.rentals[-1].status, "success")

    def test_missing_inventory_and_broker_requests_are_not_reserved(self):
        order = Order(60, "npc_tourist", (("eq_drill_01", 2), ("eq_suit_02", 2)))
        self.state.current_order = order
        self.state.equipment["eq_drill_01"] = 2
        inventory = self.state.equipment.copy()
        self.assertFalse(self.state.start_rental(60)[0])
        self.assertEqual(self.state.equipment, inventory)
        self.assertEqual(self.state.rentals, [])
        self.assertIs(self.state.current_order, order)
        self.state.current_order = Order(61, "npc_broker", ())
        self.assertFalse(self.state.start_rental(61)[0])
        self.assertEqual(self.state.coins, 100)
        self.assertEqual(self.state.rentals, [])

    def test_rental_and_sale_cannot_both_consume_same_order(self):
        order = self.supply_order("npc_novice")
        self.assertTrue(self.state.start_rental(order.identifier)[0])
        reserved = self.state.equipment.copy()
        self.assertFalse(self.state.start_rental(order.identifier)[0])
        self.assertFalse(self.state.sell_order(order.identifier)[0])
        self.assertEqual(self.state.equipment, reserved)
        self.assertEqual(len(self.state.rentals), 1)
        self.assertEqual(self.state.coins, 100)

    def test_contract_keeps_its_reward_and_probability_when_market_changes(self):
        order = self.supply_order("npc_tourist")
        reward, amount = self.state.rental_reward(order)
        self.state.start_rental(order.identifier)
        contract = self.state.rentals[-1]
        self.now = 120
        with patch("game_state.RENTAL_SUCCESS_RATE", 0.0):
            self.state.update_rentals()
        self.assertEqual(contract.success_probability, .85)
        self.assertEqual(contract.reward_item, reward)
        self.assertEqual(contract.reward_amount, amount)
        self.assertEqual(self.state.coins, 100 + amount)

    def test_multiple_contracts_settle_independently(self):
        for identifier, customer in enumerate(("npc_novice", "npc_expert", "npc_tourist"), 90):
            order = self.supply_order(customer, identifier)
            self.assertTrue(self.state.start_rental(order.identifier)[0])
        self.now = 25
        self.state.update_rentals()
        self.assertEqual([rental.status for rental in self.state.rentals], ["success", "active", "active"])
        self.now = 35
        self.state.update_rentals()
        self.assertTrue(all(rental.status == "success" for rental in self.state.rentals))
        self.assertEqual(self.state.rng.random.call_count, 3)


if __name__ == "__main__":
    unittest.main()
