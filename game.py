import pygame
import random
import os
import cv2
import mediapipe as mp
import math
import numpy as np
import sys

def calculate_angle(a, b, c):
    """Calculates the angle between three points."""
    ang = math.degrees(math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0]))
    ang = abs(ang)
    if ang > 180:
        ang = 360 - ang
    return ang

# --- MENU SCREEN FUNCTIONS ---
def show_start_screen(screen, bg_image, w, h):
    font_large = pygame.font.SysFont("impact", 80)
    font_small = pygame.font.SysFont("arial", 36)
    
    waiting = True
    while waiting:
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill((50, 50, 50))
            
        overlay = pygame.Surface((w, h))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        title = font_large.render("KINETIC KOMBAT", True, (220, 20, 60))
        prompt = font_small.render("Press SPACE to start or ESC to quit", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(w//2, h//3)))
        screen.blit(prompt, prompt.get_rect(center=(w//2, h//2 + 50)))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return 
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

def show_game_over_screen(screen, bg_image, w, h, winner_msg):
    font_large = pygame.font.SysFont("impact", 80)
    font_small = pygame.font.SysFont("arial", 36)
    
    waiting = True
    while waiting:
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill((50, 50, 50))
            
        overlay = pygame.Surface((w, h))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        title = font_large.render(winner_msg, True, (255, 215, 0))
        prompt = font_small.render("Press SPACE to replay or ESC to quit", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(w//2, h//3)))
        screen.blit(prompt, prompt.get_rect(center=(w//2, h//2 + 50)))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True 
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

# --- 1. INITIALIZE PYGAME & AUDIO ---
pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Kinetic Kombat - AI Motion Control")
clock = pygame.time.Clock()

WHITE, BLACK, RED, BLUE, GREEN, CYAN, GRAY = (
    (255, 255, 255), (0, 0, 0), (255, 0, 0), (0, 0, 255), 
    (0, 255, 0), (0, 255, 255), (200, 200, 200)
)

# --- 2. LOAD ASSETS ---
base_dir = os.path.dirname(os.path.abspath(__file__))

# Background Image
bg_path = os.path.join(base_dir, "assets", "bg.jpg")
background = None
if os.path.exists(bg_path):
    background = pygame.transform.scale(pygame.image.load(bg_path).convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))

# Audio Files
try:
    sfx_attack = pygame.mixer.Sound(os.path.join(base_dir, "assets", "sfx", "attack.wav"))
    sfx_win = pygame.mixer.Sound(os.path.join(base_dir, "assets", "sfx", "win.wav"))
    sfx_lose = pygame.mixer.Sound(os.path.join(base_dir, "assets", "sfx", "lose.wav"))
    sfx_attack.set_volume(0.8)
    sfx_win.set_volume(1.0)
    sfx_lose.set_volume(1.0)
except Exception as e:
    print(f"Audio warning: {e}. Game will run silently.")
    sfx_attack = sfx_win = sfx_lose = None

# --- 3. INITIALIZE WEBCAM & AI ---
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
cap = cv2.VideoCapture(0)
# Model Complexity set to 0 for maximum speed!
pose = mp_pose.Pose(model_complexity=0, min_detection_confidence=0.5, min_tracking_confidence=0.5)

# --- FIGHTER CLASS ---
class Fighter:
    def __init__(self, x, y, color, player_num, is_cpu=False):
        self.rect = pygame.Rect(x, y, 50, 100)
        self.start_x, self.start_y = x, y
        self.speed = 9  # Faster movement!
        self.base_color = color
        self.player_num = player_num
        self.is_cpu = is_cpu
        
        self.health = 100
        self.attacking = False
        self.attack_type = ""
        self.blocking = False
        self.attack_cooldown = 0
        self.facing_left = True if player_num == 2 else False
        
        self.ai_timer = 0
        self.ai_action = "idle"

        self.sprites = {"idle": None, "punch": None, "kick": None, "block": None}
        p_folder = f"player{self.player_num}"
        
        for action in ["idle", "punch", "kick", "block"]:
            img_path = os.path.join(base_dir, "assets", "sprites", p_folder, action, "0.png")
            if os.path.exists(img_path):
                img = pygame.image.load(img_path).convert_alpha()
                img = pygame.transform.scale(img, (120, 150))
                if self.player_num == 2:
                    img = pygame.transform.flip(img, True, False)
                self.sprites[action] = img

    def move(self, target, vision_action=None):
        dx = 0
        self.blocking = False
        key = pygame.key.get_pressed()

        if not self.attacking:
            if not self.is_cpu:
                # Keyboard Backup or Webcam inputs
                if key[pygame.K_a]: dx, self.facing_left = -self.speed, True
                if key[pygame.K_d]: dx, self.facing_left = self.speed, False
                
                if vision_action == "block" or key[pygame.K_l]:
                    self.blocking = True
                elif vision_action == "punch" or key[pygame.K_j]:
                    self.attack(target, "punch")
                elif vision_action == "kick" or key[pygame.K_k]:
                    self.attack(target, "kick")
            else:
                # CPU Logic
                dist = target.rect.centerx - self.rect.centerx
                self.facing_left = dist < 0
                if self.ai_timer <= 0:
                    self.ai_timer = random.randint(15, 45) # Faster AI decisions
                    self.ai_action = "move" if abs(dist) > 70 else random.choice(["punch", "kick", "block", "idle"])
                self.ai_timer -= 1
                
                if self.ai_action == "move": dx = self.speed if dist > 0 else -self.speed
                elif self.ai_action == "block": self.blocking = True
                elif self.ai_action in ["punch", "kick"]:
                    self.attack(target, self.ai_action)
                    self.ai_action = "idle"

        # Bounds & Collisions
        if self.rect.left + dx < 0: dx = -self.rect.left
        if self.rect.right + dx > SCREEN_WIDTH: dx = SCREEN_WIDTH - self.rect.right
        if self.rect.move(dx, 0).colliderect(target.rect):
            dx = target.rect.left - self.rect.right if dx > 0 else target.rect.right - self.rect.left
        
        self.rect.x += dx
        
        # Cooldown management
        if self.attack_cooldown > 0: 
            self.attack_cooldown -= 1
        else: 
            self.attacking, self.attack_type = False, ""

    def attack(self, target, attack_type):
        if self.attack_cooldown == 0:
            # 15 Frame cooldown allows for faster combo attacks!
            self.attacking, self.attack_type, self.attack_cooldown = True, attack_type, 15
            hw, hh = (40, 20) if attack_type == "punch" else (60, 30)
            hx = self.rect.centerx - hw - 25 if self.facing_left else self.rect.centerx + 25
            hitbox = pygame.Rect(hx, self.rect.y + 20, hw, hh)
            
            if hitbox.colliderect(target.rect):
                if sfx_attack:
                    sfx_attack.play()
                
                dmg = int((5 if attack_type == "punch" else 8) * (0.2 if target.blocking else 1))
                target.health = max(0, target.health - dmg)

    def draw(self):
        curr = None
        if self.blocking: curr = self.sprites.get("block")
        elif self.attacking: curr = self.sprites.get(self.attack_type)
        else: curr = self.sprites.get("idle")

        if curr:
            img = pygame.transform.flip(curr, self.facing_left, False)
            screen.blit(img, img.get_rect(midbottom=self.rect.midbottom))
            pygame.draw.rect(screen, GREEN, self.rect, 2)
        else:
            pygame.draw.rect(screen, CYAN if self.blocking else self.base_color, self.rect)

    def reset(self):
        self.rect.x, self.rect.y, self.health = self.start_x, self.start_y, 100
        self.attacking, self.attack_type, self.blocking = False, "", False


def draw_health_bar(health, x, y):
    pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 304, 34))
    pygame.draw.rect(screen, RED, (x, y, 300, 30))
    pygame.draw.rect(screen, GREEN, (x, y, 300 * (health / 100), 30))

# --- MAIN SETUP ---
fighter_1 = Fighter(400, 520, BLUE, 1)
fighter_2 = Fighter(700, 520, RED, 2, is_cpu=True)

vis_punching = False
vis_kicking = False
vis_guarding = False

# 1. SHOW START SCREEN ONCE
show_start_screen(screen, background, SCREEN_WIDTH, SCREEN_HEIGHT)

# 2. OUTER LOOP
run_app = True
while run_app:
    
    fighter_1.reset()
    fighter_2.reset()
    match_active = True
    winner_text = ""

    # 3. INNER LOOP (Gameplay)
    while match_active:
        clock.tick(30) 

        # READ WEBCAM & PROCESS AI
        success, frame = cap.read()
        current_vision_action = None
        mini_cam_surface = None
        
        if success:
            # Downscale frame for faster AI processing (optional optimization)
            small_frame = cv2.resize(frame, (640, 480))
            small_frame = cv2.flip(small_frame, 1)
            image_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            results = pose.process(image_rgb)
            
            if results.pose_landmarks:
                h, w, c = small_frame.shape
                landmarks = results.pose_landmarks.landmark
                
                rs = (int(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x * w), int(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y * h))
                re = (int(landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x * w), int(landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y * h))
                rw = (int(landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x * w), int(landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y * h))
                ls = (int(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * w), int(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * h))
                lw = (int(landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x * w), int(landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y * h))
                rh = (int(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x * w), int(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y * h))
                ra = (int(landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x * w), int(landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y * h))
                
                elbow_angle = calculate_angle(rs, re, rw)
                leg_elevation = ra[1] - rh[1]

                if rw[1] < (rs[1] + 30) and lw[1] < (ls[1] + 30):
                    vis_guarding = True
                    vis_punching = vis_kicking = False
                    current_vision_action = "block"
                else:
                    vis_guarding = False
                    if elbow_angle > 170 and not vis_kicking: 
                        vis_punching = True
                    elif elbow_angle < 100:
                        vis_punching = False

                    if leg_elevation < 120 and not vis_punching:
                        vis_kicking = True
                    elif leg_elevation > 200:
                        vis_kicking = False

                    if vis_punching: current_vision_action = "punch"
                    elif vis_kicking: current_vision_action = "kick"

                mp_drawing.draw_landmarks(small_frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
            # Create PiP surface from the drawn small_frame
            small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            small_frame = np.rot90(small_frame) 
            mini_cam_surface = pygame.surfarray.make_surface(small_frame)
            mini_cam_surface = pygame.transform.scale(mini_cam_surface, (200, 150)) 

        # RENDER GAME BACKGROUND
        if background: 
            screen.blit(background, (0, 0))
        else: 
            screen.fill(GRAY)

        # DRAW MINI-WEBCAM 
        if mini_cam_surface:
            screen.blit(mini_cam_surface, (SCREEN_WIDTH//2 - 100, 10))
            pygame.draw.rect(screen, CYAN, (SCREEN_WIDTH//2 - 100, 10, 200, 150), 3)

        # GAME LOGIC
        draw_health_bar(fighter_1.health, 20, 20)
        draw_health_bar(fighter_2.health, 950, 20)

        # Check Win Conditions and Play Audio
        if fighter_1.health <= 0:
            winner_text = "YOU LOST!"
            if sfx_lose and match_active: 
                sfx_lose.play()
            match_active = False
            
        elif fighter_2.health <= 0:
            winner_text = "YOU WIN!"
            if sfx_win and match_active:
                sfx_win.play()
            match_active = False

        fighter_1.move(fighter_2, current_vision_action)
        fighter_2.move(fighter_1)

        fighter_1.draw()
        fighter_2.draw()

        # EVENT HANDLER
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                match_active = False
                run_app = False 

        pygame.display.update()

    # 4. GAME OVER SCREEN
    if run_app and winner_text != "":
        wants_to_replay = show_game_over_screen(screen, background, SCREEN_WIDTH, SCREEN_HEIGHT, winner_text)
        if not wants_to_replay:
            run_app = False

# Clean up
cap.release()
pygame.quit()