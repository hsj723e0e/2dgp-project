"""Run the space workshop with: python main.py."""

import ctypes
import os
from pathlib import Path
from time import perf_counter

from pico2d import pico2d as p2
import sdl2

from player import Player
from workshop import HEIGHT, OBSTACLES, STATIONS, WALKABLE_ROOM, WIDTH, nearest_station


ASSETS = Path(__file__).resolve().parent / "asset"
CLOSE_BUTTON = (708, 116, 948, 180)
INK = (15, 28, 43)
CREAM = (241, 229, 198)
MUTED = (169, 188, 195)
CYAN = (101, 224, 217)
GOLD = (244, 190, 101)


def fill_rect(x, y, width, height, color, alpha=255):
    sdl2.SDL_SetRenderDrawColor(p2.renderer, *color, alpha)
    rectangle = p2.to_sdl_rect(x, y, width, height)
    sdl2.SDL_RenderFillRect(p2.renderer, ctypes.byref(rectangle))


def load_fonts():
    configured = os.environ.get("SPACE_WORKSHOP_FONT")
    candidates = [
        Path(configured) if configured else Path("font.ttf"),
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "malgun.ttf",
        Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
        Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    ]
    font_path = next((path for path in candidates if path.is_file()), None)
    if font_path is None:
        raise FileNotFoundError(
            "Set SPACE_WORKSHOP_FONT to the path of a Korean-capable TTF font."
        )
    return {size: p2.load_font(str(font_path), size) for size in (15, 18, 22, 30)}


