"""Shared colours and SDL rectangle drawing for workshop panels."""

import ctypes

from pico2d import pico2d as p2
import sdl2

from workshop import EQUIPMENT, MATERIALS, PERSONAL_EQUIPMENT


INK = (12, 24, 38)
CREAM = (248, 239, 218)
MUTED = (193, 209, 219)
CYAN = (103, 236, 210)
GOLD = (244, 190, 101)
RED = (255, 132, 132)


TIER_COLORS = {
    1: (245, 245, 245),
    2: (174, 230, 93),
    3: (80, 157, 255),
    4: (255, 215, 80),
}
GEAR_IMAGES = tuple(entry.image for entry in (*EQUIPMENT, *PERSONAL_EQUIPMENT[:3]))
ITEM_TIERS = {entry.image: 1 for entry in MATERIALS}
ITEM_TIERS.update({image: int(image[-2:]) + 1 for image in GEAR_IMAGES})
ITEM_CATEGORIES = {image: image.split('_')[1] for image in GEAR_IMAGES}
ITEM_CATEGORIES.update({'mat_01': 'parts', 'mat_02': 'composite', 'mat_03': 'circuit'})
CATEGORY_ICON_ASSETS = {category: f'ui_category_{category}.png'
                        for category in ('drill', 'suit', 'oxygen', 'parts', 'composite', 'circuit')}


def fill_rect(x, y, width, height, color, alpha=255):
    sdl2.SDL_SetRenderDrawColor(p2.renderer, *color, alpha)
    rectangle = p2.to_sdl_rect(x, y, width, height)
    sdl2.SDL_RenderFillRect(p2.renderer, ctypes.byref(rectangle))


def draw_item_icon(game, image, x, y, width, height, framed=True):
    """Draw the shared tier frame and top-right equipment category badge."""
    tier = ITEM_TIERS.get(image)
    is_item = tier is not None or image.startswith('item_')
    left, bottom = x - width / 2, y - height / 2
    if framed and is_item:
        fill_rect(left, bottom, width, height, TIER_COLORS.get(tier, (61, 79, 93)))
        fill_rect(left + 2, bottom + 2, width - 4, height - 4, INK)
    padding = 8 if is_item else 0
    game.icons[image].draw(x, y, width - padding, height - padding)
    category = ITEM_CATEGORIES.get(image)
    if category is not None:
        size = max(18, min(48, round(min(width, height) * 0.4)))
        badge_x = left + width - size / 2 - 2
        badge_y = bottom + height - size / 2 - 2
        game.category_icons[category].draw(badge_x, badge_y, size, size)


def quantity_badge(game, x, y, value, label="", color=GOLD, width=100):
    fill_rect(x, y, width, 32, (28, 47, 64))
    fill_rect(x, y, 3, 32, color)
    value_x = x + 10
    if label:
        game.text(x + 10, y + 16, label, 15, MUTED)
        value_x = x + max(46, len(label) * 15 + 20)
    game.text(value_x, y + 16, str(value), 22, color)


def quantity_pair(game, x, y, owned, required, required_label="필요"):
    color = CYAN if owned >= required else RED
    quantity_badge(game, x, y, owned, "보유", color)
    quantity_badge(game, x + 110, y, required, required_label, GOLD)
