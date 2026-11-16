"""Planet travel and deterministic, renderer-independent surface simulation."""

from collections import Counter
from dataclasses import dataclass
from math import hypot

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
NODE_POSITIONS = ((500, 420), (700, 510), (920, 410), (1090, 525),
                  (550, 220), (780, 315), (1020, 210), (380, 540))
GAS_POSITIONS = ((630, 350), (990, 550), (865, 170))


def gear_rank(image):
    if image.endswith('_03'):
        return 4
    if image.endswith('_advanced'):
        return 3
    return 2 if image.endswith('_02') else 1


@dataclass
class Deposit:
    x: float
    y: float
    resource: str
    remaining: int
    unstable: bool = False
    progress: float = 0.0
    strain: float = 0.0
    explosion_at: float | None = None


@dataclass
class Alien:
    x: float
    y: float
    health: float = 60
    alert_until: float = 0
    attack_at: float = 0


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
        self.nodes = []
        self.aliens = []
        self.earned = Counter()
        self.notice = ''
        self.notice_until = 0.0
        self.surface_time = 0.0
        self.attack_ready_at = 0.0
        self.mining_node = None
        self.blasts = []

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

    def leave_ship(self, player):
        allowed, reason = self.launch_status()
        if not allowed:
            return False, reason
        if self.planet is None:
            return False, '먼저 목적지를 정하고 비행하세요.'
        items = self.equipped_items()
        self.active_loadout = items
        drill, suit, oxygen = (items[category] for category in GEAR_CATEGORIES)
        self.drill_power = 1 + (gear_rank(drill.image) - 1) * 0.55 + (drill.level or 0) * 0.04
        self.armor = 1 / (1 + (gear_rank(suit.image) - 1) * 0.25 + (suit.level or 0) * 0.035)
        self.max_oxygen = 90 + gear_rank(oxygen.image) * 35 + (oxygen.level or 0) * 4
        self.oxygen = float(self.max_oxygen)
        self.health = 100.0
        self.outside = True
        self.surface_time = 0.0
        self.attack_ready_at = 0.0
        self.mining_node = None
        self.earned.clear()
        self.blasts.clear()
        self.nodes = [Deposit(x, y, self.planet.resources[index % len(self.planet.resources)],
                              8 + self.planet.danger, unstable=index % 3 == 1)
                      for index, (x, y) in enumerate(NODE_POSITIONS)]
        self.aliens = [Alien(1080, 340), Alien(760, 580)]
        player.x, player.y = LANDING_POINT
        return True, ''

    @property
    def obstacles(self):
        return (SHIP_OBSTACLE,) + tuple(Rect(node.x-28, node.y-12, node.x+28, node.y+20)
                                       for node in self.nodes if node.remaining > 0)

    def near_ship(self, player):
        return hypot(player.x - LANDING_POINT[0], player.y - LANDING_POINT[1]) <= 95

    def return_to_ship(self, player, rescued=False):
        if not self.outside:
            return False
        if not rescued and not self.near_ship(player):
            return False
        if rescued:
            for image, quantity in self.earned.items():
                inventory = self.state.resource_inventory(image)
                inventory[image] -= min(inventory[image], quantity)
        self.outside = False
        self.mining_node = None
        self.earned.clear()
        player.x, player.y = 640, 130
        self.announce('구조되었습니다. 이번 탐사에서 채집한 자원을 잃었습니다.' if rescued
                      else '우주선에 귀환했습니다. 채집한 자원이 가방에 보관되었습니다.')
        return True

    def nearest_node(self, player):
        active = [node for node in self.nodes if node.remaining > 0]
        if not active:
            return None
        node = min(active, key=lambda node: hypot(player.x - node.x, player.y - node.y))
        return node if hypot(player.x - node.x, player.y - node.y) <= 90 else None

    def gas_phase(self, index):
        phase = (self.surface_time + index * 3) % 11
        return 'warning' if 6 <= phase < 8 else 'active' if 8 <= phase < 9.5 else 'idle'

    def hurt(self, amount):
        self.health = max(0.0, self.health - amount * self.armor)

    def attack(self, player):
        if not self.outside or self.state.session_over or self.surface_time < self.attack_ready_at:
            return False
        self.attack_ready_at = self.surface_time + 0.4
        targets = [alien for alien in self.aliens if alien.health > 0
                   and hypot(alien.x - player.x, alien.y - player.y) <= 115]
        if targets:
            alien = min(targets, key=lambda alien: hypot(alien.x - player.x, alien.y - player.y))
            alien.health -= 25 * self.drill_power
            alien.alert_until = self.surface_time + 8
        return True

    def update_surface(self, player, dt, mining=False):
        if not self.outside or self.state.session_over or dt <= 0:
            return
        # Substeps keep damage, mining and timed warnings consistent across frame rates.
        remaining = dt
        while remaining > 0 and self.outside:
            step = min(remaining, 0.05)
            self._surface_step(player, step, mining)
            remaining -= step

    def _surface_step(self, player, dt, mining):
        self.surface_time += dt
        self.blasts = [blast for blast in self.blasts if blast[2] > self.surface_time]
        self.oxygen = max(0.0, self.oxygen - dt * (1 + self.planet.danger * 0.16))
        if self.oxygen <= 0:
            self.health = max(0.0, self.health - 9 * dt)
        self.mining_node = self.nearest_node(player) if mining else None
        if self.mining_node is not None:
            node = self.mining_node
            inventory = self.state.resource_inventory(node.resource)
            if inventory[node.resource] == 0 and node.resource not in self.state.staged_materials and self.state.inventory_free == 0:
                self.mining_node = None
                self.announce('가방이 가득 찼습니다. 우주선으로 귀환해 보관하세요.')
            else:
                node.progress += dt * self.drill_power
                if node.unstable and node.explosion_at is None:
                    node.strain += dt
                    if node.strain >= 2:
                        node.explosion_at = self.surface_time + 1.5
                if node.progress >= 1.6:
                    if self.state.receive_resource(node.resource, 1):
                        self.earned[node.resource] += 1
                        node.remaining -= 1
                        node.progress -= 1.6
        for node in self.nodes:
            if node.explosion_at is not None and self.surface_time >= node.explosion_at:
                self.blasts.append((node.x, node.y, self.surface_time + 0.6))
                if hypot(player.x - node.x, player.y - node.y) <= 115:
                    self.hurt(38 + self.planet.danger * 3)
                node.remaining = 0
                node.explosion_at = None
        for index, (x, y) in enumerate(GAS_POSITIONS):
            if self.gas_phase(index) == 'active' and hypot(player.x - x, player.y - y) < 72:
                self.hurt((14 + self.planet.danger * 2) * dt)
        for alien in self.aliens:
            if alien.health <= 0:
                continue
            distance = hypot(alien.x - player.x, alien.y - player.y)
            if self.mining_node is not None and distance < 650:
                alien.alert_until = self.surface_time + 8
            if alien.alert_until > self.surface_time and distance > 30:
                speed = (42 + self.planet.danger * 6) * dt
                alien.x += (player.x - alien.x) / distance * min(speed, distance - 30)
                alien.y += (player.y - alien.y) / distance * min(speed, distance - 30)
            if distance <= 45 and self.surface_time >= alien.attack_at:
                self.hurt(10 + self.planet.danger * 2)
                alien.attack_at = self.surface_time + 1
        if self.health <= 0:
            self.return_to_ship(player, rescued=True)
