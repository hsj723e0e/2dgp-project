"""Planet travel and deterministic, renderer-independent surface simulation."""

from collections import Counter
from dataclasses import dataclass
from math import cos, hypot, sin, tau

from player import Rect


@dataclass(frozen=True)
class Planet:
    image: str
    name: str
    resources: tuple
    flight_seconds: int
    danger: int


PLANETS = (
    Planet('mercury', '수성', ('mat_01', 'mat_03'), 4, 1),
    Planet('venus', '금성', ('mat_01', 'mat_03'), 5, 2),
    Planet('earth', '지구', ('mat_03',), 3, 0),
    Planet('mars', '화성', ('mat_01', 'mat_03'), 5, 1),
    Planet('jupiter', '목성', ('mat_02', 'mat_01'), 7, 3),
    Planet('saturn', '토성', ('mat_02', 'mat_01'), 8, 3),
    Planet('uranus', '천왕성', ('item_chip', 'mat_02'), 9, 4),
    Planet('neptune', '해왕성', ('item_chip', 'mat_02'), 10, 4),
    Planet('sun', '태양', ('item_core',), 12, 5),
)
SURFACE_ROOM = Rect(55, 90, 1225, 635)
SHIP_OBSTACLE = Rect(80, 350, 220, 425)
LANDING_POINT = (285, 320)
GEAR_CATEGORIES = ('drill', 'suit', 'oxygen')
ROCK_COUNT = 14
DRILL_REACH = 100
PICKUP_RADIUS = 30
MAGNET_RADIUS = 105
ROCK_AREA = Rect(340, 105, 1225, 620)


def gear_rank(image):
    if image.endswith('_03'):
        return 4
    if image.endswith('_advanced'):
        return 3
    return 2 if image.endswith('_02') else 1


@dataclass
class Asteroid:
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    health: float
    max_health: float
    resource: str
    angle: float = 0.0
    spin: float = 0.0
    flash_until: float = 0.0


@dataclass
class Bomb:
    x: float
    y: float
    vx: float
    vy: float
    radius: float = 23.0
    active: bool = True


@dataclass
class OreDrop:
    x: float
    y: float
    resource: str
    quantity: int
    vx: float = 0.0
    vy: float = 0.0


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    expires_at: float
    color: tuple


