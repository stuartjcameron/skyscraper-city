import pygame
from pygame.locals import *
from os import sys
import random
import math
pygame.init()
vec = pygame.math.Vector2  # 2 for two dimensional
import sys

# The major, minor version numbers your require
MIN_VER = (3, 13)

if sys.version_info[:2] < MIN_VER:
    sys.exit(
        "This game requires Python {}.{}.".format(*MIN_VER)
    )
    
HEIGHT = 700
WIDTH = 1000
GRAVITY = .5
FPS = 60
TOWER_WIDTH = 10   # number of bricks wide each tower is
BRICK_WIDTH = BRICK_HEIGHT = 30    # number of pixels wide each brick is
RIGHT_TOWER_EDGE = WIDTH - (TOWER_WIDTH + 1) * BRICK_WIDTH   # left edge of the right tower

BRICK_SPEED = .5
BRICK_FREQ = 1000
BRICK_CHANCE = .2   # probability of brick appearing in each column in each round
BRICK_COLOUR = (100, 100, 100)

ACC = .5
FRIC = -0.12
PLAYER_SIZE = 20
GUN_TOP = .9        # Highest angle for gun (1 = straight up, .5 = horizontal)
GUN_BOTTOM = .2     # Lowest angle for gun
GUN_SPEED = .04     # Speed at which gun rotates
FLOOR_COLLISION_THRESHOLD = 2 # number of pixels distance at which we assume we are on a platform

MAX_SHOOT_TIME = 1000  # hold down fire button to shoot further, up to this max (ms)
BULLET_SIZE = 5
BULLET_SPEED_MIN = 12
BULLET_SPEED_MAX = 16

WIN_PLATFORM_HEIGHT = 10      # No bricks you have to climb before reaching winning platform

# Labels for directions / commands
LEFT = 0
RIGHT = 1
UP = 2
DOWN = 3
FIRE = 4

KEYS = { 
    1: {
        K_LSHIFT: FIRE,
        K_w: UP,
        K_a: LEFT,
        K_s: DOWN,
        K_d: RIGHT
    },
    2: {
        K_COMMA: FIRE,
        K_UP: UP,
        K_DOWN: DOWN,
        K_LEFT: LEFT,
        K_RIGHT: RIGHT
    },
}
END_GAME_FONT = pygame.freetype.SysFont('sans', 40)

#TODO
# winning platform - adjust height
# make it easier to climb slope and get on top of same brick - currently tends to fall off
# too easy to slip down when bricks move up - adjust mechanics
# TODO: give a warning before bricks grow - allowing player to move to best position
# TODO: ensure bricks remain aligned - 1px gap can allow player to slip off!

FramePerSec = pygame.time.Clock()
displaysurface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Skyscraper city")
sprites = {}    # global for all the sprites and groups


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
        self.surf.fill(BRICK_COLOUR)
        self.tower = tower
        self.position = position
        self.column = sprites["bricks_by_position"][tower][position]
        x = position_to_x(tower, position)
        self.rect = self.surf.get_rect(topleft=(x, HEIGHT - BRICK_HEIGHT))
        self.stairs = stairs
        self.pos = vec(self.rect.midbottom)
        self.goalY = self.pos.y
        self.vel = vec(0, 0)
        self.acc = vec(0, GRAVITY)
        self.go_higher()
        self.draw()

    def go_higher(self):
        self.goalY -= BRICK_HEIGHT
        self.moving_up = True

    def below(self):
        """ Return the brick or ground that is below this brick """
        i = self.column.index(self)
        if i < len(self.column) - 1:
            return self.column[i + 1]
        else:
            return sprites["ground"]

    def move(self):
        below = self.below()
        if below.rect.top + 1 > self.pos.y:  # nothing directly under us, so fall
            step = min(below.rect.top + 1 - self.pos.y, self.vel.y + .5 * self.acc.y)
            self.pos.y += step
            self.goalY += step
            self.vel.y += self.acc.y
        else:                           # brick / ground directly below us. May need to move up for another brick underneath.
            self.vel = vec(0, 0)
            if self.moving_up:
                if self.goalY > self.pos.y:
                    self.pos.y += BRICK_SPEED
                    if self.pos.y >= self.goalY:
                        self.pos.y = self.goalY
                        self.moving_up = False
                        
                elif self.goalY < self.pos.y:
                    self.pos.y -= BRICK_SPEED
                    if self.pos.y <= self.goalY:
                        self.pos.y = self.goalY
                        self.moving_up = False
                        
        self.rect.midbottom = self.pos
        #self.draw()  # No need to redraw on each cycle - bricks stay the same

    def draw(self):
        self.surf.fill(BRICK_COLOUR)
        pygame.draw.line(self.surf, (0, 0, 100), (0, 0), (BRICK_WIDTH, 0), width=1)
        
        if self.stairs:
            if self.tower == RIGHT:
                pygame.draw.line(self.surf, (0, 0, 100), (0, 0), (BRICK_WIDTH, BRICK_HEIGHT))
            else:
                pygame.draw.line(self.surf, (0, 0, 100), (0, BRICK_HEIGHT), (BRICK_WIDTH, 0))

    def __repr__(self):
        return f"Brick {self.tower}{self.position} top={self.rect.top} bottom={self.rect.bottom} left={self.rect.left} right={self.rect.right} stairs={self.stairs}"

