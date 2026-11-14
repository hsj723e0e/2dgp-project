"""Recipe selection, ingredient staging, and the workshop crafting screen."""

import ctypes

import sdl2
import sdl2.sdlttf

from game_state import RECIPES
from ui import draw_item_icon, CREAM, CYAN, GOLD, INK, MUTED, RED, fill_rect
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
    left = 196 + index * 270
    return (left, 310, left + 254, 397)


class WorkbenchPanel:
    def __init__(self, game):
        self.game = game

    @property
    def loaded_materials(self):
        return self.game.state.staged_materials.keys()

    def reset(self):
        self.game.state.clear_craft_materials()

    def ingredients(self):
        entry = EQUIPMENT[self.game.selected_entry]
        return RECIPES[entry.image].ingredients

    def load_material(self, material):
        game = self.game
        entry = EQUIPMENT[game.selected_entry]
        game.feedback_success, game.feedback = game.state.stage_craft_material(entry.image, material)

    def action_status(self):
        game = self.game
        entry = EQUIPMENT[game.selected_entry]
        if game.state.job is not None:
            if game.state.ready_to_collect:
                return '가방 공간 대기', False, ''
            return '제작 중', False, ''
        available, reason = game.state.craft_status(entry.image)
        if not available:
            return '제작', False, reason
        if not all(material in self.loaded_materials for material in self.ingredients()):
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
                game.state.unstage_craft_material(material)
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
        draw_item_icon(game, entry.image, 454, 512, 96, 96)
        for index, (material, required) in enumerate(recipe.ingredients.items()):
            left, bottom, right, top = slot_bounds(index)
            loaded = current_job or material in self.loaded_materials
            border_width = 3 if loaded else 1
            if loaded:
                fill_rect(left - 2, bottom - 2, right - left + 4, top - bottom + 4, (30, 69, 69))
            fill_rect(left, bottom, right - left, top - bottom, CYAN if loaded else BORDER)
            fill_rect(left + border_width, bottom + border_width,
                      right - left - border_width * 2, top - bottom - border_width * 2, SURFACE)
            game.text(left + 14, 378, f'재료 {index + 1}', 15, CYAN if loaded else MUTED)
            draw_item_icon(game, material, left + 31, 343, 42, 42)
            game.text(left + 60, 343, MATERIAL_NAMES[material], 15)
            game.text(left + 178, 343, '×', 18, MUTED)
            fill_rect(left + 199, 325, 43, 35, (53, 45, 30))
            game.text(left + 211, 343, str(required), 26, GOLD)
        if state.job is None:
            game.text(344, 291, '제작 시간', 18, MUTED)
            seconds = str(recipe.seconds)
        else:
            job = next(item for item in EQUIPMENT if item.image == state.job.equipment)
            status = '완성 · 가방 공간 대기' if state.ready_to_collect else '제작 중'
            game.text(196, 291, f'{job.name} {status}', 18, MUTED)
            seconds = f'{state.remaining:.1f}'
            progress = 1 - state.remaining / RECIPES[state.job.equipment].seconds
            fill_rect(260, 273, 384, 3, SURFACE)
            fill_rect(260, 273, 384 * max(0, min(1, progress)), 3, GOLD)
        if not state.ready_to_collect:
            fill_rect(496, 277, 94, 28, (53, 45, 30))
            game.text(507, 291, seconds, 26, GOLD)
            game.text(600, 291, '초', 18, MUTED)
        label, available, _ = self.action_status()
        self.button(ACTION_BUTTON, label, available, primary=True)

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
            draw_item_icon(game, item.image, left + 28, bottom + 23, 40, 40)
            game.text(left + 59, bottom + 23, item.name, 18, GOLD if selected else CREAM)
            fill_rect(1052, bottom + 8, 64, 30, INK)
            game.text(1061, bottom + 23, str(state.equipment[item.image]), 22, GOLD)

        # Only the selected recipe's materials are offered in the bottom strip.
        fill_rect(152, 195, 976, 1, BORDER)
        game.text(168, 184, '필요 재료', 18)
        game.text(317, 184, '클릭해 투입 · 슬롯을 클릭하면 해제', 15, MUTED)
        for index, (material, required) in enumerate(recipe.ingredients.items()):
            left, bottom, right, top = material_bounds(index)
            owned = state.materials[material]
            loaded = current_job or material in self.loaded_materials
            enough = material in self.loaded_materials or owned >= required
            color = CYAN if enough else RED
            hovered = contains(material_bounds(index), *game.mouse)
            fill_rect(left, bottom, right - left, top - bottom, BORDER if loaded or hovered else SURFACE)
            fill_rect(left + 1, bottom + 1, right - left - 2, top - bottom - 2, SURFACE)
            draw_item_icon(game, material, left + 33, bottom + 34, 48, 48)
            game.text(left + 68, bottom + 46, MATERIAL_NAMES[material], 18)
            game.text(left + 68, bottom + 19, '보유', 15, MUTED)
            fill_rect(left + 121, bottom + 5, 90, 29, INK)
            game.text(left + 133, bottom + 20, str(owned), 26, color)
