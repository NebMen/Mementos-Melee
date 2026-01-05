import pygame
import sys
import json
import random

# === CONSTANTS & CONFIG ===
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
SKY_BLUE = (135, 206, 235)
YELLOW = (255, 215, 0)
GRAY = (50, 50, 50)

# Ground
GROUND_Y = SCREEN_HEIGHT - 80

# Initialize
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mementos Melee - Alpha 0.3")
clock = pygame.time.Clock()

# FONTS
font_header = pygame.font.SysFont('impact', 60)
font_sub = pygame.font.SysFont('arial', 30)
font_ui = pygame.font.SysFont('arial', 20, bold=True)

# === THE FIGHTER CLASS ===
class Fighter(pygame.sprite.Sprite):
    def __init__(self, x, y, flip=False, player=1):
        super().__init__()
        self.player = player
        self.health = 100
        self.max_health = 100
        self.display_health = self.max_health
        self.hit_flash = 0
        self.speed = 5
        self.jump_power = -15
        self.gravity = 0.8
        self.vel_y = 0
        self.is_jumping = False
        self.attacking = False
        self.attack_cooldown = 0
        self.flip = flip
        
        # New Feature: Comeback Mechanic Flag
        self.has_triggered_crisis = False 

        # Create the visual rect
        self.image = pygame.Surface((60, 100))
        color = (200, 50, 50) if player == 1 else (50, 50, 200)
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    # NOW ACCEPTS is_ai PARAMETER
    def update(self, keys, opponent, is_ai=False):
        dx = 0
        dy = 0

        # Cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            self.attacking = False

        # === INPUT HANDLING (MANUAL vs AI) ===
        move_left = False
        move_right = False
        do_jump = False
        do_attack = False

        if not is_ai:
            # MANUAL CONTROLS
            if self.player == 1:
                if keys[pygame.K_a]: move_left = True
                if keys[pygame.K_d]: move_right = True
                if keys[pygame.K_w]: do_jump = True
                if keys[pygame.K_g]: do_attack = True
            else:
                if keys[pygame.K_LEFT]: move_left = True
                if keys[pygame.K_RIGHT]: move_right = True
                if keys[pygame.K_UP]: do_jump = True
                if keys[pygame.K_k]: do_attack = True
        else:
            # === SIMPLE AI LOGIC (Placeholder) ===
            # Chase the opponent
            if self.rect.x > opponent.rect.x + 60:
                move_left = True
            elif self.rect.x < opponent.rect.x - 60:
                move_right = True
            
            # Jump randomizer or if opponent is high
            if opponent.rect.y < self.rect.y - 50 and random.randint(0, 100) < 2:
                do_jump = True
            
            # Attack if close
            dist = abs(self.rect.centerx - opponent.rect.centerx)
            if dist < 80 and random.randint(0, 100) < 5:
                do_attack = True

        # === APPLY INPUTS ===
        if move_left:
            dx -= self.speed
            self.flip = True
        if move_right:
            dx += self.speed
            self.flip = False
        
        if do_jump and not self.is_jumping:
            self.vel_y = self.jump_power
            self.is_jumping = True
            
        if do_attack and self.attack_cooldown == 0:
            self.attack()

        # Physics & Gravity
        self.vel_y += self.gravity
        dy += self.vel_y

        # Ground Collision
        if self.rect.y + dy >= GROUND_Y - self.rect.height:
            self.rect.y = GROUND_Y - self.rect.height
            self.vel_y = 0
            self.is_jumping = False
            dy = 0 

        self.rect.x += dx
        self.rect.y += dy

        # Screen Clamp
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH

        # Hitbox Logic
        if self.attacking and 15 <= self.attack_cooldown <= 20:
            attack_rect = pygame.Rect(self.rect.centerx, self.rect.y + 30, 80, 60)
            if self.flip: attack_rect.x -= 80
            
            pygame.draw.rect(screen, YELLOW, attack_rect) # Debug visual

            if attack_rect.colliderect(opponent.rect):
                opponent.health -= 10
                opponent.hit_flash = 15

        # Visuals
        self.display_health += (self.health - self.display_health) * 0.12
        if self.hit_flash > 0: self.hit_flash -= 1

    def attack(self):
        self.attacking = True
        self.attack_cooldown = 20

    def draw(self, surface):
        if self.hit_flash > 0:
            pygame.draw.rect(surface, RED, self.rect)
        else:
            color = (200, 50, 50) if self.player == 1 else (50, 50, 200)
            pygame.draw.rect(surface, color, self.rect)
            
        bar_x = self.rect.x
        bar_y = self.rect.y - 20
        pygame.draw.rect(surface, RED, (bar_x, bar_y, 60, 10))
        ratio = max(0, self.display_health / self.max_health)
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, 60 * ratio, 10))
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, 60, 10), 1)

