"""Character backpack and equipment-specific chest screens."""

import sdl2

from ui import CREAM, CYAN, GOLD, INK, MUTED, RED, fill_rect
from workshop import EQUIPMENT, HEIGHT, MATERIALS, PERSONAL_EQUIPMENT, RESOURCE_ITEMS, WIDTH


ITEM_NAMES = {entry.image: entry.name for entry in (*EQUIPMENT, *MATERIALS, *PERSONAL_EQUIPMENT)}
SLOT_SIZE = 60
SLOT_STEP = 64
BAG_ORIGIN = (544, 482)
STORAGE_BAG_ORIGIN = (878, 500)
CHEST_ORIGIN = (394, 500)
CLOSE_BAG = (504, 152, 776, 200)
CLOSE_STORAGE = (1035, 566, 1155, 610)
SURFACE = (23, 38, 51)
BORDER = (61, 79, 93)


def contains(bounds, x, y):
    left, bottom, right, top = bounds
    return left <= x <= right and bottom <= y <= top


def slot_bounds(origin, index, columns):
    left, top = origin
    x = left + (index % columns) * SLOT_STEP
    y = top - (index // columns) * SLOT_STEP
    return (x, y - SLOT_SIZE, x + SLOT_SIZE, y)


def storage_recipe_bounds(index):
    top = 510 - index * 52
    return (116, top - 46, 366, top)


def draw_grid(game, origin, items, columns, rows, selected_unit_id=None,
              selected_unit_ids=(), eligible_unit_ids=None):
    hovered = None
    selected_ids = set(selected_unit_ids)
    if selected_unit_id is not None:
        selected_ids.add(selected_unit_id)
    for index in range(columns * rows):
        bounds = slot_bounds(origin, index, columns)
        left, bottom, right, top = bounds
        disabled = (index < len(items) and eligible_unit_ids is not None
                    and items[index].unit_id not in eligible_unit_ids)
        active = contains(bounds, *game.mouse) and not disabled
        selected = (index < len(items) and items[index].unit_id is not None
                    and items[index].unit_id in selected_ids)
        color = CYAN if active else BORDER
        border_width = 1
        if selected:
            color = GOLD
            border_width = 3
        fill_rect(left, bottom, SLOT_SIZE, SLOT_SIZE, color)
        fill_rect(left + border_width, bottom + border_width,
                  SLOT_SIZE - border_width * 2, SLOT_SIZE - border_width * 2, SURFACE)
        if index >= len(items):
            continue
        item = items[index]
        game.icons[item.image].draw(left + 30, bottom + 33, 44, 44)
        if item.level is not None:
            fill_rect(left + 23, bottom + 2, 35, 20, INK)
            game.text(left + 27, bottom + 12, f'+{item.level}', 15, GOLD)
        else:
            fill_rect(left + 5, bottom + 2, 53, 20, INK)
            game.text(left + 9, bottom + 12, str(item.quantity), 22 if item.quantity < 1000 else 15, CYAN)
        if disabled:
            fill_rect(left + 1, bottom + 1, SLOT_SIZE - 2, SLOT_SIZE - 2, INK, 190)
        if active:
            hovered = item
    return hovered


class InventoryPanel:
    def __init__(self, game):
        self.game = game

    def handle_click(self, x, y):
        if contains(CLOSE_BAG, x, y):
            self.game.close_panel()

    def draw(self):
        game = self.game
        items = game.state.inventory_items()
        fill_rect(0, 44, WIDTH, HEIGHT - 44, INK, 190)
        fill_rect(438, 131, 404, 451, BORDER)
        fill_rect(439, 132, 402, 449, INK)
        game.text(477, 540, '캐릭터 인벤토리', 26)
        game.text(544, 509, f'{len(items)} / 9', 22, GOLD)
        hovered = draw_grid(game, BAG_ORIGIN, items, 3, 3)
        if hovered:
            game.text(477, 254, ITEM_NAMES[hovered.image], 18)
            if hovered.level is not None:
                game.text(477, 224, f'강화 +{hovered.level}', 18, GOLD)
            else:
                game.text(477, 224, f'보유 {hovered.quantity}', 18, CYAN)
        game.draw_button(CLOSE_BAG, '닫기')


class StoragePanel:
    def __init__(self, game):
        self.game = game

    def handle_key(self, key):
        if key in (sdl2.SDLK_UP, sdl2.SDLK_w):
            self.game.select_entry(self.game.selected_entry - 1)
        elif key in (sdl2.SDLK_DOWN, sdl2.SDLK_s):
            self.game.select_entry(self.game.selected_entry + 1)

    def handle_click(self, x, y, quantity=1, button=sdl2.SDL_BUTTON_LEFT):
        game = self.game
        if button == sdl2.SDL_BUTTON_LEFT and contains(CLOSE_STORAGE, x, y):
            game.close_panel()
            return
        for index in range(len(EQUIPMENT)):
            if button == sdl2.SDL_BUTTON_LEFT and contains(storage_recipe_bounds(index), x, y):
                game.select_entry(index)
                return
        equipment = EQUIPMENT[game.selected_entry].image
        for index, item in enumerate(game.state.inventory_items()):
            if contains(slot_bounds(STORAGE_BAG_ORIGIN, index, 3), x, y):
                game.feedback_success, game.feedback = game.state.store_equipment(equipment, item.unit_id, quantity)
                return
        for index, item in enumerate(game.state.chest_items(equipment)):
            if contains(slot_bounds(CHEST_ORIGIN, index, 7), x, y):
                game.feedback_success, game.feedback = game.state.withdraw_equipment(equipment, item.unit_id, quantity)
                return

    def draw(self):
        game = self.game
        state = game.state
        entry = EQUIPMENT[game.selected_entry]
        bag = state.inventory_items()
        chest = state.chest_items(entry.image)
        fill_rect(0, 44, WIDTH, HEIGHT - 44, INK, 190)
        fill_rect(90, 90, 1100, 545, BORDER)
        fill_rect(91, 91, 1098, 543, INK)
        game.text(116, 591, '장비 진열대', 30)
        game.draw_button(CLOSE_STORAGE, '닫기')
        fill_rect(116, 551, 1039, 1, BORDER)
        for index, equipment in enumerate(EQUIPMENT):
            left, bottom, right, top = storage_recipe_bounds(index)
            selected = index == game.selected_entry
            fill_rect(left, bottom, right - left, top - bottom, (36, 61, 70) if selected else SURFACE)
            if selected:
                fill_rect(left, bottom, 3, top - bottom, CYAN)
            game.icons[equipment.image].draw(left + 27, bottom + 23, 40, 40)
            game.text(left + 53, bottom + 23, equipment.name, 18, CYAN if selected else CREAM)
            fill_rect(right - 43, bottom + 8, 38, 30, INK)
            game.text(right - 37, bottom + 23, str(len(state.storage_units[equipment.image])), 22, GOLD)
        game.text(394, 530, entry.name + ' 보관함', 22)
        game.text(730, 530, f'{len(chest)} / 28', 18, GOLD)
        game.text(878, 530, '가방', 22)
        game.text(1001, 530, f'{len(bag)} / 9', 18, GOLD)
        hovered = draw_grid(game, CHEST_ORIGIN, chest, 7, 4)
        bag_hovered = draw_grid(game, STORAGE_BAG_ORIGIN, bag, 3, 3)
        if bag_hovered is not None:
            hovered = bag_hovered
        game.text(394, 224, '좌클릭 1개 · 우클릭 10개 · Shift+클릭 전체', 18, MUTED)
        game.text(878, 278, '가방 장비만 판매·대여', 15, MUTED)
        if hovered is not None:
            game.text(394, 185, ITEM_NAMES[hovered.image], 18)
            if hovered.level is not None:
                game.text(650, 185, f'강화 +{hovered.level}', 18, GOLD)
        if game.feedback:
            game.text(394, 143, game.feedback, 18, CYAN if game.feedback_success else RED)


def resource_slot_bounds(index):
    left = 158 + (index % 3) * 184
    top = 500 - (index // 3) * 164
    return (left, top - 96, left + 96, top)


class MaterialStoragePanel:
    def __init__(self, game):
        self.game = game

    def handle_click(self, x, y, quantity=1, button=sdl2.SDL_BUTTON_LEFT):
        game = self.game
        if button == sdl2.SDL_BUTTON_LEFT and contains(CLOSE_STORAGE, x, y):
            game.close_panel()
            return
        for index, entry in enumerate(RESOURCE_ITEMS):
            if contains(resource_slot_bounds(index), x, y):
                game.feedback_success, game.feedback = game.state.withdraw_resource(entry.image, quantity)
                return
        for index, item in enumerate(game.state.inventory_items()):
            if contains(slot_bounds(STORAGE_BAG_ORIGIN, index, 3), x, y):
                game.feedback_success, game.feedback = game.state.store_resource(item.image, quantity)
                return

    def draw(self):
        game, state = self.game, self.game.state
        bag = state.inventory_items()
        fill_rect(0, 44, WIDTH, HEIGHT - 44, INK, 190)
        fill_rect(90, 90, 1100, 545, BORDER)
        fill_rect(91, 91, 1098, 543, INK)
        game.text(116, 591, '재료 보관대', 30)
        game.draw_button(CLOSE_STORAGE, '닫기')
        fill_rect(116, 551, 1039, 1, BORDER)
        for index, entry in enumerate(RESOURCE_ITEMS):
            left, bottom, right, top = resource_slot_bounds(index)
            quantity = state.resource_storage[entry.image]
            hovered = contains((left, bottom, right, top), *game.mouse)
            color = CYAN if quantity else BORDER
            if hovered:
                color = GOLD
            fill_rect(left, bottom, right - left, top - bottom, color)
            fill_rect(left + 2, bottom + 2, right - left - 4, top - bottom - 4, SURFACE)
            game.text(left - 12, top + 23, entry.name, 18)
            game.icons[entry.image].draw(left + 48, bottom + 55, 64, 64)
            fill_rect(left + 8, bottom + 4, 80, 27, INK)
            game.text(left + 19, bottom + 18, str(quantity), 22 if quantity < 10000 else 15, CYAN if quantity else MUTED)
        fill_rect(790, 220, 1, 310, BORDER)
        game.text(878, 530, '가방', 22)
        game.text(1001, 530, f'{len(bag)} / 9', 18, GOLD)
        hovered = draw_grid(game, STORAGE_BAG_ORIGIN, bag, 3, 3)
        if hovered:
            game.text(878, 280, ITEM_NAMES[hovered.image], 18)
        game.text(158, 195, '좌클릭 1개 · 우클릭 10개 · Shift+클릭 전체', 18, MUTED)
        if game.feedback:
            game.text(158, 143, game.feedback, 18, CYAN if game.feedback_success else RED)
