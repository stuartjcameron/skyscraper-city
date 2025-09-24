import pygame
from pygame.locals import *
from os import sys
import random
import math
pygame.init()
vec = pygame.math.Vector2  # 2 for two dimensional
 
HEIGHT = 700
WIDTH = 1000
GRAVITY = .5
ACC = .5
FRIC = -0.12
FPS = 60
TOWER_WIDTH = 10   # number of bricks wide each tower is
BRICK_WIDTH = BRICK_HEIGHT = 30    # number of pixels wide each brick is
PLAYER_SIZE = 20
RIGHT_TOWER_EDGE = WIDTH - (TOWER_WIDTH + 1) * BRICK_WIDTH   # left edge of the right tower
LEFT = 0
RIGHT = 1
BRICK_SPEED = .5
BRICK_FREQ = 1000
BRICK_CHANCE = .2   # probability of brick appearing in each column in each round
GUN_TOP = .9        # Highest angle for gun (1 = straight up, .5 = horizontal)
GUN_BOTTOM = .5     # Lowest angle for gun
GUN_SPEED = .04     # Speed at which gun rotates
FLOOR_COLLISION_THRESHOLD = 2 # number of pixels distance at which we assume we are on a platform
FramePerSec = pygame.time.Clock()
 
displaysurface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")

def x_to_position(x):
    """ Convert an x coordinate to a position in the tower """
    if x < WIDTH / 2:
        r = (x - BRICK_WIDTH) / BRICK_WIDTH
    else:
        r = (x - RIGHT_TOWER_EDGE) / BRICK_WIDTH
    if 0 <= r < TOWER_WIDTH:
        return int(r)

def position_to_x(tower, position):
    """ Convert a tower and position to an x coordinate """
    if tower == LEFT:
        return (position + 1) * BRICK_WIDTH
    else:
        return RIGHT_TOWER_EDGE + position * BRICK_WIDTH

class Brick(pygame.sprite.Sprite):
    """ Bricks appear in the floor and move up one space, pushing up everything above them """
    def __init__(self, tower, position, stairs):
        super().__init__()
        self.surf = pygame.Surface((BRICK_WIDTH, BRICK_HEIGHT))
        self.surf.fill((100, 100, 100))
        self.tower = tower
        self.position = position
        x = position_to_x(tower, position)
        self.rect = self.surf.get_rect(topleft=(x, HEIGHT - BRICK_HEIGHT))
        pygame.draw.line(self.surf, (0, 0, 100), (0, 0), (BRICK_WIDTH, 0), width=1)
        if not stairs:
            self.stairs = 0
            
        elif random.random() > .5:
            self.stairs = 1  # right-up stairs
            pygame.draw.line(self.surf, (0, 0, 100), (0, BRICK_HEIGHT), (BRICK_WIDTH, 0))
        else:
            self.stairs = 2  # left-up stairs
            pygame.draw.line(self.surf, (0, 0, 100), (0, 0), (BRICK_WIDTH, BRICK_HEIGHT))

        #pygame.draw.rect(self.surf, (0,0,100), Rect(1,1,BRICK_WIDTH-1,BRICK_HEIGHT-1), width=2)
        self.pos = vec(self.rect.midbottom)
        self.goalY = self.pos.y
        self.go_higher()

    def go_higher(self):
        self.goalY -= BRICK_HEIGHT
        self.moving = True
    
    def move(self):
        if self.moving:
            if self.goalY > self.pos.y:
                self.pos.y += BRICK_SPEED
                if self.pos.y >= self.goalY:
                    self.pos.y = self.goalY
                    self.moving = False
            elif self.goalY < self.pos.y:
                self.pos.y -= BRICK_SPEED
                if self.pos.y <= self.goalY:
                    self.pos.y = self.goalY
                    self.moving = False
        self.rect.midbottom = self.pos

    def __repr__(self):
        return f"Brick {self.tower} {self.position} {self.rect.top}"

