"""The live customer order panel shown at the workshop's noticeboard."""

import sdl2

from orders import CUSTOMER_NAMES, INFORMATION_PRICE
from ui import CREAM, CYAN, GOLD, INK, MUTED, fill_rect
from workshop import EQUIPMENT, HEIGHT, WIDTH


CLOSE = (940, 550, 1036, 590)
DECLINE = (785, 140, 1005, 196)
SELL = (275, 140, 495, 196)
EQUIPMENT_NAMES = {entry.image: entry.name for entry in EQUIPMENT}


def contains(bounds, x, y):
    left, bottom, right, top = bounds
    return left <= x <= right and bottom <= y <= top


class CustomerBoard:
    def __init__(self, game):
        self.game = game

    def handle_key(self, key):
        if key == sdl2.SDLK_1:
            self.sell()
        elif key == sdl2.SDLK_3:
            self.decline()

    def handle_click(self, x, y):
        if contains(CLOSE, x, y):
            self.game.close_panel()
        elif contains(DECLINE, x, y):
            self.decline()
        elif contains(SELL, x, y):
            self.sell()

    def sell(self):
        state = self.game.state
        order = state.current_order
        if order is None:
            return
        action = state.buy_information if order.customer == "npc_broker" else state.sell_order
        self.game.feedback_success, self.game.feedback = action(order.identifier)

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
        event = state.market_event
        market_name = event.name if event else "기본 시세"
        game.text(278, 248, f"현재 시세 · {market_name} ({state.market_remaining:.0f}초)", 15, MUTED)
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
                game.text(278, 425, f"정보 가격 {INFORMATION_PRICE} 코인", 22, GOLD)
                available, reason = state.information_status(order.identifier)
                game.draw_button(SELL, f"1 정보 {INFORMATION_PRICE} 코인", available)
            else:
                available, reason = state.order_status(order.identifier)
                value = state.sale_value(order)
                game.text(766, 300, f"판매 {value} 코인", 18, GOLD)
                game.draw_button(SELL, f"1 판매 +{value} 코인", available)
            if reason and not game.feedback:
                game.text(278, 224, reason, 15, GOLD)
            game.draw_button(DECLINE, "3  거절하기")
        if state.known_next_event:
            game.text(278, 125, f"구매한 정보 · 다음은 {state.known_next_event}", 15, CYAN)
        if game.feedback:
            game.text(278, 224, game.feedback, 15, CYAN if game.feedback_success else GOLD)
