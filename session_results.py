"""Final personal equipment growth and workshop results."""

import sdl2

from customer_board import contains
from ui import CYAN, GOLD, INK, MUTED, RED, fill_rect, quantity_badge
from workshop import HEIGHT, PERSONAL_EQUIPMENT, WIDTH


EXIT = (530, 110, 750, 174)


class SessionResults:
    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        if event.type == sdl2.SDL_KEYDOWN and event.key == sdl2.SDLK_ESCAPE:
            self.game.running = False
        elif event.type == sdl2.SDL_MOUSEMOTION:
            self.game.mouse = (event.x, HEIGHT - event.y)
        elif event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_LEFT:
            self.game.mouse = (event.x, HEIGHT - event.y)
            if contains(EXIT, *self.game.mouse):
                self.game.running = False

    def draw(self):
        game, result = self.game, self.game.state.result
        fill_rect(0, 0, WIDTH, HEIGHT, INK, 210)
        game.draw_panel_frame()
        game.text(278, 585, "공방 운영 종료", 30)
        game.text(278, 548, "개인 최상급 장비 성장 결과", 18, MUTED)
        levels = dict(result.personal_levels)
        for index, entry in enumerate(PERSONAL_EQUIPMENT[:3]):
            x = 275 + index * 250
            level = levels[entry.image]
            color = CYAN if level is not None else MUTED
            fill_rect(x, 284, 230, 230, (20, 40, 56))
            fill_rect(x, 284, 3, 230, color)
            game.icons[entry.image].draw(x + 115, 443, 112, 112)
            game.text(x + 14, 365, entry.name, 18)
            quantity_badge(game, x + 14, 316, "미보유" if level is None else f"+{level}", "강화", color, 202)
            if level is not None:
                game.text(x + 14, 298, f"성능 {100 + level * 10}%", 18, CYAN)
        for x, label, value, color in (
            (275, "코인", result.coins, GOLD),
            (525, "판매", result.sold_orders, GOLD),
            (775, "제작 회수", result.collected_equipment, GOLD),
        ):
            quantity_badge(game, x, 228, value, label, color, 230)
        for x, label, value, color in (
            (275, "대여 성공", result.rental_successes, CYAN),
            (525, "대여 분실", result.rental_losses, RED),
            (775, "미종료 대여", result.pending_rentals, MUTED),
        ):
            quantity_badge(game, x, 188, value, label, color, 230)
        game.draw_button(EXIT, "게임 종료")
