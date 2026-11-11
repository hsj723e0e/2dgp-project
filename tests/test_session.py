import unittest

from game_state import GameState
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
