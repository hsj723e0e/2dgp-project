"""Shared colours and SDL rectangle drawing for workshop panels."""

import ctypes

from pico2d import pico2d as p2
import sdl2


INK = (12, 24, 38)
CREAM = (248, 239, 218)
MUTED = (193, 209, 219)
CYAN = (103, 236, 210)
GOLD = (244, 190, 101)
RED = (255, 132, 132)


def fill_rect(x, y, width, height, color, alpha=255):
    sdl2.SDL_SetRenderDrawColor(p2.renderer, *color, alpha)
    rectangle = p2.to_sdl_rect(x, y, width, height)
    sdl2.SDL_RenderFillRect(p2.renderer, ctypes.byref(rectangle))


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
