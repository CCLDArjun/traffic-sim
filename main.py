import pygame
import sys

WIDTH, HEIGHT = 800, 800
FPS = 60
CAR_RADIUS = 5
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ZONE_SIZE = 20

DIRS = {'UP': (-1, 0), 'DOWN': (1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1)}

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


def get_zone(row, col):
    return (int(row) // ZONE_SIZE, int(col) // ZONE_SIZE)

class Intersection:
    def __init__(self, x, y):
        ...

class RoadNetwork:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.roads = []
        self.intersections = {}
        self.zone_map = {}
        self.positions = {}

    def add_horizontal_road(self, y):
        self.roads.append(('H', y))
        self._update_intersections()

    def add_vertical_road(self, x):
        self.roads.append(('V', x))
        self._update_intersections()

    def move_from(self, row, col, car):
        zone = get_zone(row, col)
        assert car == self.positions[zone], f"Car {car} is not in zone {zone}"
        del self.positions[zone]
        return True

    def move_to(self, row, col, car):
        zone = get_zone(row, col)

        if zone in self.positions and self.positions[zone] != car:
            print(f"Collision detected at zone {zone} with car {self.positions[zone]} and {car}")
            return False
        
        self.positions[zone] = car
    
        return True
    
    def _update_intersections(self):
        h_roads = [y for dir, y in self.roads if dir == 'H']
        v_roads = [x for dir, x in self.roads if dir == 'V']
        for x in v_roads:
            for y in h_roads:
                self.intersections[(x, y)] = Intersection(x, y)

    def draw(self, screen):
        for dir, pos in self.roads:
            if dir == 'H':
                pygame.draw.line(screen, (50, 50, 50), (0, pos), (self.width, pos), 2)
            elif dir == 'V':
                pygame.draw.line(screen, (50, 50, 50), (pos, 0), (pos, self.height), 2)

        for (x, y), inter in self.intersections.items():
            pygame.draw.circle(screen, (0, 0, 255), (x, y), 30, width=1)


class Car:
    def __init__(self, network, row, col, direction, speed=2):
        print(row, col)
        self.network = network
        self.col = col
        self.row = row
        self.dir = direction
        self.speed = speed
        self.state = 'START'

        self.start_pos = (row, col)
        assert self.move_to(row, col)

    def move(self):
        dr, dc = DIRS[self.dir]
        ncol = self.col + (dc * self.speed)
        nrow = self.row + (dr * self.speed)

        if self.move_from(self.row, self.col):
            if self.move_to(nrow, ncol):
                self.state = 'START'
                self.row = nrow
                self.col = ncol
            else:
                self.state = 'STOP'
                self.move_to(self.row, self.col)

        print(f"Car at ({self.row}, {self.col}) moving {self.dir} to ({nrow}, {ncol})")

    def draw(self):
        color = RED if self.state == 'STOP' else GREEN
        pygame.draw.circle(screen, color, (int(self.col), int(self.row)), CAR_RADIUS)
    
    def __repr__(self):
        return f"Car({self.row}, {self.col}, {self.dir} origin {self.start_pos})"
    
    def move_to(self, *args):
        return self.network.move_to(*args, car=self)
    def move_from(self, *args):
        return self.network.move_from(*args, car=self)
 
network = RoadNetwork(WIDTH, HEIGHT)
cars = [
    Car(network, 800, 400, 'UP', 1),
    Car(network, 800 - ZONE_SIZE, 400, 'UP', 1),
    Car(network, 400, 800, 'LEFT', 1),
    Car(network, 400, 800 - ZONE_SIZE, 'LEFT', 1),
    Car(network, 400, 800 - (2 * ZONE_SIZE), 'LEFT', 1),
]

network.add_horizontal_road(400)
network.add_vertical_road(400)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((200, 200, 200))
    network.draw(screen)

    for car in cars:
        car.move()
        car.draw()
    
    print(network.positions)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
if running:
    sys.exit()
