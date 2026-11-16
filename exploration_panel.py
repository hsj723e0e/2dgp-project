"""Flight console and the playable planetary surface UI."""

from math import atan2, cos, sin, tau

import sdl2
from pico2d import pico2d as p2

from exploration import GAS_POSITIONS, GEAR_CATEGORIES, PLANETS
from inventory_panel import ITEM_NAMES, draw_grid, slot_bounds
from ui import CREAM, CYAN, GOLD, INK, MUTED, RED, draw_item_icon, fill_rect


NAV_BUTTON = (1020, 578, 1240, 618)
NAV_CLOSE = (1020, 576, 1145, 620)
LAUNCH = (140, 119, 370, 167)
DISEMBARK = (400, 119, 630, 167)
FLIGHT_BAG = (800, 480)
OUTSIDE_BAG = (1040, 646, 1230, 686)


def contains(bounds, x, y):
    left, bottom, right, top = bounds
    return left <= x <= right and bottom <= y <= top


def planet_bounds(index):
    left = 140 + index % 3 * 178
    top = 520 - index // 3 * 100
    return (left, top - 88, left + 164, top)


class FlightPanel:
    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        game = self.game
        if event.type == sdl2.SDL_MOUSEMOTION:
            game.mouse = event.x, 720 - event.y
        elif event.type == sdl2.SDL_KEYDOWN:
            if event.key in (sdl2.SDLK_ESCAPE, sdl2.SDLK_e, sdl2.SDLK_RETURN):
                game.navigation_open = False
        elif event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_LEFT:
            game.mouse = event.x, 720 - event.y
            self.handle_click(*game.mouse)

    def handle_click(self, x, y):
        game = self.game
        expedition = game.expedition
        if contains(NAV_CLOSE, x, y):
            game.navigation_open = False
        elif contains(LAUNCH, x, y):
            success, reason = expedition.launch()
            if not success:
                expedition.announce(reason)
        elif contains(DISEMBARK, x, y):
            success, reason = expedition.leave_ship(game.player)
            if success:
                game.navigation_open = False
            else:
                expedition.announce(reason)
        elif not expedition.flying:
            for index, planet in enumerate(PLANETS):
                if contains(planet_bounds(index), x, y):
                    expedition.destination = planet
                    return
            for index, item in enumerate(game.state.inventory_items()):
                if contains(slot_bounds(FLIGHT_BAG, index, 3), x, y):
                    expedition.choose_gear(item)
                    return

    def draw(self):
        game = self.game
        expedition = game.expedition
        fill_rect(0, 44, 1280, 676, INK, 215)
        fill_rect(105, 80, 1070, 554, (61, 79, 93))
        fill_rect(106, 81, 1068, 552, INK)
        game.text(140, 597, '행성 항로 · 탐사 준비', 30)
        game.draw_button(NAV_CLOSE, '닫기')
        game.text(140, 552, '목적지', 22)
        for index, planet in enumerate(PLANETS):
            left, bottom, right, top = planet_bounds(index)
            selected = expedition.destination == planet
            fill_rect(left, bottom, right-left, top-bottom, GOLD if selected else (61, 79, 93))
            game.exploration_images[planet.image].draw((left+right)/2, (top+bottom)/2, right-left-4, top-bottom-4)
            fill_rect(left+2, bottom+2, right-left-4, top-bottom-4, INK, 175)
            game.text(left+12, top-21, planet.name, 22, GOLD if selected else CREAM)
            game.text(right-54, top-22, f'{planet.flight_seconds}초', 15, MUTED)
            for offset, resource in enumerate(planet.resources):
                draw_item_icon(game, resource, left+28+offset*44, bottom+26, 34, 34)
        game.text(750, 552, '가방에서 탐사 장비 선택', 22)
        draw_grid(game, FLIGHT_BAG, game.state.inventory_items(), 3, 3,
                  selected_unit_ids=[token[1] for token in expedition.loadout.values() if token[1] is not None])
        items = expedition.equipped_items()
        for index, (category, label) in enumerate(zip(GEAR_CATEGORIES, ('드릴', '우주복', '산소 장치'))):
            y = 250-index*43
            game.text(750, y, label, 18, MUTED)
            item = items.get(category)
            if item:
                draw_item_icon(game, item.image, 864, y, 34, 34)
                game.text(889, y, ITEM_NAMES[item.image], 15, CYAN)
            else:
                game.text(856, y, '선택 필요', 18, RED)
        allowed, reason = expedition.launch_status()
        game.draw_button(LAUNCH, '비행 시작', allowed)
        game.draw_button(DISEMBARK, '우주선 밖으로', allowed and expedition.planet is not None)
        if expedition.flying:
            game.text(140, 207, f'{expedition.flight_destination.name} 이동 중', 22, CYAN)
            game.text(410, 207, f'{expedition.flight_remaining:.1f}초', 26, GOLD)
        elif expedition.planet:
            game.text(140, 207, f'현재 위치 · {expedition.planet.name}', 22, CYAN)
        else:
            game.text(140, 207, reason or '목적지를 선택하고 비행을 시작하세요.', 15, MUTED)
        if expedition.notice:
            game.text(140, 96, expedition.notice, 15, GOLD)


