import random
import unittest

from game_state import GameState, RECIPES
from orders import INFORMATION_PRICE, MARKET_EVENTS, MARKET_INTERVAL, Order, create_order


class TradingTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.state = GameState(clock=lambda: self.now, rng=random.Random(4))

    def test_each_equipment_customer_can_sell_and_duplicate_request_is_rejected(self):
        for identifier, customer in enumerate(("npc_novice", "npc_expert", "npc_tourist", "npc_mysterious"), 10):
            order = create_order(identifier, customer, random.Random(identifier))
            self.state.current_order = order
            for equipment, quantity in order.requirements:
                self.state.equipment[equipment] = quantity
            before = self.state.coins
            value = self.state.sale_value(order)
            self.assertTrue(self.state.sell_order(identifier)[0])
            self.assertEqual(self.state.coins, before + value)
            for equipment, _ in order.requirements:
                self.assertEqual(self.state.equipment[equipment], 0)
            self.assertFalse(self.state.sell_order(identifier)[0])
            self.assertEqual(self.state.coins, before + value)

    def test_missing_one_item_prevents_partial_sale(self):
        order = Order(20, "npc_tourist", (("eq_drill_01", 2), ("eq_suit_02", 2)))
        self.state.current_order = order
        self.state.equipment["eq_drill_01"] = 2
        self.state.equipment["eq_suit_02"] = 1
        inventory = self.state.equipment.copy()
        self.assertFalse(self.state.sell_order(20)[0])
        self.assertEqual(self.state.equipment, inventory)
        self.assertEqual(self.state.coins, 100)
        self.assertIs(self.state.current_order, order)

    def test_completed_order_cannot_process_the_next_customer(self):
        old = self.state.current_order
        self.state.decline_order(old.identifier)
        self.now = 8
        self.state.update_customers()
        current = self.state.current_order
        self.assertFalse(self.state.sell_order(old.identifier)[0])
        self.assertIs(self.state.current_order, current)

    def test_market_changes_sale_prices_but_keeps_material_purchase_price(self):
        order = Order(1, "npc_novice", (("eq_drill_01", 1), ("eq_suit_01", 1)))
        self.assertEqual(self.state.sale_value(order), 82)
        self.now = MARKET_INTERVAL
        self.assertEqual(self.state.market_event, MARKET_EVENTS[0])
        self.assertEqual(self.state.sale_value(order), 90)
        self.now = MARKET_INTERVAL * 2
        self.assertEqual(self.state.market_event, MARKET_EVENTS[1])
        self.assertEqual(self.state.sale_value(order), 94)
        self.state.purchase("mat_01", 1)
        self.assertEqual(self.state.coins, 92)

    def test_information_payment_reports_the_actual_next_event_and_expires(self):
        self.state.current_order = Order(50, "npc_broker", ())
        self.assertFalse(self.state.sell_order(50)[0])
        self.assertTrue(self.state.buy_information(50)[0])
        self.assertEqual(self.state.coins, 100 - INFORMATION_PRICE)
        predicted = self.state.known_next_event
        self.assertEqual(predicted, MARKET_EVENTS[0].name)
        self.assertFalse(self.state.buy_information(50)[0])
        self.now = MARKET_INTERVAL
        self.assertEqual(self.state.market_event.name, predicted)
        self.assertIsNone(self.state.known_next_event)

    def test_insufficient_information_funds_do_not_consume_order_or_inventory(self):
        self.state.current_order = Order(51, "npc_broker", ())
        self.state.coins = INFORMATION_PRICE - 1
        self.assertFalse(self.state.buy_information(51)[0])
        self.assertEqual(self.state.coins, INFORMATION_PRICE - 1)
        self.assertEqual(self.state.current_order.identifier, 51)
        self.assertEqual(sum(self.state.equipment.values()), 0)

    def test_new_session_can_buy_craft_collect_and_sell_first_order(self):
        order = self.state.current_order
        for equipment, quantity in order.requirements:
            recipe = RECIPES[equipment]
            for material, needed in recipe.ingredients.items():
                self.assertTrue(self.state.purchase(material, needed * quantity)[0])
            for _ in range(quantity):
                self.assertTrue(self.state.start_craft(equipment)[0])
                self.now += recipe.seconds
                self.assertTrue(self.state.collect()[0])
        coins = self.state.coins
        value = self.state.sale_value(order)
        self.assertTrue(self.state.sell_order(order.identifier)[0])
        self.assertEqual(self.state.coins, coins + value)
        self.assertGreater(self.state.coins, 100)
        self.assertEqual(sum(self.state.equipment.values()), 0)


if __name__ == "__main__":
    unittest.main()
