""" 
Skyscraper Destruction Race
Race to the cup up a growing skyscraper while destroying your opponent's.

"""
# TODO make it easier to climb slope and get on top of same brick - currently tends to fall off
# TODO too easy to slip down when bricks move up - adjust mechanics
# TODO ensure bricks remain aligned - 1px gap can allow player to slip off. Currently they seem to rise a little too far then
# sink back.
# TODO hitting bricks causes more damage to the surrounding bricks
# TODO animation of bricks getting hot then disintegrating

import pygame
from pygame.locals import *
import random
import math
import sys
pygame.init()
vec = pygame.math.Vector2  # 2 for two dimensional


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

COLOURS = {
    "brick": (100, 100, 100),
    "brick_line": (0, 0, 100),
    "platform": (204, 102, 0),
    "tower_marker": (0, 80, 0),
    "player": (30, 30, 30),
    "bullet": (0, 0, 0)
}

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

class TowerMarker(pygame.sprite.Sprite):
    """ Stationery sprite that marks when a tower is about to grow and hides when it isn't """
    def __init__(self, tower, position):
        super().__init__()
        self.surf = pygame.Surface((BRICK_WIDTH, BRICK_HEIGHT))
        self.surf.set_colorkey((255, 255, 255))
        self.left = position_to_x(tower, position)
        self.top = sprites["ground"].rect.top
        self.rect = self.surf.get_rect(topleft=(self.left, self.top))
        self.draw()
    
    def draw(self):
        self.surf.fill((255, 255, 255))
        #pygame.draw.circle(self.surf, (0,0,0), (self.rect.width / 2, self.rect.height / 2), 10, width=0)
        pygame.draw.polygon(self.surf, COLOURS["tower_marker"], [
            (self.rect.width / 2, 0),
            (self.rect.width, self.rect.height / 2),
            (0, self.rect.height / 2)
        ], width=0)
         

class Brick(pygame.sprite.Sprite):
    """ Bricks appear in the floor and move up one space, pushing up everything above them """
    def __init__(self, tower, position, stairs):
        super().__init__()
        self.surf = pygame.Surface((BRICK_WIDTH, BRICK_HEIGHT))
        self.tower = tower
        self.column = sprites["bricks_by_position"][tower][position]
        self.below = sprites["ground"]
        if self.column:
            self.column[-1].below = self
        self.rect = self.surf.get_rect(topleft=(position_to_x(tower, position), sprites["ground"].rect.top))
        self.stairs = stairs
        self.speed = 0
        self.surf.fill(COLOURS["brick"])
        pygame.draw.line(self.surf, COLOURS["brick_line"], (0, 0), (BRICK_WIDTH, 0), width=1)
        if stairs:
            if tower == RIGHT:
                pygame.draw.line(self.surf, COLOURS["brick_line"], (0, 0), (BRICK_WIDTH, BRICK_HEIGHT))
            else:
                pygame.draw.line(self.surf, COLOURS["brick_line"], (0, BRICK_HEIGHT), (BRICK_WIDTH, 0))

    @classmethod
    def choose_columns(cls):
        """ Choose the columns that will grow """      
        cls.chosen_columns = {tower: [i for i in range(TOWER_WIDTH) if random.random() < BRICK_CHANCE] for tower in [LEFT, RIGHT]}

    @classmethod    
    def add(cls):
        """ Add bricks in the positions chosen earlier """
        for tower, positions in cls.chosen_columns.items():
            for position in positions:
                if random.random() < .2:
                    brick = cls(tower, position, True)
                else:
                    brick = cls(tower, position, False)
                sprites["bricks"].add(brick)
                sprites["bricks_by_position"][tower][position].append(brick)

    def move(self):
        goal = self.below.rect.top
        if goal > self.rect.bottom:  # nothing directly under us, so fall
            self.rect.bottom = min(goal, self.rect.bottom + self.speed + .5 * GRAVITY)
            self.speed += GRAVITY
        elif goal < self.rect.bottom: # overlapping so shift up
            self.speed = 0
            self.rect.bottom = max(goal, self.rect.bottom - BRICK_SPEED)
        else:
            self.speed = 0              
        
    def kill(self):
        # TODO: add animation stage

        # We need to update the 'below' property of the brick that is above self
        for brick in self.column:
            if brick.below == self:
                brick.below = self.below
        self.column.remove(self)
        super().kill()

    def explode(self): #TODO: kill self and surrounding bricks
        pass

    def __repr__(self):
        return f"Brick {x_to_position(self.rect.midbottom)} midbottom={self.rect.midbottom} stairs={self.stairs}"

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
        pygame.draw.circle(self.surf, COLOURS["player"], self.centre, PLAYER_SIZE * .3, width=0)
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
        brick.kill()
        self.kill()  
        
    def hit_brick_later(self, brick):
        if self.hit is None:  # go straight through the first brick you hit
            self.hit = brick
            brick.kill()
        else:   # then make the next one explode taking the surrounding bricks with it
            brick.explode()
        self.kill() 

    def update(self):
        self.surf.fill((255, 255, 255))
        pygame.draw.circle(self.surf, COLOURS["bullet"], (BULLET_SIZE / 2, BULLET_SIZE / 2), BULLET_SIZE, width=0)


