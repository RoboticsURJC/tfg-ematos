import os
import pygame
import sys
import time
import random
import math

# ================= INIT =================
pygame.init()
pygame.font.init()
pygame.mixer.init()

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
INFO_BAR_HEIGHT = 80
SQUARE_SIZE = 120
TIME_SHOW = 1.0

# screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("Robot Memory Interface")
clock = pygame.time.Clock()

# ================= COLORS =================
BG_TOP = (220, 240, 255)
BG_BOTTOM = (200, 225, 245)

NEON_BLUE = (0, 120, 255)
NEON_GREEN = (0, 255, 120)
NEON_PINK = (255, 20, 120)
WHITE = (250, 250, 250)
BLACK = (20, 20, 20)
INFO_BAR_COLOR = (230, 245, 255)
BUTTON_HOVER = (100, 200, 255)

# ================= FONT =================
font = pygame.font.SysFont("Arial", 28, bold=True)
big_font = pygame.font.SysFont("Arial", 50, bold=True)

current_dir = os.path.dirname(os.path.abspath(__file__))
hidden_img = pygame.image.load(f"{current_dir}/assets/oculta.png")
hidden_img = pygame.transform.scale(hidden_img, (SQUARE_SIZE, SQUARE_SIZE))

# ================= SOUNDS =================
pygame.mixer.music.load(f"{current_dir}/assets/fondo.wav")
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1)

sound_flip = pygame.mixer.Sound(f"{current_dir}/assets/voltear.wav")
sound_wrong = pygame.mixer.Sound(f"{current_dir}/assets/equivocado.wav")
sound_win = pygame.mixer.Sound(f"{current_dir}/assets/ganador.wav")

# ================= LEVELS =================
LEVEL_SIZES = {1:(2,2), 2:(2,4), 3:(4,4), 4:(4,6)}

# ================= CARD CLASS =================
class Card:
    def __init__(self, image_path):
        self.show = False
        self.matched = False
        self.image_path = image_path
        self.image = pygame.transform.scale(
            pygame.image.load(image_path), (SQUARE_SIZE, SQUARE_SIZE)
        )
        self.flip_progress = 0
        self.flipping = False

# ================= PARTICLES =================
class Particle:
    def __init__(self,x,y,color):
        self.x=x
        self.y=y
        self.vx=random.uniform(-2,2)
        self.vy=random.uniform(-5,-1)
        self.color=color
        self.life=1.0
    def update(self):
        self.x+=self.vx
        self.y+=self.vy
        self.vy+=0.1
        self.life-=0.02
    def draw(self,surface):
        if self.life>0:
            pygame.draw.circle(surface,self.color,(int(self.x),int(self.y)),int(5*self.life))

# ================= HELPERS =================
def draw_background(surface, c1, c2):
    for y in range(surface.get_height()):
        ratio = y / surface.get_height()
        r = int(c1[0]*(1-ratio) + c2[0]*ratio)
        g = int(c1[1]*(1-ratio) + c2[1]*ratio)
        b = int(c1[2]*(1-ratio) + c2[2]*ratio)
        pygame.draw.line(surface, (r,g,b), (0,y), (surface.get_width(),y))

def draw_glow_text(text, x, y, color):
    glow = font.render(text, True, NEON_BLUE)
    screen.blit(glow, (x+2, y+2))
    main = font.render(text, True, color)
    screen.blit(main, (x, y))

def create_matrix(level):
    rows, cols = LEVEL_SIZES[level]
    images = ["coco.png","manzana.png","limón.png","naranja.png",
              "pera.png","piña.png","plátano.png","sandía.png"]
    pairs = (rows*cols)//2
    selected = random.sample(images, pairs)
    cards = selected*2
    random.shuffle(cards)
    matrix=[]
    i=0
    for r in range(rows):
        row=[]
        for c in range(cols):
            path=f"{current_dir}/assets/{cards[i]}"
            row.append(Card(path))
            i+=1
        matrix.append(row)
    return matrix, rows, cols

# ================= GAME STATE =================
game_state="menu"
level=1
matrix, rows, cols = create_matrix(level)
x1=y1=x2=y2=None
can_play=True
last_time=None
start_time=None
win_timer=0
particles=[]
celebration_active=False
celebration_timer=0

