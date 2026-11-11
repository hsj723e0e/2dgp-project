"""Player movement and collision, independent of the rendering library."""

from dataclasses import dataclass
from math import ceil, hypot


@dataclass(frozen=True)
class Rect:
    left: float
    bottom: float
    right: float
    top: float

    def overlaps(self, other):
        return (
            self.left < other.right
            and self.right > other.left
            and self.bottom < other.top
            and self.top > other.bottom
        )


class Player:
    SPEED = 190.0
    FOOT_HALF_WIDTH = 13
    FOOT_HEIGHT = 12
    FRAME_WIDTH = 64
    FRAME_HEIGHT = 96
    ANIMATION_ROWS = {"down": 0, "left": 1, "right": 2, "up": 3}
    WALK_FRAMES = (1, 2, 3, 2)

    def __init__(self, x=640.0, y=220.0):
        # Position is the center of the feet, in pico2d's bottom-left coordinates.
        self.x = x
        self.y = y
        self.facing = "down"
        self.walk_time = 0.0
        self.moving = False

    def footprint(self, x, y):
        return Rect(
            x - self.FOOT_HALF_WIDTH,
            y,
            x + self.FOOT_HALF_WIDTH,
            y + self.FOOT_HEIGHT,
        )

    def can_stand(self, x, y, room, obstacles):
        feet = self.footprint(x, y)
        inside = (
            feet.left >= room.left
            and feet.right <= room.right
            and feet.bottom >= room.bottom
            and feet.top <= room.top
        )
        return inside and not any(feet.overlaps(obstacle) for obstacle in obstacles)

    def update(self, dx, dy, dt, room, obstacles):
        if dt < 0:
            raise ValueError("Frame duration must be non-negative")
        if dx or dy:
            if dy:
                self.facing = "up" if dy > 0 else "down"
            else:
                self.facing = "right" if dx > 0 else "left"

        start_x, start_y = self.x, self.y
        length = hypot(dx, dy)
        if length:
            move_x = dx / length * self.SPEED * dt
            move_y = dy / length * self.SPEED * dt
            # Small steps prevent tunneling. Separate axes allow wall sliding.
            steps = max(1, ceil(max(abs(move_x), abs(move_y)) / 5))
            for _ in range(steps):
                next_x = self.x + move_x / steps
                if self.can_stand(next_x, self.y, room, obstacles):
                    self.x = next_x
                next_y = self.y + move_y / steps
                if self.can_stand(self.x, next_y, room, obstacles):
                    self.y = next_y

        self.moving = hypot(self.x - start_x, self.y - start_y) > 0.001
        self.walk_time = self.walk_time + dt if self.moving else 0.0

    @property
    def frame(self):
        if not self.moving:
            return 0
        return self.WALK_FRAMES[int(self.walk_time * 9) % len(self.WALK_FRAMES)]

    def draw(self, sheet):
        row = self.ANIMATION_ROWS[self.facing]
        sheet.clip_draw(
            self.frame * self.FRAME_WIDTH,
            sheet.h - (row + 1) * self.FRAME_HEIGHT,
            self.FRAME_WIDTH,
            self.FRAME_HEIGHT,
            self.x,
            self.y + self.FRAME_HEIGHT / 2 - 5,
        )
