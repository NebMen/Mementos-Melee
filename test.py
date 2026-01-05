# GROK: A 2D fighting game set in the Mementos level from Persona 5.
# Changed to Gemini because the game logic was mixed in with the art assets.
# AT THE MOMENT ASSETS ARE SIMULATED WITH SIMPLE SHAPES AND COLORS.

import pygame
import sys
import os
import random

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (138, 43, 226)
SKY_BLUE = (135, 206, 235)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mementos Melee")
clock = pygame.time.Clock()

# Load assets
def load_image(folder, name, scale=None):
    path = os.path.join("assets", folder, name)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if scale:
            img = pygame.transform.scale(img, scale)
        return img
    return None

background = load_image("backgrounds", "mementos.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
if not background:
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background.fill((20, 0, 40))

# Sounds
def load_sound(name):
    path = os.path.join("assets", "sounds", name)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None

punch_sound = load_sound("punch.wav")
hit_sound = load_sound("hit.wav")
jump_sound = load_sound("jump.wav")
select_sound = load_sound("select.wav") or None

# Fonts
font_big = pygame.font.SysFont("comicsans", 80, bold=True)
font_medium = pygame.font.SysFont("comicsans", 50)
font_small = pygame.font.SysFont("comicsans", 30)

ground_y = SCREEN_HEIGHT - 80

# Game States
class GameState:
    MENU = 0
    CHAR_SELECT = 1
    FIGHT = 2
    ROUND_END = 3

current_state = GameState.MENU
round_wins = [0, 0]
current_round = 1

# Damage Text
class DamageText(pygame.sprite.Sprite):
    def __init__(self, x, y, damage):
        super().__init__()
        self.image = font_medium.render(f"-{damage}", True, YELLOW)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_y = -3
        self.life = 40

    def update(self):
        self.rect.y += self.vel_y
        self.life -= 1
        if self.life <= 0:
            self.kill()

damage_texts = pygame.sprite.Group()

# Fighter Class (updated)
class Fighter(pygame.sprite.Sprite):
    def __init__(self, x, y, character_data, player):
        super().__init__()
        self.player = player
        self.char = character_data
        self.health = 100
        self.max_health = 100
        self.speed = 5
        self.jump_power = -15
        self.vel_y = 0
        self.is_jumping = False
        self.attacking = False
        self.attack_type = 0  # 0 = punch, 1 = kick
        self.attack_cooldown = 0
        self.flip = player == 2
        self.stun = 0

        # Load animations
        self.animations = {}
        folder = f"assets/sprites/{self.char['folder']}"
        for anim in ["idle", "walk", "punch", "kick"]:
            self.animations[anim] = []
            for i in range(1, 4 if anim == "walk" else 2):
                img = load_image(f"sprites/{self.char['folder']}", f"{anim}{i}.png", (80, 120))
                if img:
                    self.animations[anim].append(img)
            if not self.animations[anim]:
                surf = pygame.Surface((80, 120), pygame.SRCALPHA)
                pygame.draw.rect(surf, self.char['color'], (20, 0, 40, 60))
                self.animations[anim] = [surf]

        self.current_anim = "idle"
        self.frame = 0
        self.anim_timer = 0
        self.image = self.animations["idle"][0]
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, ground_y)

    def update(self, keys, opponent):
        if self.stun > 0:
            self.stun -= 1
            return

        dx = 0
        dy = self.vel_y

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # Input
        if self.player == 1:
            if keys[pygame.K_a]: dx -= self.speed; self.flip = True
            if keys[pygame.K_d]: dx += self.speed; self.flip = False
            if keys[pygame.K_w] and not self.is_jumping:
                self.vel_y = self.jump_power
                self.is_jumping = True
                if jump_sound: jump_sound.play()
            if keys[pygame.K_g] and self.attack_cooldown == 0:
                self.attack(0)  # punch
            if keys[pygame.K_h] and self.attack_cooldown == 0:
                self.attack(1)  # kick
        else:
            if keys[pygame.K_LEFT]: dx -= self.speed; self.flip = True
            if keys[pygame.K_RIGHT]: dx += self.speed; self.flip = False
            if keys[pygame.K_UP] and not self.is_jumping:
                self.vel_y = self.jump_power
                self.is_jumping = True
                if jump_sound: jump_sound.play()
            if keys[pygame.K_k] and self.attack_cooldown == 0:
                self.attack(0)
            if keys[pygame.K_j] and self.attack_cooldown == 0:
                self.attack(1)

        # Gravity
        self.vel_y += 0.8
        if self.rect.bottom + dy >= ground_y:
            dy = ground_y - self.rect.bottom
            self.is_jumping = False
            self.vel_y = 0

        self.rect.x += dx
        self.rect.y += dy

        # Screen bounds
        self.rect.x = max(0, min(SCREEN_WIDTH - self.rect.width, self.rect.x))

        # Animation
        if self.attacking:
            anim = "kick" if self.attack_type else "punch"
        elif dx != 0:
            anim = "walk"
        else:
            anim = "idle"

        self.anim_timer += 1
        if self.anim_timer >= 8:
            self.anim_timer = 0
            self.frame = (self.frame + 1) % len(self.animations[anim])
        self.image = self.animations[anim][self.frame]
        if self.flip:
            self.image = pygame.transform.flip(self.image, True, False)

        # Attack hit
        if self.attack_cooldown == 10:  # peak frame
            damage = 15 if self.attack_type else 10
            range_bonus = 50 if self.attack_type else 0
            attack_rect = pygame.Rect(
                self.rect.left - range_bonus if self.flip else self.rect.right,
                self.rect.y + 20, 80 + range_bonus, 80)
            if attack_rect.colliderect(opponent.rect):
                opponent.health -= damage
                damage_texts.add(DamageText(opponent.rect.centerx, opponent.rect.top, damage))
                if hit_sound: hit_sound.play()

    def attack(self, type):
        self.attacking = True
        self.attack_type = type
        self.attack_cooldown = 25
        self.frame = 0
        if punch_sound: punch_sound.play()

    def draw_health(self, surface):
        x = 50 if self.player == 1 else SCREEN_WIDTH - 250
        pygame.draw.rect(surface, RED, (x, 20, 200, 30))
        pygame.draw.rect(surface, GREEN, (x, 20, 200 * (self.health / 100), 30))
        name = font_small.render(self.char["name"], True, WHITE)
        surface.blit(name, (x, 0))