class Player(pygame.sprite.Sprite):
    """
    Sprite for a player (may be human or computer controlled)
    """
    def __init__(self, tower):
        super().__init__() 
        self.surf = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        self.tower = tower
        self.bricks = sprites["bricks_by_position"][tower]
        self.surf.set_colorkey((255,255,255))
        self.gun_angle = .5
        if tower == LEFT:
            self.direction = RIGHT
            start_x = 0
        else:
            self.direction = LEFT
            start_x = WIDTH - PLAYER_SIZE
        self.rect = self.surf.get_rect(topleft = (start_x, HEIGHT - BRICK_HEIGHT - PLAYER_SIZE))
        self.centre = vec(PLAYER_SIZE / 2, PLAYER_SIZE / 2)
        self.pos = vec(self.rect.midbottom)
        self.vel = vec(0,0)
        self.previous_under = sprites["ground"]
        self.previous_behind = None
        self.shoot_start_time = None
        self.update()
        
    def move(self, command):
        self.acc = vec(0, 0)
        
        # Firing
        if FIRE in command and self.shoot_start_time is None:
            self.start_shoot()
        elif (FIRE not in command) and self.shoot_start_time is not None:  # release shift key 
            self.finish_shoot()

        # Adjust gun direction
        if UP in command:
            self.gun_angle += GUN_SPEED
            if self.gun_angle > GUN_TOP:
                self.gun_angle = GUN_TOP
            #print('gun', self.gun_end())
        if DOWN in command:
            self.gun_angle -= GUN_SPEED
            if self.gun_angle < GUN_BOTTOM:
                self.gun_angle = GUN_BOTTOM
            #print('gun', self.gun_end())
        
        if "cheat" in command:
            add_bricks()
        # Check horizontal movement
        if LEFT in command:
            self.acc.x = -ACC
            self.direction = LEFT
        if RIGHT in command:
            self.acc.x = ACC
            self.direction = RIGHT
        
        # Check vertical movement
        under = self.under()
        self.previous_under = under
        under_stairs = getattr(under, "stairs", None)            
        behind = self.behind()
        # if not behind == self.previous_behind:
            # print("behind", behind) 
        self.previous_behind = behind
        stairs = getattr(behind, "stairs", None)
        if stairs:
            if self.tower == LEFT:
                stairs_y = behind.rect.bottom - max(0, self.pos.x - behind.rect.left)
            else:
                stairs_y = behind.rect.bottom - max(0, behind.rect.right - self.pos.x)
        on_stairs = False
        on_under_stairs = False

        if (stairs and self.gun_angle > .5 and 
            ((self.pos.x < behind.rect.left + 10 and self.tower == LEFT) or (self.pos.x > behind.rect.right - 10 and self.tower == RIGHT)) and
            behind.rect.bottom - self.pos.y <= FLOOR_COLLISION_THRESHOLD): # start climbing stairs
            self.acc.y = 0
            self.vel.y = 0
            on_stairs = True
        elif stairs and behind.rect.left <= self.pos.x <= behind.rect.right and max(stairs_y - FLOOR_COLLISION_THRESHOLD, behind.rect.top) <= self.pos.y <= min(stairs_y + FLOOR_COLLISION_THRESHOLD, behind.rect.bottom - FLOOR_COLLISION_THRESHOLD):
            self.acc.y = 0
            self.vel.y = 0
            on_stairs = True
        elif (under_stairs and self.gun_angle < .5 and 
              ((self.pos.x > under.rect.right - 10 and self.tower == LEFT) or (self.pos.x < under.rect.left + 10 and self.tower == RIGHT)) and
                self.pos.y + FLOOR_COLLISION_THRESHOLD >= under.rect.top):
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
        if self.tower == LEFT:
            if self.pos.x > WIDTH / 2 - PLAYER_SIZE / 2:  # can't go past middle 
                self.pos.x = WIDTH / 2 - PLAYER_SIZE / 2
            if self.pos.x < PLAYER_SIZE / 2:
                self.pos.x = PLAYER_SIZE / 2
        if self.tower == RIGHT:
            if self.pos.x > WIDTH - PLAYER_SIZE / 2:  # can't go past middle 
                self.pos.x = WIDTH - PLAYER_SIZE / 2
            if self.pos.x < WIDTH / 2 + PLAYER_SIZE / 2:
                self.pos.x = WIDTH / 2 + PLAYER_SIZE / 2
        if self.vel.y > 0 and self.pos.y > under.rect.top:   # Check if we've fallen too far
            self.pos.y = under.rect.top
        self.rect.midbottom = self.pos        
        self.update()

    def start_shoot(self):
        self.shoot_start_time = pygame.time.get_ticks()

    def finish_shoot(self):
        print('shoot', self.gun_end(), self.direction_vector(), pygame.time.get_ticks() - self.shoot_start_time)
        sprites["bullets"].add(Bullet(tower=self.tower,
                           pos=self.rect.topleft + self.gun_end(),
                           direction=self.direction_vector(),
                           speed=self.shoot_power()))
        self.shoot_start_time = None
    
    def shoot_power(self):
        if self.shoot_start_time is not None:
            return min(1, (pygame.time.get_ticks() - self.shoot_start_time) / MAX_SHOOT_TIME)
        return 0

    def behind(self):
        """ Check which brick is behind the player centre """
        position = x_to_position(self.pos.x)
        if position is not None:
            for brick in self.bricks[position]:
                if brick.rect.top < self.pos.y <= brick.rect.bottom:
                    return brick


    def under(self):
        """ Check whether the player is over a brick, the ground or the winning platform
          """
        position = x_to_position(self.pos.x)
        if position is not None:
            for brick in self.bricks[position]:
                if self.pos.y - FLOOR_COLLISION_THRESHOLD <= brick.rect.top:  # player is above, or just slightly below, brick top
                    return brick  # We assume the highest are at the start of the list.        
        wp = sprites["win_platform"].rect
        if wp.left < self.pos.x < wp.right and self.pos.y <= wp.top:
            return sprites["win_platform"]      
        return sprites["ground"]

    def direction_vector(self):
        if self.direction == LEFT:
            return vec(-math.sin(self.gun_angle * math.pi), math.cos(self.gun_angle * math.pi))
        else:
            return vec(math.sin(self.gun_angle * math.pi), math.cos(self.gun_angle * math.pi))
        
    def gun_end(self):
        return self.centre + self.direction_vector() * PLAYER_SIZE * .4
    
    def update(self):
        self.surf.fill((255, 255, 255))
        pygame.draw.circle(self.surf, (30, 30, 30), self.centre, PLAYER_SIZE * .3, width=0)
        red = 255 * self.shoot_power()
        pygame.draw.line(self.surf, (red, 30, 100), self.centre, self.gun_end(), width=3)

