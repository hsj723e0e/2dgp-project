"""Workbench recipe browser and crafting status panel."""

import ctypes

import sdl2.sdlttf

from game_state import RECIPES
from ui import CREAM, CYAN, GOLD, INK, MUTED, RED, fill_rect
from workshop import EQUIPMENT, HEIGHT, MATERIALS, WIDTH


CLOSE_BUTTON = (1034, 586, 1094, 624)
ACTION_BUTTON = (816, 108, 1088, 158)
SURFACE = (21, 37, 50)
BORDER = (53, 76, 90)


class WorkbenchPanel:
    def __init__(self, game):
        self.game = game

    def handle_click(self, x, y):
        if CLOSE_BUTTON[0] <= x <= CLOSE_BUTTON[2] and CLOSE_BUTTON[1] <= y <= CLOSE_BUTTON[3]:
            self.game.close_panel()
        elif ACTION_BUTTON[0] <= x <= ACTION_BUTTON[2] and ACTION_BUTTON[1] <= y <= ACTION_BUTTON[3]:
            if self.game.panel_action()[1]:
                self.game.perform_action()
        elif 192 <= x <= 524:
            for index in range(len(EQUIPMENT)):
                top = 527 - index * 52
                if top - 46 <= y <= top:
                    self.game.select_entry(index)
                    break

    def button(self, bounds, label, enabled=True, primary=False):
        game = self.game
        left, bottom, right, top = bounds
        hovered = left <= game.mouse[0] <= right and bottom <= game.mouse[1] <= top
        color = CYAN if primary and enabled else BORDER
        fill_rect(left, bottom, right - left, top - bottom, color)
        background = (38, 83, 83) if hovered and enabled else (27, 57, 63)
        if not primary or not enabled:
            background = (42, 59, 72) if hovered and enabled else SURFACE
        fill_rect(left + 1, bottom + 1, right - left - 2, top - bottom - 2, background)
        # Keep button labels centred using the actual Korean font width.
        width, height = ctypes.c_int(), ctypes.c_int()
        sdl2.sdlttf.TTF_SizeUTF8(game.fonts[18].font, label.encode('utf-8'),
                               ctypes.byref(width), ctypes.byref(height))
        game.text((left + right - width.value) / 2, (bottom + top) / 2,
                  label, 18, CREAM if enabled else MUTED)

    def draw(self):
        game = self.game
        state = game.state
        entry = EQUIPMENT[game.selected_entry]
        recipe = RECIPES[entry.image]
        fill_rect(0, 44, WIDTH, HEIGHT - 44, INK, 200)
        fill_rect(169, 77, 950, 560, (4, 12, 20), 180)
        fill_rect(164, 84, 952, 558, BORDER)
        fill_rect(165, 85, 950, 556, INK)
        fill_rect(165, 574, 950, 67, SURFACE)
        fill_rect(192, 595, 4, 25, CYAN)
        game.text(212, 609, '작업대', 30)
        game.text(360, 607, '장비 제작', 18, MUTED)
        self.button(CLOSE_BUTTON, '닫기')

        game.text(194, 550, '제작 목록', 18, MUTED)
        game.text(437, 550, '보유', 15, MUTED)
        for index, item in enumerate(EQUIPMENT):
            top = 527 - index * 52
            selected = index == game.selected_entry
            hovered = 192 <= game.mouse[0] <= 524 and top - 46 <= game.mouse[1] <= top
            fill_rect(192, top - 46, 332, 46, (33, 64, 74) if selected else SURFACE)
            if selected or hovered:
                fill_rect(192, top - 46, 3, 46, CYAN if selected else BORDER)
            game.icons[item.image].draw(220, top - 23, 40, 40)
            game.text(249, top - 23, item.name, 18, CYAN if selected else CREAM)
            fill_rect(438, top - 36, 72, 27, INK)
            game.text(450, top - 23, str(state.equipment[item.image]), 18, GOLD)
        fill_rect(544, 209, 1, 347, BORDER)

        # Large preview and concise item metadata.
        fill_rect(570, 411, 118, 136, SURFACE)
        game.icons[entry.image].draw(629, 481, 108, 108)
        tier = '초급 장비' if entry.image.endswith('_01') else '중급 장비'
        game.text(710, 533, tier, 15, CYAN)
        game.text(710, 496, entry.name, 26)
        game.text(710, 458, f'제작 시간  {recipe.seconds}초', 18, MUTED)
        game.text(710, 425, f'완성 수량  1개    ·    보유  {state.equipment[entry.image]}개', 18, GOLD)
        fill_rect(570, 391, 518, 1, BORDER)
        game.text(574, 370, '필요 재료', 18)
        game.text(882, 370, '보유 / 필요', 15, MUTED)
        names = {material.image: material.name for material in MATERIALS}
        for index, (material, required) in enumerate(recipe.ingredients.items()):
            y = 315 - index * 64
            owned = state.materials[material]
            enough = owned >= required
            color = CYAN if enough else RED
            fill_rect(570, y - 23, 518, 54, SURFACE)
            game.icons[material].draw(599, y + 4, 42, 42)
            game.text(634, y + 4, names[material], 18)
            game.text(887, y + 4, str(owned), 22, color)
            game.text(957, y + 4, '/', 18, MUTED)
            game.text(987, y + 4, str(required), 22, GOLD)
            fill_rect(1085, y - 23, 3, 54, color)

        # Current job always shows its own item, even while browsing other recipes.
        fill_rect(192, 174, 896, 1, BORDER)
        if state.job is not None:
            job_entry = next(item for item in EQUIPMENT if item.image == state.job.equipment)
            ready = state.ready_to_collect
            color = CYAN if ready else GOLD
            game.icons[job_entry.image].draw(218, 133, 46, 46)
            game.text(254, 147, job_entry.name, 18)
            status = '제작 완료 · 완성품을 회수하세요' if ready else f'제작 중 · 남은 시간 {state.remaining:.1f}초'
            game.text(445, 147, status, 15, color)
            progress = 1 - state.remaining / RECIPES[state.job.equipment].seconds
            fill_rect(254, 118, 520, 7, SURFACE)
            fill_rect(254, 118, 520 * max(0, min(1, progress)), 7, color)
        else:
            available, reason = state.craft_status(entry.image)
            message = '재료가 준비되었습니다' if available else reason
            game.text(194, 145, message, 18, CYAN if available else RED)
            game.text(194, 117, '완성된 장비는 작업대에서 직접 회수합니다.', 15, MUTED)
        label, enabled, _ = game.panel_action()
        self.button(ACTION_BUTTON, label, enabled, primary=True)
        if game.feedback and state.job is None:
            fill_rect(192, 187, 896, 29, SURFACE)
            game.text(204, 202, game.feedback, 15, CYAN if game.feedback_success else RED)