# Characters
characters = [
    {"name": "The Procrastinator", "folder": "player1", "color": (200, 50, 50),
     "bio": "Master of 'I'll do it tomorrow'. Hits hard when he finally moves."},
    {"name": "Caffeine Demon", "folder": "player2", "color": (50, 50, 200),
     "bio": "Runs on 12 espressos. Fast but crashes hard."}
]

selected = [0, 0]
player1 = None
player2 = None

# Main Loop
running = True
while running:
    clock.tick(FPS)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.blit(background, (0, 0))
    pygame.draw.rect(screen, (50, 50, 50, 180), (0, ground_y, SCREEN_WIDTH, SCREEN_HEIGHT - ground_y + 50))

    if current_state == GameState.MENU:
        title = font_big.render("MEMENTOS MELEE", True, PURPLE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        start_text = font_medium.render("Press SPACE to Start", True, WHITE)
        screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, 250))

        if keys[pygame.K_SPACE]:
            current_state = GameState.CHAR_SELECT
            if select_sound: select_sound.play()

    elif current_state == GameState.CHAR_SELECT:
        screen.blit(font_big.render("Choose Your Thief", True, YELLOW), (150, 50))
        for i, char in enumerate(characters):
            color = YELLOW if selected[0] == i else WHITE
            name = font_medium.render(char["name"], True, color)
            screen.blit(name, (100, 150 + i*100))
            bio = font_small.render(char["bio"], True, WHITE)
            screen.blit(bio, (100, 190 + i*100))

        color = YELLOW if selected[1] == i else WHITE
        name2 = font_medium.render(characters[selected[1]]["name"], True, color)
        screen.blit(name2, (600, 200))

        if keys[pygame.K_w] or keys[pygame.K_s]:
            if pygame.key.get_pressed()[pygame.K_w]:
                selected[0] = (selected[0] - 1) % len(characters)
            if pygame.key.get_pressed()[pygame.K_s]:
                selected[0] = (selected[0] + 1) % len(characters)
            if keys[pygame.K_SPACE]:
                player1 = Fighter(200, 0, characters[selected[0]], 1)
                player2 = Fighter(700, 0, characters[selected[1]], 2)
                all_sprites = pygame.sprite.Group(player1, player2)
                current_state = GameState.FIGHT

    elif current_state == GameState.FIGHT:
        player1.update(keys, player2)
        player2.update(keys, player1)
        damage_texts.update()

        all_sprites.draw(screen)
        player1.draw_health(screen)
        player2.draw_health(screen)
        damage_texts.draw(screen)

        round_text = font_medium.render(f"Round {current_round}", True, WHITE)
        screen.blit(round_text, (SCREEN_WIDTH//2 - round_text.get_width()//2, 10))

        if player1.health <= 0 or player2.health <= 0:
            winner = 2 if player1.health <= 0 else 1
            round_wins[winner-1] += 1
            current_state = GameState.ROUND_END

    elif current_state == GameState.ROUND_END:
        win_text = font_big.render(f"{characters[selected[winner-1]]['name']} WINS ROUND!", True, RED)
        screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, 200))
        if round_wins[0] == 2 or round_wins[1] == 2:
            final = font_big.render("GAME OVER - " + ("P1" if round_wins[0] == 2 else "P2") + " WINS!", True, YELLOW)
            screen.blit(final, (SCREEN_WIDTH//2 - final.get_width()//2, 300))
        else:
            current_round += 1
            pygame.time.wait(2000)
            player1.health = player1.max_health
            player2.health = player2.max_health
            player1.rect.bottomleft = (200, ground_y)
            player2.rect.bottomleft = (700, ground_y)
            current_state = GameState.FIGHT

    pygame.display.flip()

pygame.quit()
sys.exit()
