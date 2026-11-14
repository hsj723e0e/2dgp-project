"""Recipe selection, ingredient staging, and the workshop crafting screen."""

import ctypes

import sdl2
import sdl2.sdlttf

from game_state import RECIPES
from ui import CREAM, CYAN, GOLD, INK, MUTED, RED, fill_rect
from workshop import EQUIPMENT, HEIGHT, MATERIALS, WIDTH


CLOSE_BUTTON = (1068, 585, 1128, 623)
ACTION_BUTTON = (334, 228, 594, 268)
SURFACE = (23, 38, 51)
BORDER = (61, 79, 93)
MATERIAL_NAMES = {entry.image: entry.name for entry in MATERIALS}


def contains(bounds, x, y):
    left, bottom, right, top = bounds
    return left <= x <= right and bottom <= y <= top


def recipe_bounds(index):
    top = 531 - index * 52
    return (786, top - 46, 1128, top)


def material_bounds(index):
    left = 168 + index * 316
    return (left, 104, left + 300, 170)


def slot_bounds(index):
    left = 260 + index * 204
    return (left, 310, left + 180, 397)


class WorkbenchPanel:
    def __init__(self, game):
        self.game = game
        self.loaded_materials = set()

    def reset(self):
        self.loaded_materials.clear()

    def ingredients(self):
        entry = EQUIPMENT[self.game.selected_entry]
        return RECIPES[entry.image].ingredients

    def load_material(self, material):
        game = self.game
        if game.state.job is not None or material not in self.ingredients():
            return
        required = self.ingredients()[material]
        if game.state.materials[material] < required:
            game.feedback_success = False
            game.feedback = f'{MATERIAL_NAMES[material]}이 부족합니다.'
            return
        self.loaded_materials.add(material)
        game.feedback = ''

    def action_status(self):
        game = self.game
        entry = EQUIPMENT[game.selected_entry]
        if game.state.job is not None:
            return '제작 중', False, ''
        available, reason = game.state.craft_status(entry.image)
        if not available:
            return '제작', False, reason
        if not self.loaded_materials.issuperset(self.ingredients()):
            return '제작', False, '아래 필요 재료를 클릭해 조합 슬롯에 넣으세요.'
        return '제작', True, ''

    def start_craft(self):
        _, available, reason = self.action_status()
        if not available:
            self.game.feedback_success = False
            self.game.feedback = reason
            return
        entry = EQUIPMENT[self.game.selected_entry]
        self.game.feedback_success, self.game.feedback = self.game.state.start_craft(entry.image)

    def handle_key(self, key):
        game = self.game
        if key in (sdl2.SDLK_UP, sdl2.SDLK_w):
            game.select_entry(game.selected_entry - 1)
        elif key in (sdl2.SDLK_DOWN, sdl2.SDLK_s):
            game.select_entry(game.selected_entry + 1)
        elif key in (sdl2.SDLK_1, sdl2.SDLK_2):
            index = key - sdl2.SDLK_1
            materials = tuple(self.ingredients())
            if index < len(materials):
                self.load_material(materials[index])
        elif key == sdl2.SDLK_SPACE:
            self.start_craft()

    def handle_click(self, x, y):
        game = self.game
        if contains(CLOSE_BUTTON, x, y):
            game.close_panel()
            return
        if contains(ACTION_BUTTON, x, y):
            self.start_craft()
            return
        for index in range(len(EQUIPMENT)):
            if contains(recipe_bounds(index), x, y):
                game.select_entry(index)
                return
        for index, material in enumerate(self.ingredients()):
            if contains(material_bounds(index), x, y):
                self.load_material(material)
                return
            if contains(slot_bounds(index), x, y) and game.state.job is None:
                self.loaded_materials.discard(material)
                game.feedback = ''
                return

    def button(self, bounds, label, enabled=True, primary=False):
        game = self.game
        left, bottom, right, top = bounds
        hovered = contains(bounds, *game.mouse)
        fill_rect(left, bottom, right - left, top - bottom, GOLD if primary and enabled else BORDER)
        background = (91, 73, 40) if hovered and enabled else (61, 51, 34)
        if not primary or not enabled:
            background = (42, 59, 72) if hovered and enabled else SURFACE
        fill_rect(left + 1, bottom + 1, right - left - 2, top - bottom - 2, background)
        width, height = ctypes.c_int(), ctypes.c_int()
        sdl2.sdlttf.TTF_SizeUTF8(game.fonts[18].font, label.encode('utf-8'),
                               ctypes.byref(width), ctypes.byref(height))
        game.text((left + right - width.value) / 2, (bottom + top) / 2,
                  label, 18, GOLD if primary and enabled else MUTED)

    def draw(self):
        game = self.game
        state = game.state
        entry = EQUIPMENT[game.selected_entry]
        recipe = RECIPES[entry.image]
        current_job = state.job is not None and state.job.equipment == entry.image
        fill_rect(0, 44, WIDTH, HEIGHT - 44, INK, 200)
        fill_rect(130, 72, 1032, 562, (4, 12, 20), 180)
        fill_rect(124, 78, 1032, 562, BORDER)
        fill_rect(125, 79, 1030, 560, INK)
        fill_rect(125, 574, 1030, 65, SURFACE)
        fill_rect(152, 595, 4, 25, GOLD)
        game.text(172, 608, '작업대', 30)
        self.button(CLOSE_BUTTON, '닫기')

        # Output sits above the ingredient slots, with the recipe browser on its right.
        fill_rect(386, 459, 136, 106, BORDER)
        fill_rect(387, 460, 134, 104, SURFACE)
        game.icons[entry.image].draw(454, 512, 96, 96)
        game.text(327, 437, entry.name, 26)
        count = len(self.ingredients()) if current_job else len(self.loaded_materials)
        game.text(279, 415, f'조합 재료  {count} / {len(recipe.ingredients)}', 18, MUTED)
        for index, (material, required) in enumerate(recipe.ingredients.items()):
            left, bottom, right, top = slot_bounds(index)
            loaded = current_job or material in self.loaded_materials
            fill_rect(left, bottom, right - left, top - bottom, CYAN if loaded else BORDER)
            fill_rect(left + 1, bottom + 1, right - left - 2, top - bottom - 2, SURFACE)
            if loaded:
                game.icons[material].draw((left + right) / 2, 365, 48, 48)
                game.text(left + 13, 327, f'{MATERIAL_NAMES[material]}  ×{required}', 15, CYAN)
            else:
                game.text(left + 65, 366, '+', 26, BORDER)
                game.text(left + 65, 334, f'재료 {index + 1}', 15, MUTED)
        if state.job is None:
            game.text(369, 287, f'제작 시간  {recipe.seconds}초', 18, GOLD)
        else:
            job = next(item for item in EQUIPMENT if item.image == state.job.equipment)
            game.text(260, 287, f'{job.name} 제작 중 · {state.remaining:.1f}초', 18, GOLD)
            progress = 1 - state.remaining / RECIPES[state.job.equipment].seconds
            fill_rect(260, 276, 384, 3, SURFACE)
            fill_rect(260, 276, 384 * max(0, min(1, progress)), 3, GOLD)
        label, available, reason = self.action_status()
        self.button(ACTION_BUTTON, label, available, primary=True)
        message = game.feedback if state.job is None and game.feedback else reason
        if state.job is not None:
            message = '완성품은 자동으로 회수됩니다.'
        color = MUTED
        if game.feedback:
            color = CYAN if game.feedback_success else RED
        game.text(168, 211, message, 15, color)

        fill_rect(764, 224, 1, 334, BORDER)
        game.text(790, 551, '제작 목록', 18)
        game.text(1059, 551, '보유', 15, GOLD)
        for index, item in enumerate(EQUIPMENT):
            left, bottom, right, top = recipe_bounds(index)
            selected = index == game.selected_entry
            hovered = contains(recipe_bounds(index), *game.mouse)
            fill_rect(left, bottom, right - left, top - bottom,
                      (36, 61, 70) if selected else SURFACE)
            if selected or hovered:
                fill_rect(left, bottom, 3, top - bottom, GOLD if selected else BORDER)
            game.icons[item.image].draw(left + 28, bottom + 23, 40, 40)
            game.text(left + 59, bottom + 23, item.name, 18, GOLD if selected else CREAM)
            fill_rect(1052, bottom + 8, 64, 30, INK)
            game.text(1061, bottom + 23, str(state.equipment[item.image]), 18, GOLD)

        # Only the selected recipe's materials are offered in the bottom strip.
        fill_rect(152, 195, 976, 1, BORDER)
        game.text(168, 184, '필요 재료', 18)
        game.text(317, 184, '클릭해 투입 · 슬롯을 클릭하면 해제', 15, MUTED)
        for index, (material, required) in enumerate(recipe.ingredients.items()):
            left, bottom, right, top = material_bounds(index)
            owned = state.materials[material]
            loaded = current_job or material in self.loaded_materials
            enough = owned >= required
            color = CYAN if enough else RED
            hovered = contains(material_bounds(index), *game.mouse)
            fill_rect(left, bottom, right - left, top - bottom, BORDER if loaded or hovered else SURFACE)
            fill_rect(left + 1, bottom + 1, right - left - 2, top - bottom - 2, SURFACE)
            game.icons[material].draw(left + 33, bottom + 34, 48, 48)
            game.text(left + 68, bottom + 46, f'{index + 1}  {MATERIAL_NAMES[material]}', 18)
            game.text(left + 68, bottom + 19, f'보유 {owned}', 18, color)
            game.text(left + 190, bottom + 19, f'/ 필요 {required}', 18, GOLD)
        game.text(831, 143, '제작 완료 시 자동 회수', 18, CYAN)
        game.text(831, 116, '재료는 제작 시작 시 사용', 15, MUTED)
