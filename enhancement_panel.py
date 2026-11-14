"""Basic equipment enhancement and personal equipment at the enhancement station."""

import sdl2

from customer_board import contains
from game_state import MAX_ENHANCEMENT, PERSONAL_CHIP_COST, PERSONAL_CORE_COST, basic_upgrade_cost
from inventory_panel import draw_grid, slot_bounds
from ui import draw_item_icon, CYAN, GOLD, INK, MUTED, fill_rect, quantity_badge, quantity_pair
from workshop import EQUIPMENT, PERSONAL_EQUIPMENT, WIDTH, HEIGHT


MODES = ("basic", "personal", "materials")
TABS = ((275, 520, 503, 554), (526, 520, 754, 554), (777, 520, 1005, 554))
CLOSE = (280, 116, 520, 180)
ACTION = (708, 116, 948, 180)
BASIC_INVENTORY_ORIGIN = (308, 472)


class EnhancementPanel:
    def __init__(self, game):
        self.game = game
        self.reset()

    def reset(self):
        self.mode = "basic"
        self.selected_entry = 0
        self.selected_unit_id = None

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
        for equipment in EQUIPMENT:
            for unit in self.game.state.available_units(equipment.image):
                if unit.identifier == self.selected_unit_id:
                    return unit
        return None

    def select_mode(self, mode):
        self.mode = mode
        self.selected_entry = 0
        self.selected_unit_id = None
        self.game.feedback = ""

    def select_entry(self, index):
        self.selected_entry = index % len(self.entries)
        self.selected_unit_id = None
        self.game.feedback = ""

    def handle_key(self, key):
        if key == sdl2.SDLK_TAB:
            self.select_mode(MODES[(MODES.index(self.mode) + 1) % len(MODES)])
        elif self.mode != "basic" and key in (sdl2.SDLK_UP, sdl2.SDLK_w):
            self.select_entry(self.selected_entry - 1)
        elif self.mode != "basic" and key in (sdl2.SDLK_DOWN, sdl2.SDLK_s):
            self.select_entry(self.selected_entry + 1)
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
            if self.mode == "basic":
                for index, item in enumerate(self.game.state.inventory_items()):
                    if contains(slot_bounds(BASIC_INVENTORY_ORIGIN, index, 3), x, y):
                        if item.unit_id is not None:
                            self.selected_unit_id = item.unit_id
                            self.game.feedback = ""
                        return
            elif 275 <= x <= 610:
                for index in range(len(self.entries)):
                    row_y = 478 - index * 52
                    if row_y - 24 <= y <= row_y + 24:
                        self.select_entry(index)
                        break

    def perform_action(self):
        if self.mode == "basic":
            unit = self.selected_unit
            if unit is not None:
                self.game.feedback_success, self.game.feedback = self.game.state.enhance_basic(unit.equipment, unit.identifier)
        elif self.mode == "personal":
            state = self.game.state
            action = state.craft_personal if state.personal_equipment[self.entry.image] is None else state.enhance_personal
            self.game.feedback_success, self.game.feedback = action(self.entry.image)

    def draw_note(self, message, color=GOLD):
        fill_rect(280, 48, 720, 32, INK, 245)
        self.game.text(296, 64, message, 15, color)

    def draw_basic(self):
        game, state = self.game, self.game.state
        items = state.inventory_items()
        game.text(278, 493, "캐릭터 인벤토리", 18, MUTED)
        game.text(535, 493, f"{len(items)} / 9", 22, GOLD)
        draw_grid(game, BASIC_INVENTORY_ORIGIN, items, 3, 3,
                  selected_unit_id=self.selected_unit_id)
        game.text(278, 255, "강화할 장비를 클릭하세요.", 18, MUTED)
        unit = self.selected_unit
        if unit is None:
            game.text(654, 380, "가방에서 장비를 선택하세요.", 22, MUTED)
            game.draw_button(ACTION, "코인으로 강화", False)
            return
        entry = next(entry for entry in EQUIPMENT if entry.image == unit.equipment)
        draw_item_icon(game, unit.equipment, 816, 428, 144, 144)
        game.text(654, 329, entry.name, 22)
        quantity_badge(game, 654, 279, f"+{unit.level}", "현재", CYAN, 144)
        maximum = unit.level == MAX_ENHANCEMENT
        quantity_badge(game, 850, 279, f"+{min(MAX_ENHANCEMENT, unit.level + 1)}", "최대" if maximum else "다음", GOLD, 144)
        if maximum:
            game.text(654, 237, "최대 강화 +13", 18, GOLD)
        else:
            game.text(654, 237, "강화 비용", 18, MUTED)
            fill_rect(755, 218, 112, 36, (53, 45, 30))
            game.text(769, 237, str(basic_upgrade_cost(unit)), 26, GOLD)
            game.text(883, 237, "코인", 18, MUTED)
        available, reason = state.basic_upgrade_status(unit.equipment, unit.identifier)
        game.draw_button(ACTION, "코인으로 강화", available)
        if reason and not game.feedback:
            self.draw_note(reason)

    def draw_personal(self):
        game, state = self.game, self.game.state
        level = state.personal_equipment[self.entry.image]
        if level is None:
            game.text(654, 295, "고출력 코어", 15, MUTED)
            quantity_pair(game, 785, 279, state.rewards["item_core"], PERSONAL_CORE_COST)
            game.text(654, 244, "최초 제작 단계 +0", 18, MUTED)
            available, reason = state.personal_craft_status(self.entry.image)
            game.draw_button(ACTION, "최상급 장비 제작", available)
            if reason and not game.feedback:
                game.text(654, 191, reason, 15, GOLD)
        else:
            following = min(MAX_ENHANCEMENT, level + 1)
            quantity_badge(game, 654, 279, f"+{level}", "현재", CYAN, 144)
            maximum = level == MAX_ENHANCEMENT
            quantity_badge(game, 850, 279, f"+{following}", "최대" if maximum else "다음", GOLD, 144)
            if maximum:
                game.text(654, 257, "최대 강화 단계 도달", 18, GOLD)
            else:
                game.text(654, 257, "정밀제어칩", 15, MUTED)
                quantity_pair(game, 785, 241, state.rewards["item_chip"], PERSONAL_CHIP_COST)
            performance = state.personal_performance(self.entry.image)
            next_performance = 100 + following * 10
            performance_label = f"최종 성능 {performance}%" if maximum else f"성능 {performance}% → {next_performance}%"
            game.text(654, 220, performance_label, 18, CYAN)
            available, reason = state.personal_upgrade_status(self.entry.image)
            label = "최대 강화 +13" if level == MAX_ENHANCEMENT else "개인 장비 강화"
            game.draw_button(ACTION, label, available)
            if reason and not game.feedback:
                self.draw_note(reason)

    def draw(self):
        game, state = self.game, self.game.state
        fill_rect(0, 44, WIDTH, HEIGHT - 44, INK, 155)
        game.draw_panel_frame()
        game.text(278, 588, "강화 장치", 30)
        for mode, bounds, label in zip(MODES, TABS, ("기본 장비 강화", "개인 최상급 장비", "성장 재료")):
            game.draw_button(bounds, label, selected=mode == self.mode)
        fill_rect(275, 510, 730, 2, (61, 87, 103))
        if self.mode == "basic":
            self.draw_basic()
            game.draw_button(CLOSE, "돌아가기")
            if game.feedback:
                self.draw_note(game.feedback, CYAN if game.feedback_success else GOLD)
            return
        for index, entry in enumerate(self.entries):
            row_y = 478 - index * 52
            selected = index == self.selected_entry
            fill_rect(275, row_y - 24, 335, 48, (40, 68, 83) if selected else (20, 40, 56))
            if selected:
                fill_rect(275, row_y - 24, 3, 48, CYAN)
            draw_item_icon(game, entry.image, 306, row_y, 42, 42)
            game.text(339, row_y, entry.name, 18, CYAN if selected else MUTED)
            if self.mode == "materials":
                quantity_badge(game, 536, row_y - 16, state.rewards[entry.image], width=64)
            elif self.mode == "personal":
                level = state.personal_equipment[entry.image]
                if level is None:
                    game.text(538, row_y, "미보유", 15, MUTED)
                else:
                    quantity_badge(game, 536, row_y - 16, f"+{level}", color=CYAN, width=64)
        draw_item_icon(game, self.entry.image, 816, 428, 144, 144)
        game.text(654, 329, self.entry.name, 22)
        if self.mode == "personal":
            self.draw_personal()
        else:
            for index, line in enumerate(self.entry.description.split(" · ")):
                game.text(654, 300 - index * 22, line, 15, MUTED)
            if self.mode == "materials":
                quantity_badge(game, 654, 244, state.rewards[self.entry.image], "보유", CYAN, 168)
        game.draw_button(CLOSE, "돌아가기")
        if game.feedback:
            self.draw_note(game.feedback, CYAN if game.feedback_success else GOLD)
