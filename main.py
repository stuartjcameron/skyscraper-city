import pygame
from pygame.locals import *
from os import sys
import random

pygame.init()
vec = pygame.math.Vector2  # 2 for two dimensional
 
HEIGHT = 700
WIDTH = 1000
ACC = 0.5
FRIC = -0.12
FPS = 60
TOWER_WIDTH = 10   # number of bricks wide each tower is
BRICK_WIDTH = BRICK_HEIGHT = 30    # number of pixels wide each brick is
RIGHT_TOWER_EDGE = WIDTH - TOWER_WIDTH * BRICK_WIDTH   # left edge of the right tower
LEFT = 0
RIGHT = 1
BRICK_SPEED = .5
BRICK_FREQ = 1000
BRICK_CHANCE = .2   # probability of brick appearing in each column in each round

 
FramePerSec = pygame.time.Clock()
 
displaysurface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")


class Brick(pygame.sprite.Sprite):
    """ Bricks appear in the floor and move up one space, pushing up everything above them """
    def __init__(self, tower, position):
        super().__init__()
        self.surf = pygame.Surface((BRICK_WIDTH, BRICK_HEIGHT))
        self.surf.fill((100, 100, 100))
        self.tower = tower
        self.position = position
        if tower == LEFT:
            x = position * BRICK_WIDTH
        else:
            x = RIGHT_TOWER_EDGE + position * BRICK_WIDTH
        self.rect = self.surf.get_rect(topleft=(x, HEIGHT - BRICK_HEIGHT))
        pygame.draw.rect(self.surf, (0,0,100), Rect(1,1,BRICK_WIDTH-1,BRICK_HEIGHT-1), width=2)
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

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__() 
        self.surf = pygame.Surface((30, 30))
        self.surf.fill((128,255,40))
        self.rect = self.surf.get_rect(center = (10, 420))
        self.pos = vec((10, 385))
        self.vel = vec(0,0)
        self.acc = vec(0,0)

    def move(self):
        self.acc = vec(0,0)
    
        pressed_keys = pygame.key.get_pressed()
                
        if pressed_keys[K_LEFT]:
            self.acc.x = -ACC
        if pressed_keys[K_RIGHT]:
            self.acc.x = ACC
        self.acc.x += self.vel.x * FRIC
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc
        if self.pos.x > WIDTH:
            self.pos.x = 0
        if self.pos.x < 0:
            self.pos.x = WIDTH
        self.rect.midbottom = self.pos

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

started = False

add_bricks_event = pygame.USEREVENT
def add_bricks():
    print('adding bricks')
    for tower in [LEFT, RIGHT]:
        for position in range(TOWER_WIDTH):
            if random.random() < BRICK_CHANCE:
                # Move all the other bricks in the same column up
                for brick in bricks:
                    if brick.position == position and brick.tower == tower:
                        brick.go_higher()
                bricks.add(Brick(tower, position))
                print("at", tower, position)



while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == USEREVENT:
            add_bricks()

    displaysurface.fill((0,102,204))
    if started:
        P1.move()
        for brick in bricks:
            brick.move()
    elif pygame.key.get_pressed()[K_RETURN]:
        pygame.time.set_timer(add_bricks_event, BRICK_FREQ)
        started = True
    
    for entity in bricks:
        displaysurface.blit(entity.surf, entity.rect)
    for entity in background:
        displaysurface.blit(entity.surf, entity.rect)
    for entity in players:
        displaysurface.blit(entity.surf, entity.rect)
        
    
    pygame.display.update()
    FramePerSec.tick(FPS)
    