class Expedition:
    def __init__(self, state):
        self.state = state
        self.destination = PLANETS[2]
        self.planet = None
        self.arrival_at = None
        self.flight_destination = None
        self.loadout = {}
        self.active_loadout = {}
        self.outside = False
        self.health = 100.0
        self.oxygen = 0.0
        self.max_oxygen = 1.0
        self.drill_power = 1.0
        self.armor = 1.0
        self.rocks = []
        self.bombs = []
        self.drops = []
        self.particles = []
        self.blasts = []
        self.earned = Counter()
        self.notice = ''
        self.notice_until = 0.0
        self.surface_time = 0.0
        self.drilling = False
        self.drill_target = None
        self.aim = (640, 360)
        self.hit_ready_at = 0.0
        self.spark_ready_at = 0.0
        self.bomb_spawn_at = 0.0
        self.pickup_notice_at = 0.0
        self.spawn_count = 0
        self.destroyed_rocks = 0

    @property
    def flying(self):
        return self.arrival_at is not None

    @property
    def flight_remaining(self):
        return max(0.0, self.arrival_at - self.state.clock()) if self.flying else 0.0

    def announce(self, message):
        self.notice = message
        self.notice_until = self.state.clock() + 7

    def choose_gear(self, item):
        if self.flying or self.outside or self.state.session_over:
            return False
        parts = item.image.split('_')
        if len(parts) < 3 or parts[0] != 'eq' or parts[1] not in GEAR_CATEGORIES:
            return False
        if item not in self.state.inventory_items():
            return False
        self.loadout[parts[1]] = (item.image, item.unit_id)
        return True

    def equipped_items(self):
        available = {(item.image, item.unit_id): item for item in self.state.inventory_items()}
        return {category: available[token] for category, token in self.loadout.items() if token in available}

    def launch_status(self):
        if self.state.session_over:
            return False, '운영 시간이 종료되었습니다.'
        if self.flying:
            return False, '행성으로 이동 중입니다.'
        if self.outside:
            return False, '먼저 우주선으로 돌아오세요.'
        if len(self.equipped_items()) != 3:
            return False, '가방에서 드릴·우주복·산소 장치를 각각 선택하세요.'
        return True, ''

    def launch(self):
        allowed, reason = self.launch_status()
        if not allowed:
            return False, reason
        self.flight_destination = self.destination
        self.arrival_at = self.state.clock() + self.destination.flight_seconds
        self.planet = None
        self.announce(f'{self.destination.name}으로 출발했습니다.')
        return True, ''

    def update_flight(self):
        if self.state.session_over:
            return
        if self.flying and self.state.clock() >= self.arrival_at:
            self.planet = self.flight_destination
            self.arrival_at = None
            self.announce(f'{self.planet.name}에 도착했습니다. 우주선 밖으로 나갈 수 있습니다.')

    def loadout_stats(self):
        items = self.equipped_items()
        if len(items) != 3:
            return None
        drill, suit, oxygen = (items[category] for category in GEAR_CATEGORIES)
        power = 1 + (gear_rank(drill.image)-1)*0.75 + (drill.level or 0)*0.08
        armor = 1 / (1 + (gear_rank(suit.image)-1)*0.25 + (suit.level or 0)*0.035)
        capacity = 90 + gear_rank(oxygen.image)*35 + (oxygen.level or 0)*4
        return power, armor, capacity

    def leave_ship(self, player):
        allowed, reason = self.launch_status()
        if not allowed:
            return False, reason
        if self.planet is None:
            return False, '먼저 목적지를 정하고 비행하세요.'
        self.active_loadout = self.equipped_items()
        self.drill_power, self.armor, self.max_oxygen = self.loadout_stats()
        self.oxygen = float(self.max_oxygen)
        self.health = 100.0
        self.outside = True
        self.surface_time = 0.0
        self.hit_ready_at = 0.0
        self.spark_ready_at = 0.0
        self.bomb_spawn_at = 0.0
        self.pickup_notice_at = 0.0
        self.spawn_count = 0
        self.destroyed_rocks = 0
        self.drilling = False
        self.drill_target = None
        self.rocks.clear()
        self.bombs.clear()
        self.drops.clear()
        self.particles.clear()
        self.earned.clear()
        self.blasts.clear()
        player.x, player.y = LANDING_POINT
        for _ in range(ROCK_COUNT):
            self.rocks.append(self.spawn_rock(player))
        for _ in range(2 + self.planet.danger // 2):
            self.bombs.append(self.spawn_bomb(player))
        return True, ''

    @property
    def obstacles(self):
        return (SHIP_OBSTACLE,)

    @property
    def drill_damage(self):
        return 34 * self.drill_power

    def near_ship(self, player):
        return hypot(player.x-LANDING_POINT[0], player.y-LANDING_POINT[1]) <= 95

    def return_to_ship(self, player, rescued=False):
        if not self.outside or (not rescued and not self.near_ship(player)):
            return False
        if rescued:
            for image, quantity in self.earned.items():
                inventory = self.state.resource_inventory(image)
                inventory[image] -= min(inventory[image], quantity)
        self.outside = False
        self.drilling = False
        self.drill_target = None
        self.earned.clear()
        player.x, player.y = 640, 130
        self.announce('구조되었습니다. 이번 탐사에서 회수한 자원을 잃었습니다.' if rescued
                      else '우주선에 귀환했습니다. 회수한 자원이 가방에 보관되었습니다.')
        return True

    def spawn_position(self, player, radius):
        for _ in range(30):
            x = self.state.rng.uniform(ROCK_AREA.left+radius, ROCK_AREA.right-radius)
            y = self.state.rng.uniform(ROCK_AREA.bottom+radius, ROCK_AREA.top-radius)
            if hypot(x-player.x, y-player.y-30) > radius+170:
                return x, y
        # The opposite side remains available even when the player is at an edge.
        x = ROCK_AREA.left+radius if player.x > 780 else ROCK_AREA.right-radius
        return x, ROCK_AREA.top-radius

    def spawn_rock(self, player):
        rng = self.state.rng
        radius = rng.uniform(27, 49)
        x, y = self.spawn_position(player, radius)
        angle = rng.uniform(0, tau)
        speed = rng.uniform(28, 54) + self.planet.danger*7
        health = (42+self.planet.danger*17)*radius/34
        resource = self.planet.resources[self.spawn_count % len(self.planet.resources)]
        self.spawn_count += 1
        return Asteroid(x, y, cos(angle)*speed, sin(angle)*speed, radius, health, health,
                        resource, rng.uniform(0,tau), rng.uniform(-0.6,0.6))

    def spawn_bomb(self, player):
        x, y = self.spawn_position(player, 26)
        angle = self.state.rng.uniform(0,tau)
        speed = 22+self.planet.danger*4
        return Bomb(x,y,cos(angle)*speed,sin(angle)*speed)

    def move_body(self, body, dt):
        body.x += body.vx*dt
        body.y += body.vy*dt
        if body.x < ROCK_AREA.left+body.radius:
            body.x = ROCK_AREA.left+body.radius
            body.vx = abs(body.vx)
        elif body.x > ROCK_AREA.right-body.radius:
            body.x = ROCK_AREA.right-body.radius
            body.vx = -abs(body.vx)
        if body.y < ROCK_AREA.bottom+body.radius:
            body.y = ROCK_AREA.bottom+body.radius
            body.vy = abs(body.vy)
        elif body.y > ROCK_AREA.top-body.radius:
            body.y = ROCK_AREA.top-body.radius
            body.vy = -abs(body.vy)

    def target_at(self, player, aim):
        origin_x, origin_y = player.x, player.y+30
        dx, dy = aim[0]-origin_x, aim[1]-origin_y
        length = hypot(dx,dy)
        if length < 1:
            dx, dy, length = 1.0, 0.0, 1.0
        dx, dy = dx/length, dy/length
        nearest = None
        nearest_distance = float('inf')
        for body in (*self.rocks, *self.bombs):
            if isinstance(body,Bomb) and not body.active:
                continue
            offset_x, offset_y = body.x-origin_x, body.y-origin_y
            along = offset_x*dx+offset_y*dy
            side = abs(offset_x*dy-offset_y*dx)
            contact = along-body.radius
            if along >= 0 and side <= body.radius+12 and contact <= DRILL_REACH and contact < nearest_distance:
                nearest = body
                nearest_distance = contact
        return nearest

    def burst(self, x, y, count, color):
        for _ in range(count):
            angle = self.state.rng.uniform(0,tau)
            speed = self.state.rng.uniform(35,180)
            self.particles.append(Particle(x,y,cos(angle)*speed,sin(angle)*speed,
                                           self.surface_time+self.state.rng.uniform(0.25,0.65),color))

    def destroy_rock(self, rock):
        if rock not in self.rocks:
            return
        self.rocks.remove(rock)
        self.destroyed_rocks += 1
        quantity = 2+int(rock.radius//18)
        existing = next((drop for drop in self.drops if drop.resource == rock.resource
                         and hypot(drop.x-rock.x,drop.y-rock.y)<80),None)
        if existing:
            existing.quantity += quantity
        else:
            self.drops.append(OreDrop(rock.x,rock.y,rock.resource,quantity,rock.vx*0.3,rock.vy*0.3))
        self.burst(rock.x,rock.y,22,(244,190,101))
        self.blasts.append((rock.x,rock.y,rock.radius*1.3,self.surface_time+0.25,False))

    def explode_bomb(self, bomb, player):
        if not bomb.active:
            return
        bomb.active = False
        self.blasts.append((bomb.x,bomb.y,155,self.surface_time+0.65,True))
        self.burst(bomb.x,bomb.y,35,(255,100,75))
        if hypot(player.x-bomb.x,player.y+30-bomb.y)<=155:
            self.hurt(45+self.planet.danger*5)
            self.hit_ready_at = self.surface_time+0.85
        self.bomb_spawn_at = self.surface_time+4

    def hurt(self, amount):
        self.health = max(0.0,self.health-amount*self.armor)

    def update_surface(self, player, dt, mining=False, aim=None):
        if not self.outside or self.state.session_over or dt <= 0:
            return
        if aim is not None:
            self.aim = aim
        self.drilling = bool(mining)
        remaining = dt
        while remaining > 0 and self.outside:
            step = min(remaining,0.025)
            self._surface_step(player,step)
            remaining -= step

    def _surface_step(self, player, dt):
        self.surface_time += dt
        self.blasts = [blast for blast in self.blasts if blast[3]>self.surface_time]
        self.particles = [particle for particle in self.particles if particle.expires_at>self.surface_time]
        for particle in self.particles:
            particle.x += particle.vx*dt
            particle.y += particle.vy*dt
        self.oxygen = max(0.0,self.oxygen-dt*(1+self.planet.danger*0.16))
        if self.oxygen<=0:
            self.health = max(0.0,self.health-9*dt)
        for rock in self.rocks:
            self.move_body(rock,dt)
            rock.angle += rock.spin*dt
        for bomb in self.bombs:
            if bomb.active:
                self.move_body(bomb,dt)
                if hypot(bomb.x-player.x,bomb.y-player.y-30)<bomb.radius+20:
                    self.explode_bomb(bomb,player)
        self.drill_target = self.target_at(player,self.aim) if self.drilling else None
        if isinstance(self.drill_target,Bomb):
            self.explode_bomb(self.drill_target,player)
            self.drill_target = None
        elif self.drill_target is not None:
            rock = self.drill_target
            rock.health -= self.drill_damage*dt
            rock.flash_until = self.surface_time+0.08
            if self.surface_time>=self.spark_ready_at:
                self.burst(rock.x,rock.y,3,(103,236,210))
                self.spark_ready_at = self.surface_time+0.08
            if rock.health<=0:
                self.destroy_rock(rock)
                self.drill_target = None
        for rock in self.rocks:
            distance = hypot(rock.x-player.x,rock.y-player.y-30)
            if distance < rock.radius+20 and self.surface_time>=self.hit_ready_at:
                self.hurt(10+self.planet.danger*2)
                self.hit_ready_at = self.surface_time+0.85
                normal_x = (rock.x-player.x)/max(distance,1)
                normal_y = (rock.y-player.y-30)/max(distance,1)
                rock.vx = normal_x*(45+self.planet.danger*7)
                rock.vy = normal_y*(45+self.planet.danger*7)
                rock.x += normal_x*12
                rock.y += normal_y*12
                x,y = player.x-normal_x*14,player.y-normal_y*14
                if player.can_stand(x,y,SURFACE_ROOM,self.obstacles):
                    player.x,player.y = x,y
        self.collect_drops(player,dt)
        while len(self.rocks)<ROCK_COUNT:
            self.rocks.append(self.spawn_rock(player))
        if self.surface_time>=self.bomb_spawn_at:
            self.bombs = [bomb for bomb in self.bombs if bomb.active]
            while len(self.bombs)<2+self.planet.danger//2:
                self.bombs.append(self.spawn_bomb(player))
        if self.health<=0:
            self.return_to_ship(player,rescued=True)

    def collect_drops(self, player, dt):
        for drop in tuple(self.drops):
            dx,dy = player.x-drop.x,player.y+22-drop.y
            distance = hypot(dx,dy)
            if distance<=PICKUP_RADIUS:
                if self.state.receive_resource(drop.resource,drop.quantity):
                    self.earned[drop.resource] += drop.quantity
                    self.drops.remove(drop)
                elif self.surface_time>=self.pickup_notice_at:
                    self.announce('가방이 가득 찼습니다. 자원을 회수하려면 빈칸이 필요합니다.')
                    self.pickup_notice_at = self.surface_time+3
            elif distance<MAGNET_RADIUS:
                travel = min(distance-PICKUP_RADIUS/2,260*dt)
                drop.x += dx/distance*travel
                drop.y += dy/distance*travel
            else:
                drop.x = max(70,min(1210,drop.x+drop.vx*dt))
                drop.y = max(100,min(610,drop.y+drop.vy*dt))
                drop.vx *= max(0,1-3*dt)
                drop.vy *= max(0,1-3*dt)