# ================= MAIN LOOP =================
while True:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # ===== MENU =====
        if game_state=="menu":
            if event.type==pygame.MOUSEBUTTONDOWN:
                # Niveles
                for lvl in LEVEL_SIZES:
                    rect = pygame.Rect(SCREEN_WIDTH//2-100, 150+(lvl-1)*80, 200,60)
                    if rect.collidepoint(event.pos):
                        level=lvl
                        matrix, rows, cols=create_matrix(level)
                        game_state="playing"
                        start_time=time.time()
                        x1=y1=x2=y2=None
                        can_play=True
                # Salir
                exit_rect = pygame.Rect(SCREEN_WIDTH//2-100, 150+len(LEVEL_SIZES)*80, 200,60)
                if exit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

        # ===== PLAYING =====
        elif game_state=="playing":
            board_w = cols*SQUARE_SIZE
            board_h = rows*SQUARE_SIZE
            offset_x=(SCREEN_WIDTH-board_w)//2
            offset_y=(SCREEN_HEIGHT-INFO_BAR_HEIGHT-board_h)//2

            if event.type==pygame.MOUSEBUTTONDOWN and can_play:
                # MENU button
                if event.pos[1]>SCREEN_HEIGHT-INFO_BAR_HEIGHT and event.pos[0]>SCREEN_WIDTH-180:
                    game_state="menu"
                    continue

                x_abs, y_abs = event.pos
                if not(offset_x<=x_abs<=offset_x+board_w and offset_y<=y_abs<=offset_y+board_h):
                    continue

                x=(x_abs-offset_x)//SQUARE_SIZE
                y=(y_abs-offset_y)//SQUARE_SIZE
                card=matrix[y][x]
                if card.show or card.matched: continue
                card.show=True
                card.flipping=True
                sound_flip.play()
                if x1 is None:
                    x1, y1 = x,y
                else:
                    x2, y2 = x,y
                    c1 = matrix[y1][x1]
                    c2 = matrix[y2][x2]
                    if c1.image_path==c2.image_path:
                        c1.matched=c2.matched=True
                        x1=y1=x2=y2=None
                    else:
                        last_time=time.time()
                        can_play=False
                        sound_wrong.play()

    # WAIT AFTER FAIL
    if game_state=="playing" and not can_play:
        if time.time()-last_time>=TIME_SHOW:
            matrix[y1][x1].show=False
            matrix[y2][x2].show=False
            matrix[y1][x1].flip_progress=0
            matrix[y2][x2].flip_progress=0
            x1=y1=x2=y2=None
            can_play=True

    # ===== LEVEL UP / WIN CHECK =====
    if game_state=="playing":
        if all(card.matched for row in matrix for card in row):
            if level < max(LEVEL_SIZES.keys()) and not celebration_active:
                # Activar celebración antes de subir nivel
                celebration_active = True
                celebration_timer = time.time()
                board_w = cols*SQUARE_SIZE
                board_h = rows*SQUARE_SIZE
                offset_x=(SCREEN_WIDTH-board_w)//2
                offset_y=(SCREEN_HEIGHT-INFO_BAR_HEIGHT-board_h)//2
                particles = []
                for r in range(rows):
                    for c in range(cols):
                        for _ in range(5):
                            particles.append(Particle(
                                offset_x+c*SQUARE_SIZE+SQUARE_SIZE//2,
                                offset_y+r*SQUARE_SIZE+SQUARE_SIZE//2,
                                random.choice([NEON_BLUE, NEON_GREEN, NEON_PINK])
                            ))
                sound_win.play()
            elif level >= max(LEVEL_SIZES.keys()):
                if game_state != "win":
                    game_state="win"
                    win_timer = time.time()
                    sound_win.play()
                    board_w = cols*SQUARE_SIZE
                    board_h = rows*SQUARE_SIZE
                    offset_x=(SCREEN_WIDTH-board_w)//2
                    offset_y=(SCREEN_HEIGHT-INFO_BAR_HEIGHT-board_h)//2
                    particles = []
                    for r in range(rows):
                        for c in range(cols):
                            for _ in range(5):
                                particles.append(Particle(
                                    offset_x+c*SQUARE_SIZE+SQUARE_SIZE//2,
                                    offset_y+r*SQUARE_SIZE+SQUARE_SIZE//2,
                                    random.choice([NEON_BLUE, NEON_GREEN, NEON_PINK])
                                ))

    # ================= DRAW =================
    draw_background(screen,BG_TOP,BG_BOTTOM)

    # ===== DRAW CELEBRATION =====
    if celebration_active:
        for p in particles:
            p.update()
            p.draw(screen)
        particles[:] = [p for p in particles if p.life>0]
        if time.time()-celebration_timer>1.5:
            celebration_active=False
            level += 1
            matrix, rows, cols = create_matrix(level)
            x1=y1=x2=y2=None
            can_play=True
            start_time=time.time()

    # ===== MENU =====
    if game_state=="menu":
        pygame.draw.rect(screen,WHITE,(SCREEN_WIDTH//2-250,50,500,80),border_radius=20)
        title=big_font.render("SELECT LEVEL",True,BLACK)
        screen.blit(title,(SCREEN_WIDTH//2-180,60))
        for lvl in LEVEL_SIZES:
            rect=pygame.Rect(SCREEN_WIDTH//2-100, 150+(lvl-1)*80,200,60)
            pygame.draw.rect(screen,NEON_BLUE,rect,border_radius=15)
            txt=font.render(f"LEVEL {lvl}",True,BLACK)
            screen.blit(txt,(rect.x+40,rect.y+15))
        exit_rect = pygame.Rect(SCREEN_WIDTH//2-100, 150+len(LEVEL_SIZES)*80,200,60)
        pygame.draw.rect(screen,NEON_PINK,exit_rect,border_radius=15)
        txt_exit=font.render("EXIT",True,BLACK)
        screen.blit(txt_exit,(exit_rect.x+60,exit_rect.y+15))

    # ===== PLAYING =====
    elif game_state=="playing":
        board_w = cols*SQUARE_SIZE
        board_h = rows*SQUARE_SIZE
        offset_x=(SCREEN_WIDTH-board_w)//2
        offset_y=(SCREEN_HEIGHT-INFO_BAR_HEIGHT-board_h)//2
        for r in range(rows):
            for c in range(cols):
                x=offset_x+c*SQUARE_SIZE
                y=offset_y+r*SQUARE_SIZE
                card=matrix[r][c]
                if card.flipping:
                    card.flip_progress+=0.12
                    if card.flip_progress>=1:
                        card.flip_progress=1
                        card.flipping=False
                scale=abs(1-card.flip_progress*2)
                scaled_w=max(1,int(SQUARE_SIZE*scale))
                surf=pygame.transform.scale(hidden_img if card.flip_progress<0.5 else card.image,(scaled_w,SQUARE_SIZE))
                rect_surf=surf.get_rect(center=(x+SQUARE_SIZE//2,y+SQUARE_SIZE//2))
                screen.blit(surf,rect_surf)

        pygame.draw.rect(screen,INFO_BAR_COLOR,(0,SCREEN_HEIGHT-INFO_BAR_HEIGHT,SCREEN_WIDTH,INFO_BAR_HEIGHT))
        elapsed=int(time.time()-start_time)
        draw_glow_text(f"LEVEL {level}   TIME {elapsed}s",20,SCREEN_HEIGHT-INFO_BAR_HEIGHT+20,BLACK)
        total=(rows*cols)//2
        matched=sum(1 for row in matrix for card in row if card.matched)//2
        ratio=matched/total
        pygame.draw.rect(screen,(180,180,220),(20,SCREEN_HEIGHT-30,300,15),border_radius=10)
        pygame.draw.rect(screen,NEON_GREEN,(20,SCREEN_HEIGHT-30,int(300*ratio),15),border_radius=10)
        menu_rect=pygame.Rect(SCREEN_WIDTH-180,SCREEN_HEIGHT-INFO_BAR_HEIGHT+20,150,40)
        pygame.draw.rect(screen,NEON_PINK,menu_rect,border_radius=12)
        screen.blit(font.render("MENU",True,BLACK),(menu_rect.x+40,menu_rect.y+8))

    # ===== WIN SCREEN =====
    elif game_state=="win":
        for p in particles:
            p.update()
            p.draw(screen)
        particles[:] = [p for p in particles if p.life>0]
        elapsed=time.time()-win_timer
        pulse=abs(math.sin(elapsed*3))*20
        text=big_font.render("VICTORY!",True,NEON_GREEN)
        rect=text.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2-pulse))
        screen.blit(text,rect)
        sub=font.render("Touch to return to menu",True,BLACK)
        screen.blit(sub,(SCREEN_WIDTH//2-150,SCREEN_HEIGHT//2+60))
        if any(e.type==pygame.MOUSEBUTTONDOWN for e in events):
            game_state="menu"

    pygame.display.update()
    clock.tick(60)