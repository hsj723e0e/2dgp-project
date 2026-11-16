"""Flight console and the playable planetary surface UI."""

from math import atan2, cos, sin, tau

import sdl2
from pico2d import pico2d as p2

from exploration import GEAR_CATEGORIES, PLANETS
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
                game.surface_view.drill_held = False
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
        stats = expedition.loadout_stats()
        if stats:
            power, armor, oxygen = stats
            game.text(140, 182, f'드릴 {34*power:.0f}/초 · 산소 {oxygen} · 충돌 피해 {armor*100:.0f}%', 15, GOLD)
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
        self.drill_held = False

    def handle_event(self, event):
        game = self.game
        expedition = game.expedition
        if event.type == sdl2.SDL_MOUSEMOTION:
            game.mouse = event.x, 720-event.y
        elif event.type == sdl2.SDL_MOUSEBUTTONUP and event.button == sdl2.SDL_BUTTON_LEFT:
            self.drill_held = False
        elif event.type == sdl2.SDL_KEYDOWN:
            if event.key == sdl2.SDLK_i:
                game.inventory_open = not game.inventory_open
                self.drill_held = False
            elif event.key == sdl2.SDLK_ESCAPE:
                self.drill_held = False
                if game.inventory_open:
                    game.inventory_open = False
                else:
                    expedition.announce('착륙선 입구로 돌아와 E키로 탑승하세요.')
            elif event.key in (sdl2.SDLK_e, sdl2.SDLK_RETURN):
                if game.inventory_open:
                    game.inventory_open = False
                elif expedition.near_ship(game.player):
                    self.drill_held = False
                    expedition.return_to_ship(game.player)
            elif event.key == sdl2.SDLK_F10:
                game.state.apply_cheat()
        elif event.type == sdl2.SDL_MOUSEBUTTONDOWN and event.button == sdl2.SDL_BUTTON_LEFT:
            game.mouse = event.x, 720-event.y
            if game.inventory_open:
                game.inventory_panel.handle_click(*game.mouse)
            elif contains(OUTSIDE_BAG, *game.mouse):
                game.inventory_open = True
                self.drill_held = False
            else:
                self.drill_held = True

    def draw_player(self):
        game = self.game
        expedition = game.expedition
        game.draw_shadow()
        game.player.draw(game.explorer_sheet)
        angle = atan2(expedition.aim[1]-game.player.y-30, expedition.aim[0]-game.player.x)
        offset = 44+2*sin(expedition.surface_time*65) if expedition.drilling else 36
        x = game.player.x+cos(angle)*offset
        y = game.player.y+30+sin(angle)*offset
        drill = expedition.active_loadout['drill'].image
        game.icons[drill].composite_draw(angle+tau/2, '', x, y, 84, 70)
        if expedition.surface_time < expedition.hit_ready_at:
            ring(game.player.x, game.player.y+27, 36, RED)

    def draw_rock(self, rock):
        game = self.game
        expedition = game.expedition
        size = rock.radius*2.4
        game.exploration_images['asteroid'].composite_draw(rock.angle, '', rock.x, rock.y, size, size)
        if rock.flash_until > expedition.surface_time:
            ring(rock.x, rock.y, rock.radius+2, CREAM)
        if rock is expedition.drill_target:
            ring(rock.x, rock.y, rock.radius+7, CYAN)
            left, y = rock.x-52, rock.y-rock.radius-17
            fill_rect(left, y, 104, 7, INK)
            fill_rect(left+1, y+1, 102*max(0,rock.health)/rock.max_health, 5, GOLD)
            draw_item_icon(game, rock.resource, rock.x-32, rock.y+rock.radius+27, 34, 34)
            game.text(rock.x-8, rock.y+rock.radius+27, f'{max(0,int(rock.health))}', 22, GOLD)

    def draw(self):
        game = self.game
        expedition = game.expedition
        game.exploration_images[expedition.planet.image].draw(640, 360, 1280, 720)
        game.exploration_images['ship'].draw(160, 415, 250, 250)
        for rock in expedition.rocks:
            self.draw_rock(rock)
        for bomb in expedition.bombs:
            if bomb.active:
                game.exploration_images['bomb'].draw(bomb.x,bomb.y,65,65)
                if int(expedition.surface_time*5)%2:
                    ring(bomb.x,bomb.y,33,RED)
        for drop in expedition.drops:
            draw_item_icon(game,drop.resource,drop.x,drop.y,36,36)
            game.text(drop.x+19,drop.y,str(drop.quantity),18,GOLD)
        self.draw_player()
        for particle in expedition.particles:
            fill_rect(particle.x,particle.y,4,4,particle.color)
        for x,y,radius,expires_at,dangerous in expedition.blasts:
            duration = 0.65 if dangerous else 0.25
            progress = 1-(expires_at-expedition.surface_time)/duration
            ring(x,y,radius*min(1,0.3+progress),RED if dangerous else GOLD)
            if dangerous:
                ring(x,y,radius*min(1,0.15+progress),GOLD)
        if expedition.near_ship(game.player):
            fill_rect(98,264,190,32,INK,220)
            game.text(110,280,'E  우주선 귀환',18,CYAN)
        self.draw_meters()
        fill_rect(465,650,395,52,INK,225)
        game.text(480,679,expedition.planet.name+' · 암석 파괴',26)
        game.text(480,653,f'파괴 {expedition.destroyed_rocks}개 · 드릴 {expedition.drill_damage:.0f}/초',18,GOLD)
        game.draw_button(OUTSIDE_BAG,'인벤토리 · I')
        self.draw_minimap()
        fill_rect(0,0,1280,65,INK,240)
        game.text(24,24,'WASD 이동   마우스 조준·좌클릭 길게 드릴   E 귀환   I 가방',15,MUTED)
        for index,image in enumerate(expedition.planet.resources):
            x = 690+index*125
            draw_item_icon(game,image,x,32,42,42)
            game.text(x+29,32,str(game.state.resource_inventory(image)[image]),26,CYAN)
        if expedition.oxygen <= expedition.max_oxygen*0.2:
            fill_rect(465,578,495,36,INK,225)
            game.text(483,596,'산소 부족 · 우주선으로 귀환하세요!',22,RED)
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
        fill_rect(1050,506,182,125,INK,225)
        markers = [(160,350,GOLD),(game.player.x,game.player.y,CYAN)]
        markers += [(rock.x,rock.y,(200,200,220)) for rock in expedition.rocks]
        markers += [(bomb.x,bomb.y,RED) for bomb in expedition.bombs if bomb.active]
        markers += [(drop.x,drop.y,CYAN) for drop in expedition.drops]
        for x,y,color in markers:
            fill_rect(1058+x/1280*164,514+y/720*108,5,5,color)

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