class Platform(pygame.sprite.Sprite):
    def __init__(self, pos, width):
        super().__init__()
        self.surf = pygame.Surface((width, BRICK_HEIGHT))
        self.surf.fill(COLOURS["platform"])
        self.rect = self.surf.get_rect(topleft=pos)

class Cup(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.surf = pygame.image.load("cup.png")
        self.surf.set_colorkey((255,255,255))
        self.rect = self.surf.get_rect(midbottom=pos)




def initial_set_up():
    sprites["bricks_by_position"] = {
        LEFT: [[] for _ in range(TOWER_WIDTH)],
        RIGHT: [[] for _ in range(TOWER_WIDTH)]
        }
    sprites["ground"] = Platform(pos=(0, HEIGHT - BRICK_HEIGHT), width=WIDTH)
    sprites["tower_marker"] = {tower: [TowerMarker(tower, position) for position in range(TOWER_WIDTH)] for tower in [LEFT, RIGHT]}
    sprites["win_platform"] = Platform(pos=(BRICK_WIDTH + TOWER_WIDTH * BRICK_WIDTH,
                             HEIGHT - (BRICK_HEIGHT - 1) * (1 + WIN_PLATFORM_HEIGHT) + 2),
                        width=WIDTH-2*BRICK_HEIGHT-2*TOWER_WIDTH*BRICK_HEIGHT) 
    sprites["cup"] = Cup(pos=(sprites["win_platform"].rect.centerx, sprites["win_platform"].rect.top))
    sprites["players_dict"] = {1: Player(LEFT), 2: Player(RIGHT)}
    sprites["players_group"] = pygame.sprite.Group(sprites["players_dict"].values())
    sprites["background"] = pygame.sprite.Group(sprites["ground"], sprites["win_platform"], sprites["cup"])
    sprites["bricks"] = pygame.sprite.Group()
    sprites["bullets"] = pygame.sprite.Group()
 
while True:
    initial_set_up()
    Brick.choose_columns()
    pygame.time.set_timer(USEREVENT, BRICK_FREQ)
    end_message = None
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == USEREVENT:
                Brick.add()
                Brick.choose_columns()

        displaysurface.fill((0,102,204))
        pressed_keys = pygame.key.get_pressed()
        if end_message:
            if pressed_keys[K_RETURN]:
                break
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
        for group in ["bricks", "background", "players_group", "bullets"]:
            for entity in sprites[group]:
                displaysurface.blit(entity.surf, entity.rect)

        for tower, columns in Brick.chosen_columns.items():
            for column in columns:
                marker = sprites["tower_marker"][tower][column]
                displaysurface.blit(marker.surf, marker.rect)

        if end_message is not None:
            text_surf, text_rect = END_GAME_FONT.render(end_message)
            text_rect.center = (WIDTH / 2, HEIGHT / 2)
            displaysurface.blit(text_surf, text_rect)
        pygame.display.update()
        FramePerSec.tick(FPS)
    pygame.time.set_timer(USEREVENT, 0)   # remove timer

    