class Bullet(pygame.sprite.Sprite):
    """ Bullet goes straight through first brick it touches. Second brick explodes destroying all the bricks around it. """
    def __init__(self, tower, pos, direction, speed):
        super().__init__()
        self.tower = tower
        self.pos = pos
        self.vel = direction * (BULLET_SPEED_MIN + speed * (BULLET_SPEED_MAX - BULLET_SPEED_MIN))
        self.acc = vec(0, GRAVITY)
        self.surf = pygame.Surface((BULLET_SIZE, BULLET_SIZE))
        self.surf.set_colorkey((255,255,255))
        self.hit = None
        self.rect = self.surf.get_rect(center=pos)    
        self.hit_floor_time = None 

    def move(self):
        if self.pos.y == sprites["ground"].rect.top and self.hit_floor_time is not None and pygame.time.get_ticks() - self.hit_floor_time > 1000:
            print("bullet removed from ground", self)
            self.kill()
            return
        
        self.pos += self.vel + .5 * self.acc
        self.vel += self.acc
        self.rect.center = self.pos

        if self.pos.y >= sprites["ground"].rect.top and self.hit_floor_time is None:
            self.pos.y = sprites["ground"].rect.top
            self.vel = vec(0, 0)
            self.acc = vec(0, 0)
            self.hit_floor_time = pygame.time.get_ticks()
            print("bullet hit ground", self, self.hit_floor_time)
            
        collisions = pygame.sprite.spritecollide(self, sprites["bricks"], False)
        for brick in collisions:
            if brick.tower != self.tower:
                self.hit_brick(brick)
        self.update()

    def hit_brick(self, brick):
        remove_brick(brick)
        self.kill()  
        
    def hit_brick_later(self, brick):
        if self.hit is None:  # go straight through the first brick you hit
            self.hit = brick
            remove_brick(brick)
        else:   # then make the next one explode taking the surrounding bricks with it
            explode_brick(brick)
        self.kill() 

    def update(self):
        self.surf.fill((255, 255, 255))
        pygame.draw.circle(self.surf, (0, 0, 0), (BULLET_SIZE / 2, BULLET_SIZE / 2), BULLET_SIZE, width=0)