class Player(pygame.sprite.Sprite):
    """
    TODO:
    When player changes column, update self.on
    
    """
    def __init__(self):
        super().__init__() 
        self.surf = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        self.tower = LEFT
        self.surf.set_colorkey((255,255,255))
        self.gun_angle = .5
        self.direction = RIGHT
        self.update()
        self.rect = self.surf.get_rect(topleft = (0, HEIGHT - BRICK_HEIGHT - PLAYER_SIZE))
        self.pos = vec(self.rect.midbottom)
        self.vel = vec(0,0)
        self.previous_under = ground      # If they are on a brick this will be updated to (brick, diagonal)
                            # If they are falling this is updated to None

    def move(self):
        self.acc = vec(0, 0)
        pressed_keys = pygame.key.get_pressed()
        
        # Adjust gun direction
        if pressed_keys[K_UP]:
            self.gun_angle += GUN_SPEED
            if self.gun_angle > GUN_TOP:
                self.gun_angle = GUN_TOP
        if pressed_keys[K_DOWN]:
            self.gun_angle -= GUN_SPEED
            if self.gun_angle < GUN_BOTTOM:
                self.gun_angle = GUN_BOTTOM
        
        # Check horizontal movement
        if pressed_keys[K_LEFT]:
            self.acc.x = -ACC
            self.direction = LEFT
        if pressed_keys[K_RIGHT]:
            self.acc.x = ACC
            self.direction = RIGHT
        
        # Check vertical movement
        under = self.under()
        if not under == self.previous_under:
            print("under", under)
        self.previous_under = under
        if under.rect.top - self.pos.y <= FLOOR_COLLISION_THRESHOLD:  # on the brick / ground
            self.acc.y = 0
            self.vel.y = 0
            self.pos.y = under.rect.top
        else:  # falling
            self.acc.y = GRAVITY
        
        # Resolve movement
        self.acc.x += self.vel.x * FRIC
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc
        if self.pos.x > WIDTH / 2 - PLAYER_SIZE / 2:  # can't go past middle 
            self.pos.x = WIDTH / 2 - PLAYER_SIZE / 2
        if self.pos.x < PLAYER_SIZE / 2:
            self.pos.x = PLAYER_SIZE / 2
        if self.vel.y > 0 and self.pos.y > under.rect.top:   # Check if we've fallen too far
            self.pos.y = under.rect.top
        self.rect.midbottom = self.pos        
        self.update()

    def under(self):
        """ Check whether the player is over a brick or the ground 
         TODO: still working  inconsistently at the moment - check it. """
        position = x_to_position(self.pos.x)
        if position is not None:
            for brick in bricks_by_position[self.tower][position]:
                if self.pos.y - FLOOR_COLLISION_THRESHOLD <= brick.rect.top:
                    return brick  # We assume the highest are at the start of the list.        
        return ground
           
    def update(self):
        self.surf.fill((255, 255, 255))
        pygame.draw.circle(self.surf, (30, 30, 30), (PLAYER_SIZE / 2, PLAYER_SIZE / 2), PLAYER_SIZE * .3, width=0)
        if self.direction == LEFT:
            direction = -1
        else:
            direction = 1
        gun_x = PLAYER_SIZE / 2 + direction * math.sin(self.gun_angle * math.pi) * .4 * PLAYER_SIZE
        gun_y = PLAYER_SIZE / 2 + math.cos(self.gun_angle * math.pi) * .4 * PLAYER_SIZE
        pygame.draw.line(self.surf, (30, 30, 100), (PLAYER_SIZE / 2, PLAYER_SIZE / 2), (gun_x, gun_y), width = 3)

class Ground(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.surf = pygame.Surface((WIDTH, BRICK_HEIGHT))
        self.surf.fill((204, 102, 0))
        self.rect = self.surf.get_rect(topleft = (0, HEIGHT - BRICK_HEIGHT))
 
ground = Ground()
P1 = Player()

players = pygame.sprite.Group(P1)
background = pygame.sprite.Group(ground)
bricks = pygame.sprite.Group()
bricks_by_position = {LEFT: [[] for _ in range(TOWER_WIDTH)],
                      RIGHT: [[] for _ in range(TOWER_WIDTH)]}
started = True
add_bricks_event = pygame.USEREVENT
pygame.time.set_timer(add_bricks_event, BRICK_FREQ)



def add_bricks():
    #print('adding bricks')
    for tower in [LEFT, RIGHT]:
        to_add = [i for i in range(TOWER_WIDTH) if random.random() < BRICK_CHANCE]
        if to_add:
            #staircase = random.choice(to_add)
            #print(to_add)
            for position in to_add:
                for brick in bricks_by_position[tower][position]:
                    brick.go_higher()
                if random.random() < .2:
                    brick = Brick(tower, position, True)
                else:
                    brick = Brick(tower, position, False)
                bricks.add(brick)
                bricks_by_position[tower][position].append(brick)
                #print("at", tower, position)

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == USEREVENT:
            add_bricks()

    displaysurface.fill((0,102,204))
    P1.move()
    for brick in bricks:
        brick.move()
    
    for entity in bricks:
        displaysurface.blit(entity.surf, entity.rect)
    for entity in background:
        displaysurface.blit(entity.surf, entity.rect)
    for entity in players:
        displaysurface.blit(entity.surf, entity.rect)
        
    
    pygame.display.update()
    FramePerSec.tick(FPS)
    