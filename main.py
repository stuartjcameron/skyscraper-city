import pygame
from pygame.locals import *
from os import sys
 
pygame.init()
vec = pygame.math.Vector2  # 2 for two dimensional
 
HEIGHT = 700
WIDTH = 1000
ACC = 0.5
FRIC = -0.12
FPS = 60
TOWER_WIDTH = 10   # number of bricks wide each tower is
BRICK_WIDTH = 30    # number of pixels wide each brick is
RIGHT_TOWER_EDGE = WIDTH - TOWER_WIDTH * BRICK_WIDTH   # left edge of the right tower
LEFT = 0
RIGHT = 1

 
FramePerSec = pygame.time.Clock()
 
displaysurface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")




class Brick(pygame.sprite.Sprite):
    def __init__(self, tower, position):
        super().__init__()
        self.surf = pygame.Surface((30, 30))
        self.surf.fill((100, 100, 100))
        self.tower = tower
        self.position = position
        if tower == LEFT:
            x = position * BRICK_WIDTH
        else:
            x = RIGHT_TOWER_EDGE + position * BRICK_WIDTH
        self.rect = self.surf.get_rect(topleft=(x, HEIGHT - 100))
        pygame.draw.rect(self.surf, (0,0,100), Rect(1,1,29,29), width=2)
        self.pos = self.rect.midbottom
        self.vel = vec(0, 0)
        self.acc = vec(0, -.5)

    def move(self):
        self.acc.y += self.vel.y * FRIC
        self.vel += self.acc
        self.pos += self.vel + .5 * self.acc
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

class platform(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.surf = pygame.Surface((WIDTH, 20))
        self.surf.fill((204, 102, 0))
        self.rect = self.surf.get_rect(center = (WIDTH/2, HEIGHT - 10))
 
PT1 = platform()
P1 = Player()
B1 = Brick(LEFT, 1)


all_sprites = pygame.sprite.Group()
all_sprites.add(PT1)
all_sprites.add(P1)
all_sprites.add(B1)
 
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
    
    P1.move()
    B1.move()
    displaysurface.fill((0,102,204))
 
    for entity in all_sprites:
        displaysurface.blit(entity.surf, entity.rect)
    
    
    pygame.display.update()
    FramePerSec.tick(FPS)
    