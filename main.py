import pygame
import sys
from dataclasses import dataclass

WIDTH, HEIGHT = 800, 800
FPS = 60
CAR_RADIUS = 5
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)

ZONE_SIZE = 20
INTERSECTION_ZONE_SIZE = ZONE_SIZE * 2

DIRS = {'UP': (-1, 0), 'DOWN': (1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1)}

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

def get_zone(row, col):
    return (int(row) // ZONE_SIZE, int(col) // ZONE_SIZE)

def distance(x1, y1, x2, y2):
    return (x2 - x1)**2 + (y2 - y1)**2

def adjacent_zones(zone):
    zrow, zcol = zone
    return [
        (zrow + dr, zcol + dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if not (dr == 0 and dc == 0)
    ]

class Intersection:
    def __init__(self, x, y, state_update_time=120, yellow_pct=0.15):
        self.x = x
        self.y = y
        self.zones = {"UP": [], "DOWN": [], "LEFT": [], "RIGHT": []}
        self.active_light = "UP"
        self.active_light_state = GREEN
        self.tick_count = 0
        self.state_update_time = state_update_time
        self.yellow_pct = yellow_pct

    def draw(self, screen):
        self.tick_count += 1
        self.update_state()

        car = self.zones[self.active_light].pop(0) if self.zones[self.active_light] else None
        if car and self.active_light_state == GREEN:
            car.unblock_intersection()

        offset = 20

        # Draw main intersection circle
        pygame.draw.circle(screen, (0, 0, 255), (self.x, self.y), 20, width=1)

        # Set color for green/red lights
        light_colors = {
            "UP": (0, 255, 0) if self.active_light == "UP" else (255, 0, 0),
            "DOWN": (0, 255, 0) if self.active_light == "DOWN" else (255, 0, 0),
            "LEFT": (0, 255, 0) if self.active_light == "LEFT" else (255, 0, 0),
            "RIGHT": (0, 255, 0) if self.active_light == "RIGHT" else (255, 0, 0),
        }

        radius = 6


        # Draw debug lights in each direction
        pygame.draw.circle(screen, light_colors["UP"], (self.x, self.y - offset), radius)
        pygame.draw.circle(screen, light_colors["DOWN"], (self.x, self.y + offset), radius)
        pygame.draw.circle(screen, light_colors["LEFT"], (self.x - offset, self.y), radius)
        pygame.draw.circle(screen, light_colors["RIGHT"], (self.x + offset, self.y), radius)
    
    def enter(self, car):
        carx, cary = car.col, car.row
        zone = None

        if cary < self.y:
            zone = self.zones["UP"]
        elif cary > self.y:
            zone = self.zones["DOWN"]
        elif carx < self.x:
            zone = self.zones["LEFT"]
        elif carx > self.x:
            zone = self.zones["RIGHT"]

        if car not in zone:
            zone.append(car)

    def update_state(self):
        if self.tick_count % self.state_update_time == 0:
            states = list(self.zones.keys())
            i = states.index(self.active_light)
            self.active_light = states[(i + 1) % len(states)]

@dataclass
class Road:
    x1: int
    y1: int
    x2: int
    y2: int

    def dir(self):
        if self.x1 == self.x2:
            return 'V'
        elif self.y1 == self.y2:
            return 'H'
        else:
            raise ValueError("Invalid road coordinates")
    
    def length(self):
        if self.dir() == 'H':
            return abs(self.x2 - self.x1)
        elif self.dir() == 'V':
            return abs(self.y2 - self.y1)
        else:
            raise ValueError("Invalid road coordinates")

    def intersects(self, other):
        if self.dir() == other.dir():
            return None

        h = self if self.dir() == 'H' else other
        v = other if self.dir() == 'H' else self

        hx_min, hx_max = sorted([h.x1, h.x2])
        vy_min, vy_max = sorted([v.y1, v.y2])

        if hx_min <= v.x1 <= hx_max and vy_min <= h.y1 <= vy_max:
            return (v.x1, h.y1)

        return None

    def draw(self, screen):
        if self.dir() == 'H':
            pygame.draw.line(screen, (0, 0, 0), (self.x1, self.y1), (self.x2, self.y2), 2)
        elif self.dir() == 'V':
            pygame.draw.line(screen, (0, 0, 0), (self.x1, self.y1), (self.x2, self.y2), 2)


class RoadNetwork:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.roads = []
        self.intersections = {}
        self.zone_map = {}
        self.positions = {}

    def add_road(self, road):
        assert road not in self.roads, f"Road {road} already exists"
        self.roads.append(road)
        self._update_intersections()

    def move_from(self, row, col, car):
        zone = get_zone(row, col)
        if car not in self.positions.get(zone, set()):
            breakpoint()
        assert (
            car in self.positions[zone]
        ), f"Car {car} is not in zone {zone} it is in zone {self.positions.get(zone, None)}"

        self.positions[zone].remove(car)

        return True

    def move_to(self, row, col, car):
        zone = get_zone(row, col)

        for other_zone in adjacent_zones(zone):
            for other_car in self.positions.get(other_zone, set()):
                if other_car == car:
                    continue
                if distance(col, row, other_car.col, other_car.row) < (2 * CAR_RADIUS + 2)**2:
                    return False

        if zone not in self.positions:
            self.positions[zone] = set()
        self.positions[zone].add(car)

        return True
    
    def _update_intersections(self):
        for road in self.roads:
            for other in self.roads:
                if road == other:
                    continue
                intersection = road.intersects(other)
                if intersection and intersection not in self.intersections:
                    self.intersections[intersection] = Intersection(*intersection)

    def draw(self, screen):
        for car in cars:
            car.move()
            car.draw()

            for x, y in self.intersections:
                carx, cary = car.col, car.row
                if distance(carx, cary, x, y) < INTERSECTION_ZONE_SIZE**2:
                    car.enter(self.intersections[(x, y)])

        for road in self.roads:
            road.draw(screen)

        for inter in self.intersections.values():
            inter.draw(screen)
    
    def __iadd__(self, other):
        self.add_road(other)
        return self


class Car:
    def __init__(self, network, row, col, direction, speed=2):
        self.network = network
        self.col = col
        self.row = row
        self.dir = direction
        self.speed = speed
        self.state = 'START'
        self.intersection = None

        self.start_pos = (row, col)
        assert self.move_to(row, col)

    def move(self):
        dr, dc = DIRS[self.dir]
        ncol = self.col + (dc * self.speed)
        nrow = self.row + (dr * self.speed)

        if self.state == 'INTERSECTION':
            return
        
        if (
            self.state == 'LEAVE_INTERSECTION'
            and distance(
                self.col, 
                self.row,
                self.intersection.x,
                self.intersection.y
            ) > INTERSECTION_ZONE_SIZE ** 2
        ):
            self.state = "START"

        if self.move_from(self.row, self.col):
            if self.move_to(nrow, ncol):
                if self.state != 'LEAVE_INTERSECTION':
                    self.state = 'START'
                self.row = nrow
                self.col = ncol
            else:
                self.state = 'STOP'
                assert self.move_to(self.row, self.col)
        else:
            assert False
    
    def unblock_intersection(self):
        if self.state == 'INTERSECTION':
            self.state = 'LEAVE_INTERSECTION'
        else:
            assert False
    
    def exited_intersection(self):
        if self.state == 'LEAVE_INTERSECTION':
            self.state = 'START'

    def enter(self, intersection):
        if self.state == 'LEAVE_INTERSECTION':
            return
        intersection.enter(self)
        self.intersection = intersection
        self.state = 'INTERSECTION'

    def draw(self):
        if self.state == 'START':
            color = GREEN
        if self.state == 'STOP' or self.state == 'INTERSECTION':
            color = RED
        if self.state == 'LEAVE_INTERSECTION':
            color = ORANGE

        pygame.draw.circle(screen, color, (int(self.col), int(self.row)), CAR_RADIUS)
    
    def __repr__(self):
        return f"Car({self.row}, {self.col}, {self.dir} origin={self.start_pos})"
    
    def move_to(self, *args):
        return self.network.move_to(*args, car=self)
    def move_from(self, *args):
        return self.network.move_from(*args, car=self)
    
    def __hash__(self):
        return hash(self.start_pos)
    
    def __eq__(self, other):
        if not isinstance(other, Car):
            return False
        return (
            self.start_pos == other.start_pos
        )

 
network = RoadNetwork(WIDTH, HEIGHT)
cars = [
    Car(network, 800, 400, 'UP', 1),
    Car(network, 800 - ZONE_SIZE, 400, 'UP', 1),
    Car(network, 400, 800, 'LEFT', 1),
    Car(network, 400, 800 - ZONE_SIZE, 'LEFT', 1),
    #Car(network, 400, 800 - (2 * ZONE_SIZE), 'LEFT', 1),
]


#cars[1].state = 'INTERSECTION'
#cars[4].state = 'INTERSECTION'

network += Road(0, 400, 800, 400)
network += Road(400, 0, 400, 800)

running = True
prev_str = ""
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((200, 200, 200))
    network.draw(screen)


    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
if running:
    sys.exit()
