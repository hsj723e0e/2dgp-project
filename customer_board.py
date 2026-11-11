"""The live customer order panel shown at the workshop's noticeboard."""

import sdl2

from orders import CUSTOMER_NAMES
from ui import CREAM, CYAN, GOLD, INK, MUTED, fill_rect
from workshop import EQUIPMENT, HEIGHT, WIDTH


CLOSE = (940, 550, 1036, 590)
DECLINE = (785, 140, 1005, 196)
EQUIPMENT_NAMES = {entry.image: entry.name for entry in EQUIPMENT}


def contains(bounds, x, y):
    left, bottom, right, top = bounds
    return left <= x <= right and bottom <= y <= top


class CustomerBoard:
    def __init__(self, game):
        self.game = game

    def handle_key(self, key):
        if key == sdl2.SDLK_3:
            self.decline()

    def handle_click(self, x, y):
        if contains(CLOSE, x, y):
            self.game.close_panel()
        elif contains(DECLINE, x, y):
            self.decline()

    def decline(self):
        order = self.game.state.current_order
        if order is not None:
            self.game.feedback_success, self.game.feedback = self.game.state.decline_order(order.identifier)

    def draw(self):
        game, state = self.game, self.game.state
        fill_rect(0, 0, WIDTH, HEIGHT, INK, 155)
        game.draw_panel_frame()
        game.text(278, 572, "주문 게시판", 30)
        game.draw_button(CLOSE, "닫기")
        fill_rect(275, 510, 730, 2, (61, 87, 103))
        order = state.current_order
        if order is None:
            game.text(278, 534, "다음 손님을 기다리고 있습니다.", 18, MUTED)
            game.text(340, 380, f"다음 방문까지 {state.next_customer_in:.1f}초", 22, GOLD)
        else:
            game.text(278, 534, f"{CUSTOMER_NAMES[order.customer]}의 주문 · 총 {order.quantity}개", 18, MUTED)
            game.icons[order.customer].draw(870, 430, 152, 152)
            game.text(766, 329, CUSTOMER_NAMES[order.customer], 22)
            for index, (equipment, quantity) in enumerate(order.requirements):
                y = 470 - index * 60
                owned = state.equipment[equipment]
                fill_rect(275, y - 26, 440, 52, (20, 40, 56))
                game.icons[equipment].draw(305, y, 42, 42)
                game.text(339, y + 7, EQUIPMENT_NAMES[equipment], 18)
                game.text(339, y - 14, f"요청 {quantity}개 / 보유 {owned}개", 15, CYAN if owned >= quantity else GOLD)
            if order.customer == "npc_broker":
                game.text(278, 465, "코인을 받고 다음 시장 사건을 알려드립니다.", 18)
            game.draw_button(DECLINE, "3  거절하기")
        if game.feedback:
            game.text(278, 224, game.feedback, 15, CYAN if game.feedback_success else GOLD)