def ring(x, y, radius, color):
    sdl2.SDL_SetRenderDrawColor(p2.renderer, *color, 230)
    for index in range(32):
        start = tau*index/32
        end = tau*(index+1)/32
        sdl2.SDL_RenderDrawLine(p2.renderer, int(x+cos(start)*radius), int(720-y-sin(start)*radius),
                              int(x+cos(end)*radius), int(720-y-sin(end)*radius))


class SurfaceView:
    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        game = self.game
        expedition = game.expedition
        if event.type == sdl2.SDL_MOUSEMOTION:
            game.mouse = event.x, 720-event.y
        elif event.type == sdl2.SDL_KEYDOWN:
            if event.key == sdl2.SDLK_i:
                game.inventory_open = not game.inventory_open
            elif event.key == sdl2.SDLK_ESCAPE:
                if game.inventory_open:
                    game.inventory_open = False
                else:
                    expedition.announce('착륙선 입구로 돌아와 E키로 탑승하세요.')
            elif event.key in (sdl2.SDLK_e, sdl2.SDLK_RETURN):
                if game.inventory_open:
                    game.inventory_open = False
                elif expedition.near_ship(game.player):
                    expedition.return_to_ship(game.player)
            elif event.key == sdl2.SDLK_SPACE and not game.inventory_open:
                expedition.attack(game.player)
            elif event.key == sdl2.SDLK_F10:
                game.state.apply_cheat()
        elif event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_LEFT:
            game.mouse = event.x, 720-event.y
            if game.inventory_open:
                game.inventory_panel.handle_click(*game.mouse)
            elif contains(OUTSIDE_BAG, *game.mouse):
                game.inventory_open = True
            else:
                expedition.attack(game.player)

    def draw_prop(self, kind, item):
        game = self.game
        expedition = game.expedition
        if kind == 'ship':
            game.exploration_images['ship'].draw(160, 415, 250, 250)
        elif kind == 'node':
            game.exploration_images['deposit'].draw(item.x, item.y+25, 84, 84)
            draw_item_icon(game, item.resource, item.x+26, item.y+65, 30, 30)
            if item.unstable:
                length = item.strain * 13
                sdl2.SDL_SetRenderDrawColor(p2.renderer, *(RED if item.explosion_at else GOLD), 255)
                for direction in (-2.3, -0.5, 1.3):
                    sdl2.SDL_RenderDrawLine(p2.renderer, int(item.x), int(720-item.y-25),
                                          int(item.x+cos(direction)*length),
                                          int(720-item.y-25-sin(direction)*length))
                ring(item.x, item.y, 43, RED if item.explosion_at else GOLD)
                if item.explosion_at:
                    fill_rect(item.x-44, item.y+77, 88, 24, INK, 220)
                    game.text(item.x-38, item.y+89, '폭발 임박!', 15, RED)
        elif kind == 'alien':
            game.exploration_images['alien'].draw(item.x, item.y+17, 68, 68)
            fill_rect(item.x-23, item.y+51, 46, 4, INK)
            fill_rect(item.x-23, item.y+51, 46*max(0,item.health)/60, 4, RED)
        else:
            game.draw_shadow()
            game.player.draw(game.explorer_sheet)
            if expedition.mining_node is not None:
                node = expedition.mining_node
                angle = atan2(node.y+20-game.player.y, node.x-game.player.x)
                x = game.player.x+cos(angle)*30
                y = game.player.y+32+sin(angle)*15
                drill = expedition.active_loadout['drill'].image
                game.icons[drill].composite_draw(angle+tau/2, '', x, y, 54, 54)
                for offset in range(3):
                    flicker = int(7*sin(expedition.surface_time*35+offset*2))
                    fill_rect(x+cos(angle)*24+flicker, y+sin(angle)*24+offset*5, 4, 4, GOLD)
            if expedition.surface_time < expedition.attack_ready_at-0.2:
                ring(game.player.x, game.player.y+15, 53, GOLD)

    def draw(self):
        game = self.game
        expedition = game.expedition
        game.exploration_images[expedition.planet.image].draw(640, 360, 1280, 720)
        for index, (x, y) in enumerate(GAS_POSITIONS):
            phase = expedition.gas_phase(index)
            ring(x, y, 16 if phase == 'idle' else 72, (69, 72, 79) if phase == 'idle' else GOLD if phase == 'warning' else RED)
            if phase == 'warning':
                ring(x, y, 70, GOLD)
                fill_rect(x-44, y-12, 88, 25, INK, 220)
                game.text(x-32, y+1, '가스 전조', 15, GOLD)
            elif phase == 'active':
                for offset in range(-2, 3):
                    fill_rect(x+offset*18-7, y-12, 14, 45+int(12*sin(expedition.surface_time*12+offset)), (133, 218, 102), 180)
        props = [(350, 'ship', None), (game.player.y, 'player', None)]
        props += [(node.y, 'node', node) for node in expedition.nodes if node.remaining > 0]
        props += [(alien.y, 'alien', alien) for alien in expedition.aliens if alien.health > 0]
        for _, kind, item in sorted(props, key=lambda row: row[0], reverse=True):
            self.draw_prop(kind, item)
        for x, y, _ in expedition.blasts:
            ring(x, y, 115, RED)
            ring(x, y, 80, GOLD)
        node = expedition.nearest_node(game.player)
        if node:
            fill_rect(node.x-50, node.y-33, 100, 6, INK)
            fill_rect(node.x-50, node.y-33, 100*min(1,node.progress/1.6), 6, CYAN)
            if not expedition.near_ship(game.player):
                game.text(node.x-38, node.y-49, 'E 길게 채집', 15, GOLD)
        game.text(115, 282, 'E  우주선 귀환', 18, CYAN if expedition.near_ship(game.player) else MUTED)
        self.draw_meters()
        game.text(555, 681, expedition.planet.name+' 탐사', 26)
        game.draw_button(OUTSIDE_BAG, '인벤토리 · I')
        self.draw_minimap()
        fill_rect(0, 0, 1280, 65, INK, 240)
        game.text(24, 24, 'WASD 이동   E 길게 채집   SPACE / 좌클릭 전투   I 가방', 15, MUTED)
        for index, image in enumerate(expedition.planet.resources):
            x = 650+index*125
            draw_item_icon(game, image, x, 32, 42, 42)
            game.text(x+29, 32, str(game.state.resource_inventory(image)[image]), 26, CYAN)
        if expedition.oxygen <= expedition.max_oxygen*0.2:
            fill_rect(465, 578, 495, 36, INK, 225)
            game.text(483, 596, '산소 부족 · 우주선으로 귀환하세요!', 22, RED)
        if game.inventory_open:
            game.inventory_panel.draw()
        self.draw_notice()

    def draw_meters(self):
        game = self.game
        expedition = game.expedition
        meters = (
            ('health', '체력', 674, expedition.health, 100, RED, (91, 27, 208, 22)),
            ('oxygen', '산소', 588, expedition.oxygen, expedition.max_oxygen,
             RED if expedition.oxygen <= expedition.max_oxygen*0.2 else CYAN, (105, 26, 194, 22)),
        )
        for kind, label, y, value, maximum, color, well in meters:
            game.mining_meters[kind].draw(178, y, 320, 78)
            left, bottom, width, height = well
            ratio = max(0, min(1, value/maximum))
            fill_rect(18+left, y-39+bottom, width*ratio, height, color)
            highlight = tuple(min(255, component+35) for component in color)
            fill_rect(18+left, y-39+bottom+height-3, width*ratio, 3, highlight)
            fill_rect(339, y-27, 108, 55, INK, 220)
            game.text(348, y+14, label, 15, MUTED)
            game.text(348, y-10, f'{int(value)}/{int(maximum)}', 22, color)

    def draw_minimap(self):
        game = self.game
        expedition = game.expedition
        fill_rect(1050, 506, 182, 125, INK, 225)
        for x,y,color in [(160,350,GOLD), (game.player.x,game.player.y,CYAN)]+[
                (node.x,node.y,(200,200,220)) for node in expedition.nodes if node.remaining>0]:
            fill_rect(1058+x/1280*164, 514+y/720*108, 5, 5, color)

    def draw_notice(self):
        game = self.game
        expedition = game.expedition
        if expedition.flying:
            message = f'{expedition.flight_destination.name} 이동 중 · {expedition.flight_remaining:.1f}초'
        elif expedition.state.clock() < expedition.notice_until:
            message = expedition.notice
        else:
            return
        y = 76 if expedition.outside else 628
        fill_rect(300,y,710,33,INK,230)
        game.text(315,y+16,message,18,GOLD)
