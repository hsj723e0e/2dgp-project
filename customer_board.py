"""The live customer order panel shown at the workshop's noticeboard."""

import sdl2

from orders import CUSTOMER_NAMES, INFORMATION_PRICE, RENTAL_DURATIONS, RENTAL_SUCCESS_RATE, REWARD_NAMES
from ui import CREAM, CYAN, GOLD, INK, MUTED, RED, fill_rect, quantity_badge, quantity_pair
from workshop import EQUIPMENT, HEIGHT, WIDTH


CLOSE = (940, 550, 1036, 590)
DECLINE = (785, 140, 1005, 196)
SELL = (275, 140, 495, 196)
RENT = (530, 140, 750, 196)
VIEW_RENTALS = (760, 550, 920, 590)
EQUIPMENT_NAMES = {entry.image: entry.name for entry in EQUIPMENT}


def contains(bounds, x, y):
    left, bottom, right, top = bounds
    return left <= x <= right and bottom <= y <= top


class CustomerBoard:
    def __init__(self, game):
        self.game = game
        self.reset()

    def reset(self):
        self.show_rentals = False
        self.selected_contract = 0

    @property
    def contracts(self):
        return list(reversed(self.game.state.rentals))

    def toggle_view(self):
        self.show_rentals = not self.show_rentals
        self.selected_contract = 0

    def handle_key(self, key):
        if key == sdl2.SDLK_TAB:
            self.toggle_view()
        elif self.show_rentals:
            contracts = self.contracts
            if contracts and key in (sdl2.SDLK_UP, sdl2.SDLK_w):
                self.selected_contract = (self.selected_contract - 1) % len(contracts)
            elif contracts and key in (sdl2.SDLK_DOWN, sdl2.SDLK_s):
                self.selected_contract = (self.selected_contract + 1) % len(contracts)
        elif key == sdl2.SDLK_1:
            self.sell()
        elif key == sdl2.SDLK_2:
            self.rent()
        elif key == sdl2.SDLK_3:
            self.decline()

    def handle_click(self, x, y):
        if contains(CLOSE, x, y):
            self.game.close_panel()
        elif contains(VIEW_RENTALS, x, y):
            self.toggle_view()
        elif self.show_rentals:
            start = self.selected_contract // 6 * 6
            for index in range(start, min(start + 6, len(self.contracts))):
                row_y = 478 - (index - start) * 52
                if 275 <= x <= 715 and row_y - 24 <= y <= row_y + 24:
                    self.selected_contract = index
                    break
        elif contains(DECLINE, x, y):
            self.decline()
        elif contains(SELL, x, y):
            self.sell()
        elif contains(RENT, x, y):
            self.rent()

    def rent(self):
        order = self.game.state.current_order
        if order is not None and order.customer != "npc_broker":
            self.game.feedback_success, self.game.feedback = self.game.state.start_rental(order.identifier)

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
        game.text(278, 572, "대여 현황" if self.show_rentals else "주문 게시판", 30)
        game.draw_button(CLOSE, "닫기")
        game.draw_button(VIEW_RENTALS, "주문 보기" if self.show_rentals else "대여 현황")
        fill_rect(275, 510, 730, 2, (61, 87, 103))
        if self.show_rentals:
            self.draw_rentals()
            return
        event = state.market_event
        market_name = event.name if event else "기본 시세"
        game.text(278, 248, f"현재 시세 · {market_name} ({state.market_remaining:.0f}초)", 15, MUTED)
        order = state.current_order
        if order is None:
            game.text(278, 534, "다음 손님을 기다리고 있습니다.", 18, MUTED)
            game.text(340, 380, f"다음 방문까지 {state.next_customer_in:.1f}초", 22, GOLD)
        else:
            game.text(278, 534, f"{CUSTOMER_NAMES[order.customer]}의 주문", 18, MUTED)
            if order.customer != "npc_broker":
                quantity_badge(game, 610, 518, order.quantity, "총", GOLD)
            game.icons[order.customer].draw(870, 430, 152, 152)
            game.text(766, 329, CUSTOMER_NAMES[order.customer], 22)
            for index, (equipment, quantity) in enumerate(order.requirements):
                y = 470 - index * 60
                owned = state.equipment[equipment]
                fill_rect(275, y - 26, 440, 52, (20, 40, 56))
                if owned < quantity:
                    fill_rect(275, y - 26, 3, 52, RED)
                game.icons[equipment].draw(305, y, 42, 42)
                game.text(339, y, EQUIPMENT_NAMES[equipment], 18)
                quantity_pair(game, 495, y - 16, owned, quantity, "요구")
            if order.customer == "npc_broker":
                game.text(278, 465, "코인을 받고 다음 시장 사건을 알려드립니다.", 18)
                game.text(278, 425, f"정보 가격 {INFORMATION_PRICE} 코인", 22, GOLD)
                available, reason = state.information_status(order.identifier)
                game.draw_button(SELL, f"1 정보 {INFORMATION_PRICE} 코인", available)
            else:
                available, reason = state.order_status(order.identifier)
                value = state.sale_value(order)
                game.text(766, 300, f"판매 {value} 코인", 18, GOLD)
                reward, amount = state.rental_reward(order)
                game.text(766, 278, f"대여 {REWARD_NAMES[reward]} {amount}개" if reward != "coins" else f"대여 {amount} 코인", 15, CYAN)
                game.text(766, 256, f"{RENTAL_DURATIONS[order.customer]}초 · 성공률 {RENTAL_SUCCESS_RATE:.0%}", 15, MUTED)
                game.draw_button(SELL, f"1 판매 +{value} 코인", available)
                game.draw_button(RENT, "2 대여하기", available)
            if reason and not game.feedback:
                game.text(278, 224, reason, 15, GOLD)
            game.draw_button(DECLINE, "3  거절하기")
        if state.known_next_event:
            game.text(278, 125, f"구매한 정보 · 다음은 {state.known_next_event}", 15, CYAN)
        if game.feedback:
            game.text(278, 224, game.feedback, 15, CYAN if game.feedback_success else GOLD)

    def draw_rentals(self):
        game, state = self.game, self.game.state
        contracts = self.contracts
        active = sum(contract.status == "active" for contract in contracts)
        success = sum(contract.status == "success" for contract in contracts)
        lost = sum(contract.status == "lost" for contract in contracts)
        game.text(278, 534, f"진행 {active}건 · 성공 {success}건 · 분실 {lost}건", 18, MUTED)
        if not contracts:
            game.text(340, 380, "진행한 대여 계약이 없습니다.", 22, MUTED)
            return
        start = self.selected_contract // 6 * 6
        for index, contract in enumerate(contracts[start:start + 6], start):
            row_y = 478 - (index - start) * 52
            selected = index == self.selected_contract
            fill_rect(275, row_y - 24, 440, 48, (40, 68, 83) if selected else (20, 40, 56))
            if selected:
                fill_rect(275, row_y - 24, 3, 48, CYAN)
            game.icons[contract.order.customer].draw(306, row_y, 42, 42)
            game.text(339, row_y + 8, CUSTOMER_NAMES[contract.order.customer], 18)
            if contract.status == "active":
                status = f"진행 중 · {max(0, contract.due_at - state.clock()):.1f}초"
            else:
                status = "반납 완료" if contract.status == "success" else "장비 분실"
            game.text(339, row_y - 13, status, 15, CYAN if contract.status == "success" else GOLD)
        game.text(278, 125, f"↑ ↓ 항목 선택 · {start // 6 + 1} / {(len(contracts) + 5) // 6}쪽", 15, MUTED)
        contract = contracts[self.selected_contract]
        game.icons[contract.order.customer].draw(870, 430, 152, 152)
        game.text(766, 329, CUSTOMER_NAMES[contract.order.customer], 22)
        status = {"active": "반납 대기", "success": "장비 반환 · 보상 지급", "lost": "장비 분실"}[contract.status]
        game.text(758, 303, status, 18, CYAN if contract.status == "success" else GOLD)
        reward = f"{REWARD_NAMES[contract.reward_item]} {contract.reward_amount}"
        game.text(758, 279, "보상 없음" if contract.status == "lost" else f"보상 · {reward}", 15, MUTED)
        for index, (equipment, quantity) in enumerate(contract.order.requirements):
            game.text(758, 253 - index * 22, f"{EQUIPMENT_NAMES[equipment]} {quantity}개", 15)
        game.text(758, 150, f"계약 성공률 {contract.success_probability:.0%}", 15, MUTED)