class Game:
    def __init__(self):
        sdl2.SDL_SetWindowTitle(p2.window, "나만의 우주공방".encode("utf-8"))
        sdl2.SDL_SetHint(b"SDL_RENDER_SCALE_QUALITY", b"0")
        sdl2.SDL_SetRenderDrawBlendMode(p2.renderer, sdl2.SDL_BLENDMODE_BLEND)
        self.background = p2.load_image(str(ASSETS / "bg_workshop_room.png"))
        self.player_sheet = p2.load_image(str(ASSETS / "player_walk.png"))
        self.panel_image = p2.load_image(str(ASSETS / "ui_order_panel.png"))
        self.button = p2.load_image(str(ASSETS / "ui_button.png"))
        self.button_hover = p2.load_image(str(ASSETS / "ui_button_selected.png"))
        image_names = {entry.image for station in STATIONS for entry in station.entries}
        self.icons = {name: p2.load_image(str(ASSETS / f"{name}.png")) for name in image_names}
        self.fonts = load_fonts()
        self.player = Player()
        self.running = True
        self.active_station = None
        self.selected_entry = 0
        self.mouse = (0, 0)

    def text(self, x, y, text, size=18, color=CREAM):
        self.fonts[size].draw(x, y, text, color)

    def close_panel(self):
        self.active_station = None

    def interact(self):
        if self.active_station:
            self.close_panel()
            return
        self.active_station = nearest_station(self.player)
        self.selected_entry = 0
        if self.active_station:
            self.player.moving = False
            self.player.walk_time = 0.0

    def handle_events(self, events):
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                self.running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                if event.key == sdl2.SDLK_ESCAPE:
                    if self.active_station:
                        self.close_panel()
                    else:
                        self.running = False
                elif event.key in (sdl2.SDLK_e, sdl2.SDLK_RETURN):
                    self.interact()
                elif self.active_station:
                    if event.key in (sdl2.SDLK_UP, sdl2.SDLK_w):
                        self.selected_entry = (self.selected_entry - 1) % len(self.active_station.entries)
                    elif event.key in (sdl2.SDLK_DOWN, sdl2.SDLK_s):
                        self.selected_entry = (self.selected_entry + 1) % len(self.active_station.entries)
            elif event.type == sdl2.SDL_MOUSEMOTION:
                self.mouse = (event.x, HEIGHT - event.y)
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_LEFT:
                self.mouse = (event.x, HEIGHT - event.y)
                self.handle_click(*self.mouse)

    def handle_click(self, x, y):
        if not self.active_station:
            return
        left, bottom, right, top = CLOSE_BUTTON
        if left <= x <= right and bottom <= y <= top:
            self.close_panel()
        elif 275 <= x <= 610:
            for index in range(len(self.active_station.entries)):
                row_y = 478 - index * 56
                if row_y - 24 <= y <= row_y + 24:
                    self.selected_entry = index
                    break

    def update(self, dt):
        if self.active_station:
            return
        keys = sdl2.SDL_GetKeyboardState(None)
        dx = dy = 0
        if sdl2.SDL_GetKeyboardFocus():
            dx = int(bool(keys[sdl2.SDL_SCANCODE_D] or keys[sdl2.SDL_SCANCODE_RIGHT]))
            dx -= int(bool(keys[sdl2.SDL_SCANCODE_A] or keys[sdl2.SDL_SCANCODE_LEFT]))
            dy = int(bool(keys[sdl2.SDL_SCANCODE_W] or keys[sdl2.SDL_SCANCODE_UP]))
            dy -= int(bool(keys[sdl2.SDL_SCANCODE_S] or keys[sdl2.SDL_SCANCODE_DOWN]))
        self.player.update(dx, dy, dt, WALKABLE_ROOM, OBSTACLES)

    def draw_shadow(self):
        for offset in range(-4, 5):
            half_width = int(17 * (1 - (offset / 5) ** 2) ** 0.5)
            fill_rect(self.player.x - half_width, self.player.y + offset, half_width * 2, 1, INK, 75)

    def draw_station_labels(self):
        nearby = nearest_station(self.player)
        for station in STATIONS:
            selected = station is nearby
            width = len(station.name) * 18 + 28
            x, y = station.x - width / 2, station.y + 26
            fill_rect(x - 1, y - 1, width + 2, 28, CYAN if selected else (68, 87, 97), 220)
            fill_rect(x, y, width, 26, INK, 235)
            self.text(x + 14, y + 14, station.name, color=CYAN if selected else CREAM)
            if selected:
                fill_rect(station.x - 4, station.y + 10, 8, 4, GOLD)

    def draw_panel(self):
        station = self.active_station
        fill_rect(0, 0, WIDTH, HEIGHT, INK, 155)
        self.draw_panel_frame()
        self.text(278, 572, station.name, 30)
        self.text(278, 534, station.subtitle, 18, MUTED)
        fill_rect(275, 510, 730, 2, (61, 87, 103))
        for index, entry in enumerate(station.entries):
            row_y = 478 - index * 56
            selected = index == self.selected_entry
            fill_rect(275, row_y - 24, 335, 48, (40, 68, 83) if selected else (20, 40, 56))
            if selected:
                fill_rect(275, row_y - 24, 3, 48, CYAN)
            self.icons[entry.image].draw(306, row_y, 42, 42)
            self.text(339, row_y, entry.name, 18, CYAN if selected else CREAM)

        entry = station.entries[self.selected_entry]
        self.icons[entry.image].draw(816, 395, 176, 176)
        self.text(654, 275, entry.name, 22)
        # Recipe text is split at the separator to fit the detail column.
        lines = entry.description.split(" · ")
        for index, line in enumerate(lines):
            self.text(654, 239 - index * 26, line, 15, MUTED)
        self.text(278, 143, "↑ ↓ 항목 선택    E / ESC 닫기", 15, MUTED)
        left, bottom, right, top = CLOSE_BUTTON
        hovered = left <= self.mouse[0] <= right and bottom <= self.mouse[1] <= top
        button = self.button_hover if hovered else self.button
        button.draw(828, 148)
        self.text(792, 149, "돌아가기", 18, INK)

    def draw_panel_frame(self):
        # Nine-slice drawing keeps the original pixel border and screws intact.
        margin = 48
        source_x = (0, margin, self.panel_image.w - margin, self.panel_image.w)
        source_y = (0, margin, self.panel_image.h - margin, self.panel_image.h)
        target_x = (205, 205 + margin, 1075 - margin, 1075)
        target_y = (85, 85 + margin, 635 - margin, 635)
        for row in range(3):
            for column in range(3):
                width = target_x[column + 1] - target_x[column]
                height = target_y[row + 1] - target_y[row]
                self.panel_image.clip_draw(
                    source_x[column], source_y[row],
                    source_x[column + 1] - source_x[column],
                    source_y[row + 1] - source_y[row],
                    target_x[column] + width / 2,
                    target_y[row] + height / 2,
                    width, height,
                )

    def draw(self):
        p2.clear_canvas()
        self.background.draw(WIDTH / 2, HEIGHT / 2)
        self.draw_station_labels()
        self.draw_shadow()
        self.player.draw(self.player_sheet)
        fill_rect(18, 665, 282, 39, INK, 225)
        self.text(34, 686, "나만의 우주공방", 22)
        fill_rect(0, 0, WIDTH, 44, INK, 235)
        if self.active_station:
            self.text(28, 23, "↑ ↓ / W S  항목 선택", 15, MUTED)
            self.text(1002, 23, "ESC  시설 닫기", 15, MUTED)
        else:
            self.text(28, 23, "WASD / 방향키  이동", 15, MUTED)
            self.text(1002, 23, "ESC  공방 나가기", 15, MUTED)
        nearby = nearest_station(self.player)
        if nearby and not self.active_station:
            self.text(483, 23, f"E / ENTER  {nearby.name} 이용", 18, GOLD)
        if self.active_station:
            self.draw_panel()


def main():
    p2.open_canvas(WIDTH, HEIGHT, sync=True)
    game = None
    try:
        game = Game()
        previous_time = perf_counter()
        while game.running:
            current_time = perf_counter()
            dt = min(current_time - previous_time, 0.05)
            previous_time = current_time
            game.handle_events(p2.get_events())
            game.update(dt)
            game.draw()
            p2.update_canvas()
    finally:
        # Release textures and fonts while SDL's renderer is still alive.
        if game is not None:
            del game
        p2.close_canvas()


if __name__ == "__main__":
    main()
