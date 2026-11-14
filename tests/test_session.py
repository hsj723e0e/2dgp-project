import unittest

from game_state import GameState, PERSONAL_IDS
from orders import Order


class SessionClockTests(unittest.TestCase):
    def test_twenty_minute_default_and_deadline_clamping(self):
        now = [100.0]
        state = GameState(clock=lambda: now[0])
        self.assertEqual(state.session_remaining, 1200)
        now[0] = 1300
        self.assertTrue(state.session_over)
        self.assertEqual(state.session_remaining, 0)
        now[0] = 5000
        self.assertEqual(state.effective_time, 1300)
        self.assertEqual(state.session_remaining, 0)

    def test_delayed_frame_does_not_settle_rental_due_after_session(self):
        now = [0.0]
        state = GameState(clock=lambda: now[0], session_duration=20)
        state.equipment["eq_drill_01"] = 1
        state.current_order = Order(1, "npc_novice", (("eq_drill_01", 1),))
        state.start_rental(1)
        state.rng.random = lambda: 0
        now[0] = 100
        state.update_rentals()
        self.assertEqual(state.rentals[0].status, "active")
        self.assertEqual(state.equipment["eq_drill_01"], 0)
        self.assertEqual(state.rewards["item_chip"], 0)

    def test_deadline_result_settles_due_rentals_once_and_freezes_personal_levels(self):
        now = [0.0]
        state = GameState(clock=lambda: now[0], session_duration=25)
        state.equipment["eq_drill_01"] = 1
        state.current_order = Order(1, "npc_novice", (("eq_drill_01", 1),))
        state.start_rental(1)
        state.personal_equipment[PERSONAL_IDS[0]] = 4
        state.rng.random = lambda: 0
        now[0] = 100
        result = state.finish_session()
        self.assertEqual(result.rental_successes, 1)
        self.assertEqual(result.pending_rentals, 0)
        self.assertEqual(dict(result.personal_levels)[PERSONAL_IDS[0]], 4)
        self.assertIs(state.finish_session(), result)
        self.assertEqual(state.equipment["eq_drill_01"], 1)
        state.personal_equipment[PERSONAL_IDS[0]] = 13
        self.assertEqual(dict(result.personal_levels)[PERSONAL_IDS[0]], 4)

    def test_no_currency_inventory_or_progression_changes_after_deadline(self):
        now = [0.0]
        state = GameState(clock=lambda: now[0], session_duration=5)
        state.equipment["eq_drill_01"] = 1
        state.apply_cheat()
        unit = state.available_units("eq_drill_01")[0]
        state.personal_equipment[PERSONAL_IDS[0]] = 0
        order_id = state.current_order.identifier
        before = (state.coins, state.materials.copy(), state.equipment.copy(), state.rewards.copy())
        now[0] = 5
        actions = (
            lambda: state.purchase("mat_01", 1),
            lambda: state.start_craft("eq_drill_01"),
            state.collect,
            lambda: state.sell_order(order_id),
            lambda: state.start_rental(order_id),
            lambda: state.decline_order(order_id),
            lambda: state.enhance_basic("eq_drill_01", unit.identifier),
            lambda: state.craft_personal(PERSONAL_IDS[1]),
            lambda: state.enhance_personal(PERSONAL_IDS[0]),
        )
        for action in actions:
            self.assertFalse(action()[0])
        state.apply_cheat()
        self.assertEqual((state.coins, state.materials, state.equipment, state.rewards), before)
        self.assertEqual(unit.level, 0)
        self.assertEqual(state.personal_equipment[PERSONAL_IDS[0]], 0)