class Platform(pygame.sprite.Sprite):
    def __init__(self, pos, width):
        super().__init__()
        self.surf = pygame.Surface((width, BRICK_HEIGHT))
        self.surf.fill((204, 102, 0))
        self.rect = self.surf.get_rect(topleft=pos)

class Cup(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.surf = pygame.image.load("cup.png")
        self.surf.set_colorkey((255,255,255))
        self.rect = self.surf.get_rect(midbottom=pos)




def add_bricks():
    #print('adding bricks')
    for tower in [LEFT, RIGHT]:
        to_add = [i for i in range(TOWER_WIDTH) if random.random() < BRICK_CHANCE]
        if to_add:
            #staircase = random.choice(to_add)
            #print(to_add)
            for position in to_add:
                for brick in sprites["bricks_by_position"][tower][position]:
                    brick.go_higher()
                if random.random() < .2:
                    brick = Brick(tower, position, True)
                else:
                    brick = Brick(tower, position, False)
                sprites["bricks"].add(brick)
                sprites["bricks_by_position"][tower][position].append(brick)
                #print("at", tower, position)

def remove_brick(brick):
    print("remove", brick)
    c = brick.column
    brick.column.remove(brick)
    brick.kill()  
    

# TODO: hitting bricks causes more damage to the surrounding bricks
# TODO: animation of bricks getting hot then disintegrating

def explode_brick(brick):
    remove_brick(brick) # TODO:also remove the surrounding bricks


def initial_set_up():
    sprites["bricks_by_position"] = {LEFT: [[] for _ in range(TOWER_WIDTH)],
                      RIGHT: [[] for _ in range(TOWER_WIDTH)]} 
    sprites["ground"] = Platform(pos=(0, HEIGHT - BRICK_HEIGHT), width=WIDTH)
    sprites["win_platform"] = Platform(pos=(BRICK_WIDTH + TOWER_WIDTH * BRICK_WIDTH,
                             HEIGHT - (BRICK_HEIGHT - 1) * (1 + WIN_PLATFORM_HEIGHT)) + 2,
                        width=WIDTH-2*BRICK_HEIGHT-2*TOWER_WIDTH*BRICK_HEIGHT) 
    sprites["cup"] = Cup(pos=(sprites["win_platform"].rect.centerx, sprites["win_platform"].rect.top))
    sprites["players_dict"] = {1: Player(LEFT), 2: Player(RIGHT)}
    sprites["players_group"] = pygame.sprite.Group(sprites["players_dict"].values())
    sprites["background"] = pygame.sprite.Group(sprites["ground"], sprites["win_platform"], sprites["cup"])
    sprites["bricks"] = pygame.sprite.Group()
    sprites["bullets"] = pygame.sprite.Group()
    
#TODO: display end game message till user presses key then restart game
while True:
    initial_set_up()
    pygame.time.set_timer(USEREVENT, BRICK_FREQ)
    end_message = None
    loop = True
    while loop:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == USEREVENT:
                add_bricks()

        displaysurface.fill((0,102,204))
        pressed_keys = pygame.key.get_pressed()
        if end_message:
            if pressed_keys[K_RETURN]:
                loop = False
        else:
            for i, player in sprites["players_dict"].items():
                keyboard_input = {command for key, command in KEYS[i].items() if pressed_keys[key]}
                player.move(keyboard_input)
            for brick in sprites["bricks"]:
                brick.move()
            for bullet in sprites["bullets"]:
                bullet.move()
            winners = pygame.sprite.spritecollide(sprites["cup"], sprites["players_group"], False)
            if len(winners) == 1:
                if winners[0] == sprites["players_dict"][1]:
                    end_message = "PLAYER 1 WINS!"
                elif winners[0] == sprites["players_dict"][2]:
                    end_message = "PLAYER 1 WINS!"
            elif len(winners) == 2:
                end_message = "DRAW!" 

        # Draw everything
        for entity in sprites["bricks"]:
            displaysurface.blit(entity.surf, entity.rect)
        for entity in sprites["background"]:
            displaysurface.blit(entity.surf, entity.rect)
        for entity in sprites["players_group"]:
            displaysurface.blit(entity.surf, entity.rect)
        for entity in sprites["bullets"]:
            displaysurface.blit(entity.surf, entity.rect)
        if end_message is not None:
            text_surf, text_rect = END_GAME_FONT.render(end_message)
            text_rect.center = (WIDTH / 2, HEIGHT / 2)
            displaysurface.blit(text_surf, text_rect)
        pygame.display.update()
        FramePerSec.tick(FPS)
    pygame.time.set_timer(USEREVENT, 0)   # remove timer

    