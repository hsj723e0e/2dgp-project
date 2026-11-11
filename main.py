"""Run the space workshop with: python main.py."""

import ctypes
import os
from pathlib import Path
from time import perf_counter

from pico2d import pico2d as p2
import sdl2

from customer_board import CustomerBoard
from game_state import GameState, MATERIAL_PRICES, RECIPES
from player import Player
from ui import CREAM, CYAN, GOLD, INK, MUTED, fill_rect
from workshop import EQUIPMENT, HEIGHT, MATERIALS, OBSTACLES, STATIONS, WALKABLE_ROOM, WIDTH, nearest_station


ASSETS = Path(__file__).resolve().parent / "asset"
CLOSE_BUTTON = (280, 116, 520, 180)
ACTION_BUTTON = (708, 116, 948, 180)


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
        self.button_disabled = p2.load_image(str(ASSETS / "ui_button_disabled.png"))
        image_names = {entry.image for station in STATIONS for entry in station.entries}
        self.icons = {name: p2.load_image(str(ASSETS / f"{name}.png")) for name in image_names}
        self.fonts = load_fonts()
        self.player = Player()
        self.state = GameState()
        self.running = True
        self.active_station = None
        self.selected_entry = 0
        self.mouse = (0, 0)
        self.purchase_quantity = 1
        self.feedback = ""
        self.feedback_success = True
        self.customer_board = CustomerBoard(self)

    def text(self, x, y, text, size=18, color=CREAM):
        self.fonts[size].draw(x, y, text, color)

    def close_panel(self):
        self.active_station = None
        self.feedback = ""

    def select_entry(self, index):
        self.selected_entry = index % len(self.active_station.entries)
        self.purchase_quantity = 1
        self.feedback = ""

    def interact(self):
        if self.active_station:
            self.close_panel()
            return
        self.active_station = nearest_station(self.player)
        self.selected_entry = 0
        self.purchase_quantity = 1
        self.feedback = ""
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
                elif self.active_station and self.active_station.name == "주문 게시판":
                    self.customer_board.handle_key(event.key)
                elif self.active_station:
                    if event.key in (sdl2.SDLK_UP, sdl2.SDLK_w):
                        self.select_entry(self.selected_entry - 1)
                    elif event.key in (sdl2.SDLK_DOWN, sdl2.SDLK_s):
                        self.select_entry(self.selected_entry + 1)
                    elif event.key == sdl2.SDLK_LEFT:
                        self.change_quantity(-1)
                    elif event.key == sdl2.SDLK_RIGHT:
                        self.change_quantity(1)
                    elif event.key == sdl2.SDLK_SPACE:
                        self.perform_action()
            elif event.type == sdl2.SDL_MOUSEMOTION:
                self.mouse = (event.x, HEIGHT - event.y)
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_LEFT:
                self.mouse = (event.x, HEIGHT - event.y)
                self.handle_click(*self.mouse)

    def handle_click(self, x, y):
        if not self.active_station:
            return
        if self.active_station.name == "주문 게시판":
            self.customer_board.handle_click(x, y)
            return
        left, bottom, right, top = CLOSE_BUTTON
        if left <= x <= right and bottom <= y <= top:
            self.close_panel()
        elif ACTION_BUTTON[0] <= x <= ACTION_BUTTON[2] and ACTION_BUTTON[1] <= y <= ACTION_BUTTON[3]:
            self.perform_action()
        elif 708 <= x <= 748 and 215 <= y <= 243:
            self.change_quantity(-1)
        elif 908 <= x <= 948 and 215 <= y <= 243:
            self.change_quantity(1)
        elif 275 <= x <= 610:
            for index in range(len(self.active_station.entries)):
                row_y = 478 - index * 52
                if row_y - 24 <= y <= row_y + 24:
                    self.select_entry(index)
                    break

    def change_quantity(self, amount):
        if self.active_station.name != "재료 보관대":
            return
        entry = self.active_station.entries[self.selected_entry]
        maximum = max(1, self.state.coins // MATERIAL_PRICES[entry.image])
        self.purchase_quantity = max(1, min(maximum, self.purchase_quantity + amount))
        self.feedback = ""

    def panel_action(self):
        if self.active_station.name == "재료 보관대":
            entry = self.active_station.entries[self.selected_entry]
            available, reason = self.state.purchase_status(entry.image, self.purchase_quantity)
            cost = MATERIAL_PRICES[entry.image] * self.purchase_quantity
            return f"{cost} 코인 구매", available, reason
        if self.active_station.name == "작업대":
            if self.state.job is not None:
                if self.state.ready_to_collect:
                    return "완성품 회수", True, ""
                return "제작 중", False, ""
            entry = self.active_station.entries[self.selected_entry]
            available, reason = self.state.craft_status(entry.image)
            return "제작 시작", available, reason
        return None

    def perform_action(self):
        if self.active_station.name == "재료 보관대":
            entry = self.active_station.entries[self.selected_entry]
            self.feedback_success, self.feedback = self.state.purchase(entry.image, self.purchase_quantity)
            if self.feedback_success:
                self.purchase_quantity = 1
        elif self.active_station.name == "작업대":
            if self.state.job is not None:
                self.feedback_success, self.feedback = self.state.collect()
            else:
                entry = self.active_station.entries[self.selected_entry]
                self.feedback_success, self.feedback = self.state.start_craft(entry.image)

    def draw_button(self, bounds, label, enabled=True):
        left, bottom, right, top = bounds
        hovered = left <= self.mouse[0] <= right and bottom <= self.mouse[1] <= top
        image = self.button_hover if hovered else self.button
        if not enabled:
            image = self.button_disabled
        image.draw((left + right) / 2, (bottom + top) / 2, right - left, top - bottom)
        text_width, text_height = ctypes.c_int(), ctypes.c_int()
        sdl2.sdlttf.TTF_SizeUTF8(self.fonts[18].font, label.encode("utf-8"), ctypes.byref(text_width), ctypes.byref(text_height))
        self.text((left + right - text_width.value) / 2, (bottom + top) / 2 + 1, label, 18, INK)

    def update(self, dt):
        self.state.update_customers()
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
        if station.name == "주문 게시판":
            self.customer_board.draw()
            return
        fill_rect(0, 0, WIDTH, HEIGHT, INK, 155)
        self.draw_panel_frame()
        self.text(278, 572, station.name, 30)
        self.text(278, 534, station.subtitle, 18, MUTED)
        if station.name == "장비 진열대":
            self.text(875, 572, f"총 {sum(self.state.equipment.values())}개", 22, GOLD)
        fill_rect(275, 510, 730, 2, (61, 87, 103))
        for index, entry in enumerate(station.entries):
            row_y = 478 - index * 52
            selected = index == self.selected_entry
            fill_rect(275, row_y - 24, 335, 48, (40, 68, 83) if selected else (20, 40, 56))
            if selected:
                fill_rect(275, row_y - 24, 3, 48, CYAN)
            self.icons[entry.image].draw(306, row_y, 42, 42)
            self.text(339, row_y, entry.name, 18, CYAN if selected else CREAM)
            if station.name == "장비 진열대":
                self.text(550, row_y, f"{self.state.equipment[entry.image]}개", 18, GOLD)

        entry = station.entries[self.selected_entry]
        self.icons[entry.image].draw(816, 428, 144, 144)
        self.text(654, 329, entry.name, 22)
        lines = entry.description.split(" · ")
        if station.name == "작업대":
            recipe = RECIPES[entry.image]
            material_names = {material.image: material.name for material in MATERIALS}
            lines = [
                f"{material_names[name]} {quantity}개 / 보유 {self.state.materials[name]}개"
                for name, quantity in recipe.ingredients.items()
            ]
        for index, line in enumerate(lines):
            self.text(654, 300 - index * 22, line, 15, MUTED)
        if station.name == "재료 보관대":
            price = MATERIAL_PRICES[entry.image]
            owned = self.state.materials[entry.image]
            self.text(654, 255, f"단가 {price} 코인 · 보유 {owned}개", 18, GOLD)
            fill_rect(708, 215, 40, 28, (40, 68, 83))
            fill_rect(908, 215, 40, 28, (40, 68, 83))
            self.text(722, 229, "-")
            self.text(921, 229, "+")
            self.text(764, 229, f"수량 {self.purchase_quantity}개", 18)
        elif station.name == "작업대":
            self.text(654, 255, f"제작 시간 {RECIPES[entry.image].seconds}초", 18, GOLD)
            if self.state.job is not None:
                equipment_name = next(item.name for item in EQUIPMENT if item.image == self.state.job.equipment)
                self.text(654, 230, equipment_name, 18, CYAN)
                status = "완성 · 회수 가능" if self.state.ready_to_collect else f"남은 시간 {self.state.remaining:.1f}초"
                self.text(654, 208, status, 15, GOLD)
        elif station.name == "장비 진열대":
            self.text(654, 255, f"보유 수량 {self.state.equipment[entry.image]}개", 22, CYAN)
        self.draw_button(CLOSE_BUTTON, "돌아가기")
        action = self.panel_action()
        if action:
            label, available, reason = action
            self.draw_button(ACTION_BUTTON, label, available)
            if reason and not self.feedback:
                self.text(654, 191, reason, 15, GOLD)
        if self.feedback and not (station.name == "작업대" and self.state.job is not None):
            self.text(654, 191, self.feedback, 15, CYAN if self.feedback_success else GOLD)

    def draw_crafting_status(self):
        if self.state.job is None:
            return
        name = next(entry.name for entry in EQUIPMENT if entry.image == self.state.job.equipment)
        fill_rect(366, 665, 600, 39, INK, 240)
        if self.state.ready_to_collect:
            self.text(382, 687, f"{name} 완성 · 작업대에서 회수", 18, CYAN)
            progress = 1.0
        else:
            self.text(382, 687, f"{name} 제작 중 · {self.state.remaining:.1f}초", 18, GOLD)
            progress = 1 - self.state.remaining / RECIPES[self.state.job.equipment].seconds
        fill_rect(382, 669, 568, 3, (40, 68, 83))
        fill_rect(382, 669, 568 * progress, 3, CYAN)

    def draw_coin_counter(self):
        fill_rect(1044, 665, 218, 39, INK, 240)
        for offset in range(-9, 10):
            half_width = int((100 - offset * offset) ** 0.5)
            fill_rect(1068 - half_width, 685 + offset, 2 * half_width, 1, GOLD)
        fill_rect(1066, 680, 3, 10, (156, 100, 41))
        self.text(1091, 686, f"{self.state.coins} 코인", 22, GOLD)

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
            controls = "↑ ↓ / W S 선택   E / ESC 닫기"
            if self.active_station.name == "재료 보관대":
                controls = "↑ ↓ 선택   ← → 수량   SPACE 구매   E / ESC 닫기"
            elif self.active_station.name == "작업대":
                controls = "↑ ↓ 선택   SPACE 제작 / 회수   E / ESC 닫기"
            elif self.active_station.name == "주문 게시판":
                controls = "3 주문 거절   E / ESC 닫기"
            self.text(28, 23, controls, 15, MUTED)
            self.text(1002, 23, "ESC  시설 닫기", 15, MUTED)
        else:
            self.text(28, 23, "WASD / 방향키  이동", 15, MUTED)
            self.text(1002, 23, "ESC  공방 나가기", 15, MUTED)
        nearby = nearest_station(self.player)
        if nearby and not self.active_station:
            self.text(483, 23, f"E / ENTER  {nearby.name} 이용", 18, GOLD)
        if self.active_station:
            self.draw_panel()
        self.draw_crafting_status()
        self.draw_coin_counter()


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
