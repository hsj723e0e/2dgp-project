"""Shared colours and SDL rectangle drawing for workshop panels."""

import ctypes

from pico2d import pico2d as p2
import sdl2


INK = (15, 28, 43)
CREAM = (241, 229, 198)
MUTED = (169, 188, 195)
CYAN = (101, 224, 217)
GOLD = (244, 190, 101)


def fill_rect(x, y, width, height, color, alpha=255):
    sdl2.SDL_SetRenderDrawColor(p2.renderer, *color, alpha)
    rectangle = p2.to_sdl_rect(x, y, width, height)
    sdl2.SDL_RenderFillRect(p2.renderer, ctypes.byref(rectangle))
