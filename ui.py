"""Shared colours and SDL rectangle drawing for workshop panels."""

import ctypes

from pico2d import pico2d as p2
import sdl2
import sdl2.sdlimage

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
ITEM_CATEGORIES.update({entry.image: 'parts' for entry in MATERIALS})
CATEGORY_ICON_ASSETS = {category: f'ui_category_{category}.png'
                        for category in ('drill', 'suit', 'oxygen', 'parts')}


def fill_rect(x, y, width, height, color, alpha=255):
    sdl2.SDL_SetRenderDrawColor(p2.renderer, *color, alpha)
    rectangle = p2.to_sdl_rect(x, y, width, height)
    sdl2.SDL_RenderFillRect(p2.renderer, ctypes.byref(rectangle))


def grayscale_color(color):
    value = (77 * color[0] + 150 * color[1] + 29 * color[2]) // 256
    return (value, value, value)


def load_grayscale_image(path):
    """Build a grayscale SDL texture once while retaining the source alpha."""
    source = sdl2.sdlimage.IMG_Load(str(path).encode('utf-8'))
    if not source:
        raise OSError(f'Cannot load image for grayscale display: {path}')
    surface = sdl2.SDL_ConvertSurfaceFormat(source, sdl2.SDL_PIXELFORMAT_RGBA32, 0)
    sdl2.SDL_FreeSurface(source)
    if not surface:
        raise OSError('Cannot convert image to RGBA')
    try:
        if sdl2.SDL_LockSurface(surface) != 0:
            raise OSError('Cannot lock grayscale image surface')
        try:
            info = surface.contents
            pixels = (ctypes.c_uint8 * (info.pitch * info.h)).from_address(info.pixels)
            for y in range(info.h):
                for x in range(info.w):
                    offset = y * info.pitch + x * 4
                    value = (77 * pixels[offset] + 150 * pixels[offset + 1] + 29 * pixels[offset + 2]) // 256
                    pixels[offset] = pixels[offset + 1] = pixels[offset + 2] = value
        finally:
            sdl2.SDL_UnlockSurface(surface)
        texture = sdl2.SDL_CreateTextureFromSurface(p2.renderer, surface)
        if not texture:
            raise OSError('Cannot create grayscale image texture')
        return p2.Image(texture)
    finally:
        sdl2.SDL_FreeSurface(surface)


def draw_item_icon(game, image, x, y, width, height, framed=True, grayscale=False):
    """Draw the shared tier frame and top-right equipment category badge."""
    tier = ITEM_TIERS.get(image)
    is_item = tier is not None or image.startswith('item_')
    left, bottom = x - width / 2, y - height / 2
    if framed and is_item:
        border = TIER_COLORS.get(tier, (61, 79, 93))
        background = INK
        if grayscale:
            border = grayscale_color(border)
            background = grayscale_color(background)
        fill_rect(left, bottom, width, height, border)
        fill_rect(left + 2, bottom + 2, width - 4, height - 4, background)
    padding = 8 if is_item else 0
    icons = game.grayscale_icons if grayscale else game.icons
    icons[image].draw(x, y, width - padding, height - padding)
    category = ITEM_CATEGORIES.get(image)
    if category is not None:
        size = max(18, min(48, round(min(width, height) * 0.4)))
        badge_x = left + width - size / 2 - 2
        badge_y = bottom + height - size / 2 - 2
        badges = game.grayscale_category_icons if grayscale else game.category_icons
        badges[category].draw(badge_x, badge_y, size, size)


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