# === THE GAME MANAGER ===
class Game:
    def __init__(self):
        self.state = "MENU" # START IN MENU
        self.game_mode = "PVP" # PVP or PVE
        
        self.p1 = Fighter(200, GROUND_Y - 100, player=1)
        self.p2 = Fighter(700, GROUND_Y - 100, flip=True, player=2)
        
        # Menu Variables
        self.menu_options = ["1 PLAYER (VS AI)", "2 PLAYER (PVP)", "EXIT"]
        self.menu_index = 0
        
        # Trivia Setup
        self.active_player = None
        self.user_input = ""
        self.trivia_q = ""
        self.trivia_a = ""
        
        try:
            with open('questions.json', 'r') as f:
                self.question_db = json.load(f)
        except FileNotFoundError:
            self.question_db = [{"q": "File missing. Type OK.", "a": "OK"}]

    def update(self):
        # === MENU LOGIC ===
        if self.state == "MENU":
            # Handled in handle_input to prevent scrolling too fast
            pass
            
        # === FIGHT LOGIC ===
        elif self.state == "FIGHT":
            keys = pygame.key.get_pressed()
            
            # P1 is always manual
            self.p1.update(keys, self.p2, is_ai=False)
            
            # P2 is AI if mode is PVE, otherwise Manual
            is_ai_mode = (self.game_mode == "PVE")
            self.p2.update(keys, self.p1, is_ai=is_ai_mode)
            
            # Check for Trivia
            if self.p1.health <= 20 and not self.p1.has_triggered_crisis:
                self.trigger_crisis(self.p1)
            elif self.p2.health <= 20 and not self.p2.has_triggered_crisis:
                self.trigger_crisis(self.p2)

            if self.p1.health <= 0 or self.p2.health <= 0:
                self.state = "GAME_OVER"

        elif self.state == "TRIVIA":
            pass

    def trigger_crisis(self, player):
        self.state = "TRIVIA"
        self.active_player = player
        self.active_player.has_triggered_crisis = True
        data = random.choice(self.question_db)
        self.trivia_q = data['q']
        self.trivia_a = data['a'].upper()
        self.user_input = ""

    def handle_input(self, event):
        # === GLOBAL INPUTS (Works in any state) ===
        if event.type == pygame.KEYDOWN:
            # Fullscreen Toggle (Alt + Enter)
            if event.key == pygame.K_RETURN and (pygame.key.get_mods() & pygame.KMOD_ALT):
                pygame.display.toggle_fullscreen()

        # === MENU INPUTS ===
        if self.state == "MENU":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w or event.key == pygame.K_UP:
                    self.menu_index = (self.menu_index - 1) % len(self.menu_options)
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    self.menu_index = (self.menu_index + 1) % len(self.menu_options)
                elif event.key == pygame.K_RETURN:
                    if not (pygame.key.get_mods() & pygame.KMOD_ALT):
                       # Ignores Enter if Alt is held (prevent triggering selection when toggling fullscreen)
                        if self.menu_index == 0: # 1 Player
                            self.game_mode = "PVE"
                            self.reset_match()
                            self.state = "FIGHT"
                        elif self.menu_index == 1: # 2 Player
                            self.game_mode = "PVP"
                            self.reset_match()
                            self.state = "FIGHT"
                        elif self.menu_index == 2: # Exit
                            pygame.quit(); sys.exit()

        # === GAME INPUTS ===
        elif self.state == "FIGHT":
            if event.type == pygame.KEYDOWN:
                # Tab OR Escape triggers Pause
                if event.key == pygame.K_TAB or event.key == pygame.K_ESCAPE:
                    self.state = "PAUSE"
                    
        elif self.state == "PAUSE":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB or event.key == pygame.K_ESCAPE: 
                    self.state = "FIGHT" # Resume
                elif event.key == pygame.K_m: 
                    self.state = "MENU" # Go to Main Menu
                    self.reset_match()  # Reset game so it's fresh next time
                elif event.key == pygame.K_q: 
                    pygame.quit(); sys.exit() # Quit to Desktop

        elif self.state == "TRIVIA":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.check_answer()
                elif event.key == pygame.K_BACKSPACE:
                    self.user_input = self.user_input[:-1]
                else:
                    self.user_input += event.unicode
        
        elif self.state == "GAME_OVER":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset_match()
                self.state = "FIGHT"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = "MENU"

    def reset_match(self):
        # Helper to restart fight without reloading app
        self.p1 = Fighter(200, GROUND_Y - 100, player=1)
        self.p2 = Fighter(700, GROUND_Y - 100, flip=True, player=2)

    def check_answer(self):
        if self.user_input.upper() == self.trivia_a:
            self.active_player.health += 50
            if self.active_player.health > 100: self.active_player.health = 100
        else:
            self.active_player.health -= 20
        self.state = "FIGHT"

    def draw(self):
        screen.fill(SKY_BLUE)
        
        # === DRAW MENU ===
        if self.state == "MENU":
            screen.fill(BLACK) # Persona 5 Style Red/Black later
            title = font_header.render("MEMENTOS MELEE", True, RED)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
            
            for i, option in enumerate(self.menu_options):
                color = RED if i == self.menu_index else WHITE
                txt = font_sub.render(option, True, color)
                screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 250 + i * 50))
                
                # Draw Arrow for selection
                if i == self.menu_index:
                    pygame.draw.polygon(screen, RED, [(380, 260 + i*50), (380, 280 + i*50), (400, 270 + i*50)])

        # === DRAW GAME ===
        else:
            # Draw Background
            pygame.draw.rect(screen, (100, 200, 100), (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
            
            self.p1.draw(screen)
            self.p2.draw(screen)
            
            # === CONTROLS OVERLAY (TOP LEFT) ===
            # Semi-transparent box
            s = pygame.Surface((250, 100))
            s.set_alpha(150)
            s.fill(BLACK)
            screen.blit(s, (10, 10))
            
            c1 = font_ui.render("P1: WASD + G (Atk)", True, WHITE)
            c2 = font_ui.render("P2: Arrows + K (Atk)", True, WHITE)
            mode_txt = font_ui.render(f"MODE: {self.game_mode}", True, YELLOW)
            
            screen.blit(c1, (20, 20))
            screen.blit(c2, (20, 45))
            screen.blit(mode_txt, (20, 70))

            # === PAUSE SCREEN (UPDATED) ===
            if self.state == "PAUSE":
                # Darken background
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.set_alpha(200) # Darker than before
                overlay.fill(BLACK)
                screen.blit(overlay, (0,0))
                
                # Menu Box
                box_rect = pygame.Rect(300, 120, 400, 260)
                pygame.draw.rect(screen, WHITE, box_rect)
                pygame.draw.rect(screen, BLUE, box_rect, 5)
                
                # Text Options
                title = font_header.render("PAUSED", True, BLACK)
                opt1 = font_sub.render("TAB/ESC: Resume", True, BLUE)
                opt2 = font_sub.render("M: Main Menu", True, BLACK)
                opt3 = font_sub.render("Q: Quit Desktop", True, RED)
                
                screen.blit(title, (410, 130))
                screen.blit(opt1, (350, 200))
                screen.blit(opt2, (350, 250))
                screen.blit(opt3, (350, 300))

            if self.state == "TRIVIA":
                # Same Trivia code as before
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                overlay.set_alpha(150)
                overlay.fill(BLACK)
                screen.blit(overlay, (0,0))
                box_rect = pygame.Rect(200, 100, 600, 300)
                pygame.draw.rect(screen, WHITE, box_rect)
                pygame.draw.rect(screen, RED, box_rect, 5)
                header = font_header.render("COGNITIVE CRISIS!", True, RED)
                q_text = font_sub.render(self.trivia_q, True, BLACK)
                ans_text = font_sub.render(f"Answer: {self.user_input}", True, BLUE)
                screen.blit(header, (box_rect.x + 20, box_rect.y + 20))
                screen.blit(q_text, (box_rect.x + 20, box_rect.y + 100))
                screen.blit(ans_text, (box_rect.x + 20, box_rect.y + 200))

            if self.state == "GAME_OVER":
                txt = font_header.render("GAME OVER", True, RED)
                sub = font_sub.render("Press R to Retry, ESC for Menu", True, BLACK)
                screen.blit(txt, (350, 150))
                screen.blit(sub, (300, 250))

        pygame.display.flip()

# === RUN ===
game = Game()
running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        game.handle_input(event)
    
    game.update()
    game.draw()

pygame.quit()
sys.exit()