"""Basic equipment enhancement and personal equipment at the enhancement station."""

import sdl2

from customer_board import contains
from game_state import MAX_ENHANCEMENT, basic_upgrade_cost, rental_success_probability
from ui import CYAN, GOLD, INK, MUTED, fill_rect, quantity_badge
from workshop import EQUIPMENT, PERSONAL_EQUIPMENT, WIDTH, HEIGHT


MODES = ("basic", "personal", "materials")
TABS = ((275, 520, 503, 554), (526, 520, 754, 554), (777, 520, 1005, 554))
CLOSE = (280, 116, 520, 180)
ACTION = (708, 116, 948, 180)
PREVIOUS_UNIT = (708, 185, 780, 217)
NEXT_UNIT = (900, 185, 972, 217)


class EnhancementPanel:
    def __init__(self, game):
        self.game = game
        self.reset()

    def reset(self):
        self.mode = "basic"
        self.selected_entry = 0
        self.unit_index = 0

    @property
    def entries(self):
        if self.mode == "basic":
            return EQUIPMENT
        if self.mode == "personal":
            return PERSONAL_EQUIPMENT[:3]
        return PERSONAL_EQUIPMENT[3:]

    @property
    def entry(self):
        return self.entries[self.selected_entry]

    @property
    def selected_unit(self):
        units = self.game.state.available_units(self.entry.image)
        return units[self.unit_index % len(units)] if units else None

    def select_mode(self, mode):
        self.mode = mode
        self.selected_entry = self.unit_index = 0
        self.game.feedback = ""

    def select_entry(self, index):
        self.selected_entry = index % len(self.entries)
        self.unit_index = 0
        self.game.feedback = ""

    def handle_key(self, key):
        if key == sdl2.SDLK_TAB:
            self.select_mode(MODES[(MODES.index(self.mode) + 1) % len(MODES)])
        elif key in (sdl2.SDLK_UP, sdl2.SDLK_w):
            self.select_entry(self.selected_entry - 1)
        elif key in (sdl2.SDLK_DOWN, sdl2.SDLK_s):
            self.select_entry(self.selected_entry + 1)
        elif self.mode == "basic" and key == sdl2.SDLK_LEFT:
            self.unit_index -= 1
        elif self.mode == "basic" and key == sdl2.SDLK_RIGHT:
            self.unit_index += 1
        elif key == sdl2.SDLK_SPACE:
            self.perform_action()

    def handle_click(self, x, y):
        if contains(CLOSE, x, y):
            self.game.close_panel()
        elif contains(ACTION, x, y):
            self.perform_action()
        else:
            for mode, bounds in zip(MODES, TABS):
                if contains(bounds, x, y):
                    self.select_mode(mode)
                    return
            if self.mode == "basic" and contains(PREVIOUS_UNIT, x, y):
                self.unit_index -= 1
            elif self.mode == "basic" and contains(NEXT_UNIT, x, y):
                self.unit_index += 1
            elif 275 <= x <= 610:
                for index in range(len(self.entries)):
                    row_y = 478 - index * 52
                    if row_y - 24 <= y <= row_y + 24:
                        self.select_entry(index)
                        break

    def perform_action(self):
        if self.mode == "basic" and self.selected_unit:
            self.game.feedback_success, self.game.feedback = self.game.state.enhance_basic(self.entry.image, self.selected_unit.identifier)

    def draw_basic(self):
        game, state = self.game, self.game.state
        unit = self.selected_unit
        if unit is None:
            game.text(654, 275, "보유 장비가 없습니다.", 22, GOLD)
            game.draw_button(ACTION, "장비 강화", False)
            return
        quantity_badge(game, 654, 279, f"+{unit.level}", "현재", CYAN, 144)
        quantity_badge(game, 850, 279, f"+{min(MAX_ENHANCEMENT, unit.level + 1)}", "다음", GOLD, 144)
        game.text(654, 260, f"강화 비용 {basic_upgrade_cost(unit)} 코인", 18, GOLD)
        current = rental_success_probability((unit,))
        following = min(.98, current + .01)
        game.text(654, 234, f"대여 성공률 {current:.0%} → {following:.0%}", 18, CYAN)
        units = state.available_units(self.entry.image)
        game.draw_button(PREVIOUS_UNIT, "←")
        game.draw_button(NEXT_UNIT, "→")
        game.text(791, 201, f"{self.unit_index % len(units) + 1}/{len(units)}", 18)
        available, reason = state.basic_upgrade_status(self.entry.image, unit.identifier)
        game.draw_button(ACTION, "코인으로 강화", available)
        if reason and not game.feedback:
            game.text(278, 191, reason, 15, GOLD)

    def draw(self):
        game, state = self.game, self.game.state
        fill_rect(0, 0, WIDTH, HEIGHT, INK, 155)
        game.draw_panel_frame()
        game.text(278, 588, "강화 장치", 30)
        for mode, bounds, label in zip(MODES, TABS, ("기본 장비 강화", "개인 최상급 장비", "성장 재료")):
            game.draw_button(bounds, label, selected=mode == self.mode)
        fill_rect(275, 510, 730, 2, (61, 87, 103))
        for index, entry in enumerate(self.entries):
            row_y = 478 - index * 52
            selected = index == self.selected_entry
            fill_rect(275, row_y - 24, 335, 48, (40, 68, 83) if selected else (20, 40, 56))
            if selected:
                fill_rect(275, row_y - 24, 3, 48, CYAN)
            game.icons[entry.image].draw(306, row_y, 42, 42)
            game.text(339, row_y, entry.name, 18, CYAN if selected else MUTED)
            if self.mode == "basic":
                quantity_badge(game, 536, row_y - 16, state.equipment[entry.image], width=64)
            elif self.mode == "materials":
                quantity_badge(game, 536, row_y - 16, state.rewards[entry.image], width=64)
        game.icons[self.entry.image].draw(816, 428, 144, 144)
        game.text(654, 329, self.entry.name, 22)
        if self.mode == "basic":
            self.draw_basic()
        else:
            for index, line in enumerate(self.entry.description.split(" · ")):
                game.text(654, 300 - index * 22, line, 15, MUTED)
            if self.mode == "materials":
                quantity_badge(game, 654, 244, state.rewards[self.entry.image], "보유", CYAN, 168)
        game.draw_button(CLOSE, "돌아가기")
        if game.feedback:
            fill_rect(280, 48, 720, 32, INK, 245)
            game.text(296, 64, game.feedback, 15, CYAN if game.feedback_success else GOLD)
