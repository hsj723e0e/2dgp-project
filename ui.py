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
