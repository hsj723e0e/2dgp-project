"""The live customer order panel shown at the workshop's noticeboard."""

import sdl2

from orders import CUSTOMER_NAMES, INFORMATION_PRICE, RENTAL_DURATIONS, RENTAL_SUCCESS_RATE, REWARD_NAMES
from game_state import rental_success_probability
from ui import CREAM, CYAN, GOLD, INK, MUTED, RED, fill_rect, quantity_badge, quantity_pair
from workshop import EQUIPMENT, HEIGHT, WIDTH


CLOSE = (940, 550, 1036, 590)
DECLINE = (785, 140, 1005, 196)
SELL = (275, 140, 495, 196)
RENT = (530, 140, 750, 196)
VIEW_RENTALS = (760, 550, 920, 590)
CONFIRM_UNITS = (275, 120, 495, 176)
CANCEL_UNITS = (785, 120, 1005, 176)
PREVIOUS_UNIT = (708, 211, 780, 243)
NEXT_UNIT = (900, 211, 972, 243)
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
        self.cancel_selection()

    def cancel_selection(self):
        self.unit_action = None
        self.chosen_units = []
        self.selected_slot = 0
        self.selection_order_id = None

    def begin_selection(self, action):
        state = self.game.state
        order = state.current_order
        if order is None:
            return
        available, reason = state.order_status(order.identifier)
        if not available:
            self.game.feedback_success, self.game.feedback = False, reason
            return
        self.unit_action = action
        self.selection_order_id = order.identifier
        self.chosen_units = [unit.identifier for unit in state.order_units(order)]
        self.selected_slot = 0
        self.game.feedback = ""

    def selected_units(self):
        order = self.game.state.current_order
        return self.game.state.order_units(order, tuple(self.chosen_units))

    def change_unit(self, step):
        selected = self.selected_units()[self.selected_slot]
        taken = set(self.chosen_units)
        taken.remove(selected.identifier)
        choices = [unit for unit in self.game.state.available_units(selected.equipment) if unit.identifier not in taken]
        index = next(index for index, unit in enumerate(choices) if unit.identifier == selected.identifier)
        self.chosen_units[self.selected_slot] = choices[(index + step) % len(choices)].identifier

    def confirm_selection(self):
        state = self.game.state
        action = state.sell_order if self.unit_action == "sell" else state.start_rental
        self.game.feedback_success, self.game.feedback = action(self.selection_order_id, tuple(self.chosen_units))
        self.cancel_selection()

    @property
    def contracts(self):
        return list(reversed(self.game.state.rentals))

    def toggle_view(self):
        self.show_rentals = not self.show_rentals
        self.selected_contract = 0

    def handle_key(self, key):
        if self.unit_action:
            if key in (sdl2.SDLK_UP, sdl2.SDLK_w):
                self.selected_slot = (self.selected_slot - 1) % len(self.chosen_units)
            elif key in (sdl2.SDLK_DOWN, sdl2.SDLK_s):
                self.selected_slot = (self.selected_slot + 1) % len(self.chosen_units)
            elif key == sdl2.SDLK_LEFT:
                self.change_unit(-1)
            elif key == sdl2.SDLK_RIGHT:
                self.change_unit(1)
            elif key in (sdl2.SDLK_SPACE, sdl2.SDLK_RETURN):
                self.confirm_selection()
            elif key == sdl2.SDLK_ESCAPE:
                self.cancel_selection()
        elif key == sdl2.SDLK_TAB:
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
        elif self.unit_action:
            if contains(CONFIRM_UNITS, x, y):
                self.confirm_selection()
            elif contains(CANCEL_UNITS, x, y):
                self.cancel_selection()
            elif contains(PREVIOUS_UNIT, x, y):
                self.change_unit(-1)
            elif contains(NEXT_UNIT, x, y):
                self.change_unit(1)
            else:
                for index in range(len(self.chosen_units)):
                    y_center = 470 - index * 60
                    if 275 <= x <= 715 and y_center - 26 <= y <= y_center + 26:
                        self.selected_slot = index
                        break
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
            self.begin_selection("rent")

    def sell(self):
        state = self.game.state
        order = state.current_order
        if order is None:
            return
        if order.customer == "npc_broker":
            self.game.feedback_success, self.game.feedback = state.buy_information(order.identifier)
        else:
            self.begin_selection("sell")

    def decline(self):
        order = self.game.state.current_order
        if order is not None:
            self.game.feedback_success, self.game.feedback = self.game.state.decline_order(order.identifier)

    def draw(self):
        game, state = self.game, self.game.state
        fill_rect(0, 0, WIDTH, HEIGHT, INK, 155)
        game.draw_panel_frame()
        if self.unit_action:
            self.draw_unit_selection()
            return
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
                game.text(766, 256, f"대여 {RENTAL_DURATIONS[order.customer]}초 · 장비 직접 선택", 15, MUTED)
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
        quantity_badge(game, 278, 518, active, "진행", GOLD, 130)
        quantity_badge(game, 428, 518, success, "성공", CYAN, 130)
        quantity_badge(game, 578, 518, lost, "분실", RED, 130)
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
        if contract.status == "lost":
            game.text(758, 279, "보상 없음", 18, RED)
        else:
            game.text(758, 279, REWARD_NAMES[contract.reward_item], 18, MUTED)
            quantity_badge(game, 940, 263, contract.reward_amount, color=CYAN, width=64)
        for index, (equipment, quantity) in enumerate(contract.order.requirements):
            y = 237 - index * 34
            game.text(758, y + 16, EQUIPMENT_NAMES[equipment], 15)
            quantity_badge(game, 940, y, quantity, color=GOLD, width=64)
        game.text(758, 118, f"계약 성공률 {contract.success_probability:.1%}", 15, MUTED)

    def draw_unit_selection(self):
        game = self.game
        units = self.selected_units()
        title = "판매 장비 선택" if self.unit_action == "sell" else "대여 장비 선택"
        game.text(278, 572, title, 30)
        game.text(278, 534, "↑ ↓ 요청 항목 선택 · ← → 사용할 장비 선택", 18, MUTED)
        game.draw_button(CLOSE, "닫기")
        fill_rect(275, 510, 730, 2, (61, 87, 103))
        for index, unit in enumerate(units):
            y = 470 - index * 60
            selected = index == self.selected_slot
            fill_rect(275, y - 26, 440, 52, (40, 68, 83) if selected else (20, 40, 56))
            game.icons[unit.equipment].draw(305, y, 42, 42)
            game.text(339, y, EQUIPMENT_NAMES[unit.equipment], 18)
            quantity_badge(game, 594, y - 16, f"+{unit.level}", color=CYAN, width=110)
        unit = units[self.selected_slot]
        game.icons[unit.equipment].draw(816, 428, 144, 144)
        game.text(654, 329, EQUIPMENT_NAMES[unit.equipment], 22)
        quantity_badge(game, 654, 279, f"+{unit.level}", "강화", CYAN, 160)
        available = game.state.available_units(unit.equipment)
        position = next(index for index, item in enumerate(available) if item.identifier == unit.identifier) + 1
        game.text(654, 260, f"보유 장비 {position} / {len(available)}", 18, MUTED)
        game.draw_button(PREVIOUS_UNIT, "←")
        game.draw_button(NEXT_UNIT, "→")
        if self.unit_action == "rent":
            game.text(654, 190, f"선택 장비 성공률 {rental_success_probability(units):.1%}", 18, GOLD)
        game.draw_button(CONFIRM_UNITS, "선택 확정")
        game.draw_button(CANCEL_UNITS, "취소")
