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
 
FramePerSec = pygame.time.Clock()
 
displaysurface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")

def x_to_position(x):
    """ Convert an x coordinate to a tower, position (column) tuple """
    if x < WIDTH / 2:
        return LEFT, (x - BRICK_WIDTH) // BRICK_WIDTH
    else:
        return RIGHT, (x - WIDTH) // BRICK_WIDTH

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
        self.acc = vec(0,0)
        self.on = ground      # If they are on a brick this will be updated to (brick, diagonal)
                            # If they are falling this is updated to None

    def move(self):
        self.acc = vec(0,0)
        #_, start_position = x_to_position(self.pos.x)   # not used because we always check for bricks coming up
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[K_UP]:
            self.gun_angle += GUN_SPEED
            if self.gun_angle > GUN_TOP:
                self.gun_angle = GUN_TOP
        if pressed_keys[K_DOWN]:
            self.gun_angle -= GUN_SPEED
            if self.gun_angle < GUN_BOTTOM:
                self.gun_angle = GUN_BOTTOM
        if pressed_keys[K_LEFT]:
            self.acc.x = -ACC
            self.direction = LEFT
        if pressed_keys[K_RIGHT]:
            self.acc.x = ACC
            self.direction = RIGHT
        
        # Check vertical movement
        if self.on is None:   # falling
            self.acc.y = GRAVITY 
        else:  # on brick or ground
            self.vel.y = 0
            self.pos.y = self.on.rect.top
        
        # Resolve movement
        self.acc.x += self.vel.x * FRIC
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc
        if self.pos.x > WIDTH / 2 - PLAYER_SIZE / 2:  # can't go past middle 
            self.pos.x = WIDTH / 2 - PLAYER_SIZE / 2
        if self.pos.x < PLAYER_SIZE / 2:
            self.pos.x = PLAYER_SIZE / 2
        self.rect.midbottom = self.pos

        # Check new position
        _, position = x_to_position(self.pos.x)
        self.on = self.check_what_on(position)
        # Note, the above check could be optimized. Does not need to be checked in every cycle. Only when
        # (1) we move to a new column position
        # (2) we are falling (and then need to be more careful in collision check)
        # (3) we are on the ground and a brick in the same position is rising
        
        self.update()

    def check_what_on(self, position):
        """ Check what the player is on.
             Scenarios:
             - in the air -> fall until we hit a brick or the ground. Bricks may be coming up under the player, 
                so we have to check this continuously while falling.
             - on a brick (top of brick is close to bottom of player) -> move up or down if the brick moves.
             - on a slope (slope is close to bottom of player) -> move up or down if the brick moves.
               L/R moves up or down the slope.
            - on the ground (ground is close to bottom of player and there is no brick coming up) -> as usual
            """
        for brick in bricks:
            if brick.tower == self.tower and brick.position == position and 2 > brick.rect.top - self.rect.bottom >= 0:
                if self.on != brick:
                    print("on", brick)
                return brick
        if 2 > ground.rect.top - self.rect.bottom >= 0:  # close to ground
            if self.on != ground:
                print("on ground")
            return ground
        if self.on is not None:
            print("Falling")
        return None
           
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
bricks_by_position = {LEFT: [], RIGHT: []}
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
                for brick in bricks:
                    if brick.position == position and brick.tower == tower:
                        brick.go_higher()
                if random.random() < .2:
                    bricks.add(Brick(tower, position, True))
                else:
                    bricks.add(Brick(tower, position, False))
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
    