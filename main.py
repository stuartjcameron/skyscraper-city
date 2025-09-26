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


BRICK_SPEED = .5
BRICK_FREQ = 1000
BRICK_CHANCE = .2   # probability of brick appearing in each column in each round
GUN_TOP = .9        # Highest angle for gun (1 = straight up, .5 = horizontal)
GUN_BOTTOM = .2     # Lowest angle for gun
GUN_SPEED = .04     # Speed at which gun rotates
FLOOR_COLLISION_THRESHOLD = 2 # number of pixels distance at which we assume we are on a platform

# Labels for directions
LEFT = 0
RIGHT = 1

FramePerSec = pygame.time.Clock()
 
displaysurface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Skyscraper city")

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
        self.stairs = stairs
        if stairs:
            if tower == RIGHT:
                pygame.draw.line(self.surf, (0, 0, 100), (0, 0), (BRICK_WIDTH, BRICK_HEIGHT))
            else:
                pygame.draw.line(self.surf, (0, 0, 100), (0, BRICK_HEIGHT), (BRICK_WIDTH, 0))

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
        return f"Brick {self.tower}{self.position} top={self.rect.top} bottom={self.rect.bottom} left={self.rect.left} right={self.rect.right} stairs={self.stairs}"

class Player(pygame.sprite.Sprite):
    """
    TODO: To start ascending a diagonal, the player has to move to a new brick that has a diagonal facing the right way,
    with the gun pointing up. Once on the diagonal, they will 'stick' to it and can just walk left or right.
    To start descending they have to move to a new brick with the gun pointing down.
    """
    def __init__(self, tower=LEFT):
        super().__init__() 
        self.surf = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        self.tower = tower
        self.bricks = bricks_by_position[tower]
        self.surf.set_colorkey((255,255,255))
        self.gun_angle = .5
        self.direction = RIGHT
        self.update()
        self.rect = self.surf.get_rect(topleft = (0, HEIGHT - BRICK_HEIGHT - PLAYER_SIZE))
        self.pos = vec(self.rect.midbottom)
        self.vel = vec(0,0)
        self.previous_under = ground
        self.previous_behind = None

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
        
        if pressed_keys[K_1]:
            add_bricks()
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
        under_stairs = getattr(under, "stairs", None)            
        behind = self.behind()
        if not behind == self.previous_behind:
            print("behind", behind) 
        self.previous_behind = behind
        stairs = getattr(behind, "stairs", None)
        if stairs:
            if self.tower == LEFT:
                stairs_y = behind.rect.bottom - max(0, self.pos.x - behind.rect.left)
            else:
                stairs_y = behind.rect.bottom - max(0, behind.rect.right - self.pos.x)
        on_stairs = False
        on_under_stairs = False
        if stairs and self.gun_angle > .5 and self.pos.x < behind.rect.left + 10 and behind.rect.bottom - self.pos.y <= FLOOR_COLLISION_THRESHOLD: # start climbing stairs
            self.acc.y = 0
            self.vel.y = 0
            on_stairs = True
        elif stairs and behind.rect.left <= self.pos.x <= behind.rect.right and max(stairs_y - FLOOR_COLLISION_THRESHOLD, behind.rect.top) <= self.pos.y <= min(stairs_y + FLOOR_COLLISION_THRESHOLD, behind.rect.bottom - FLOOR_COLLISION_THRESHOLD):
            self.acc.y = 0
            self.vel.y = 0
            on_stairs = True
        elif under_stairs and self.gun_angle < .5 and self.pos.x > under.rect.right - 10 and self.pos.y + FLOOR_COLLISION_THRESHOLD >= under.rect.top:
            self.acc.y = 0
            self.vel.y = 0
            on_under_stairs = True
        elif self.pos.y + FLOOR_COLLISION_THRESHOLD >= under.rect.top:
        # player is on, or just slightly above or below, the brick underneath
        # Note, this keeps player on rising platform (provided the platform doesn't rise too fast)
            self.acc.y = 0
            self.vel.y = 0
            self.pos.y = under.rect.top
        else:  # falling
            self.acc.y = GRAVITY
        
        # Resolve movement
        self.acc.x += self.vel.x * FRIC
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc
        if on_stairs:
            #TODO: check if still on stairs - may have moved off them! (although maybe we can just deal with that in the next cycle)
            if self.tower == LEFT:
                self.pos.y = behind.rect.bottom - max(0, self.pos.x - behind.rect.left)
            else:
                self.pos.y = behind.rect.bottom - max(0, behind.rect.right - self.pos.x)
        if on_under_stairs:
            if self.tower == LEFT:
                self.pos.y = under.rect.bottom - max(0, self.pos.x - under.rect.left)
            else:
                self.pos.y = under.rect.bottom - max(0, under.rect.right - self.pos.x)
        if self.pos.x > WIDTH / 2 - PLAYER_SIZE / 2:  # can't go past middle 
            self.pos.x = WIDTH / 2 - PLAYER_SIZE / 2
        if self.pos.x < PLAYER_SIZE / 2:
            self.pos.x = PLAYER_SIZE / 2
        if self.vel.y > 0 and self.pos.y > under.rect.top:   # Check if we've fallen too far
            self.pos.y = under.rect.top
        self.rect.midbottom = self.pos        
        self.update()

    def behind(self):
        """ Check which brick is behind the player centre """
        #if self.direction == LEFT:  # we check the left edge if facing left, right edge if facing right
        #    position = x_to_position(self.rect.left)
        #else:
        #    position = x_to_position(self.rect.right)
        position = x_to_position(self.pos.x)
        if position is not None:
            for brick in self.bricks[position]:
                if brick.rect.top < self.pos.y <= brick.rect.bottom:
                    return brick


    def under(self):
        """ Check whether the player is over a brick or the ground 
          """
        position = x_to_position(self.pos.x)
        if position is not None:
            for brick in self.bricks[position]:
                if self.pos.y - FLOOR_COLLISION_THRESHOLD <= brick.rect.top:  # player is above, or just slightly below, brick top
                    return brick  # We assume the highest are at the start of the list.        
        return ground
           
    def update(self):
        self.surf.fill((255, 255, 255))
        pygame.draw.circle(self.surf, (30, 30, 30), (PLAYER_SIZE / 2, PLAYER_SIZE / 2), PLAYER_SIZE * .3, width=0)
        if self.direction == LEFT:
            direction = -1
        else:
            direction = 1
        gun_end = (PLAYER_SIZE / 2 + direction * math.sin(self.gun_angle * math.pi) * .4 * PLAYER_SIZE,
                   PLAYER_SIZE / 2 + math.cos(self.gun_angle * math.pi) * .4 * PLAYER_SIZE)
        pygame.draw.line(self.surf, (30, 30, 100), (PLAYER_SIZE / 2, PLAYER_SIZE / 2), gun_end, width = 3)

class Ground(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.surf = pygame.Surface((WIDTH, BRICK_HEIGHT))
        self.surf.fill((204, 102, 0))
        self.rect = self.surf.get_rect(topleft = (0, HEIGHT - BRICK_HEIGHT))

bricks_by_position = {LEFT: [[] for _ in range(TOWER_WIDTH)],
                      RIGHT: [[] for _ in range(TOWER_WIDTH)]} 
ground = Ground()
P1 = Player()
players = pygame.sprite.Group(P1)
background = pygame.sprite.Group(ground)
bricks = pygame.sprite.Group()
started = True
add_bricks_event = pygame.USEREVENT
#pygame.time.set_timer(add_bricks_event, BRICK_FREQ)



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
    