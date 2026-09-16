import pygame
import ctypes
import os
import math
import sys
import time
LIB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libengine.so")
engine = ctypes.CDLL(LIB_PATH)
engine.engine_init.argtypes = [ctypes.c_int, ctypes.c_int]
engine.engine_init.restype = None
engine.engine_free.argtypes = []
engine.engine_free.restype = None
engine.engine_reset.argtypes = []
engine.engine_reset.restype = None
engine.engine_set_direction.argtypes = [ctypes.c_int]
engine.engine_set_direction.restype = None
engine.engine_step.argtypes = []
engine.engine_step.restype = ctypes.c_int
engine.engine_update_particles.argtypes = []
engine.engine_update_particles.restype = None
engine.engine_get_state.argtypes = [
    ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int),
    ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int),
]
engine.engine_get_state.restype = ctypes.c_int
GRID_W, GRID_H = 20, 20
CELL = 32
MARGIN = 80
SCREEN_W = GRID_W * CELL + MARGIN * 2
SCREEN_H = GRID_H * CELL + MARGIN + 40
FPS = 60
BG_COLOR = (105, 174, 95)
GRID_COLOR = (120, 188, 110)
SNAKE_HEAD = (34, 100, 34)
SNAKE_BODY = (55, 135, 50)
SNAKE_BODY_ALT = (45, 120, 42)
SNAKE_OUTLINE = (25, 75, 25)
FOOD_COLOR = (210, 60, 50)
FOOD_GLOW = (255, 100, 80)
FOOD_HIGHLIGHT = (255, 160, 140)
TEXT_COLOR = (255, 255, 255)
TEXT_SHADOW = (25, 75, 25)
GRID_LINE_ALPHA = 20
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("Arial", 42, bold=True)
font_medium = pygame.font.SysFont("Arial", 28, bold=True)
font_small = pygame.font.SysFont("Arial", 20)
grid_surface = pygame.Surface((GRID_W * CELL, GRID_H * CELL), pygame.SRCALPHA)
engine.engine_init(GRID_W, GRID_H)
engine.engine_reset()
def get_state():
    snake_buf = (ctypes.c_float * (GRID_W * GRID_H * 2))()
    snake_len = ctypes.c_int()
    food_buf = (ctypes.c_float * 2)()
    score = ctypes.c_int()
    game_over = ctypes.c_int()
    direction = ctypes.c_int()
    particle_buf = (ctypes.c_float * 5000)()
    particle_count = ctypes.c_int()
    trail_buf = (ctypes.c_float * 80)()
    trail_len = ctypes.c_int()
    engine.engine_get_state(
        snake_buf, ctypes.byref(snake_len),
        food_buf, ctypes.byref(score), ctypes.byref(game_over), ctypes.byref(direction),
        particle_buf, ctypes.byref(particle_count),
        trail_buf, ctypes.byref(trail_len),
    )
    snake = [(snake_buf[i*2], snake_buf[i*2+1]) for i in range(snake_len.value)]
    food = (food_buf[0], food_buf[1])
    particles = []
    for i in range(particle_count.value):
        off = i * 7
        particles.append({
            "x": particle_buf[off], "y": particle_buf[off+1], "life": particle_buf[off+2],
            "r": particle_buf[off+3], "g": particle_buf[off+4], "b": particle_buf[off+5],
            "size": particle_buf[off+6],
        })
    trail = [(trail_buf[i*2], trail_buf[i*2+1]) for i in range(trail_len.value)]
    return {
        "snake": snake, "food": food, "score": score.value,
        "game_over": game_over.value, "direction": direction.value,
        "particles": particles, "trail": trail,
    }
def cell_rect(gx, gy, padding=2):
    x = MARGIN + gx * CELL + padding
    y = MARGIN + gy * CELL + padding
    w = CELL - padding * 2
    h = CELL - padding * 2
    return (x, y, w, h)
def draw_rounded_rect(surface, color, rect, radius=8):
    x, y, w, h = rect
    pygame.draw.rect(surface, color, (x + radius, y, w - 2*radius, h))
    pygame.draw.rect(surface, color, (x, y + radius, w, h - 2*radius))
    pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius)
def draw_food(food, tick):
    gx, gy = food
    cx = MARGIN + gx * CELL + CELL // 2
    cy = MARGIN + gy * CELL + CELL // 2
    pulse = 0.5 + 0.5 * math.sin(tick * 0.08)
    glow_r = int(12 + 4 * pulse)
    glow_surf = pygame.Surface((glow_r*4, glow_r*4), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (*FOOD_GLOW, int(80 * pulse)), (glow_r*2, glow_r*2), glow_r)
    screen.blit(glow_surf, (cx - glow_r*2, cy - glow_r*2))
    pygame.draw.circle(screen, FOOD_COLOR, (cx, cy), 10)
    pygame.draw.circle(screen, FOOD_HIGHLIGHT, (cx - 2, cy - 3), 4)
def draw_snake(snake, direction, tick):
    for i in range(len(snake) - 1, -1, -1):
        gx, gy = int(snake[i][0]), int(snake[i][1])
        rect = cell_rect(gx, gy, padding=2)
        if i == 0:
            color = SNAKE_HEAD
            draw_rounded_rect(screen, color, rect, radius=10)
            cx = MARGIN + gx * CELL + CELL // 2
            cy = MARGIN + gy * CELL + CELL // 2
            eye_offset = 4
            if direction == 0:
                e1 = (cx - eye_offset, cy - 3)
                e2 = (cx + eye_offset, cy - 3)
            elif direction == 1:
                e1 = (cx + eye_offset, cy - 3)
                e2 = (cx + eye_offset, cy + 3)
            elif direction == 2:
                e1 = (cx - eye_offset, cy + 3)
                e2 = (cx + eye_offset, cy + 3)
            else:
                e1 = (cx - eye_offset, cy - 3)
                e2 = (cx - eye_offset, cy + 3)
            pygame.draw.circle(screen, (255, 255, 255), e1, 4)
            pygame.draw.circle(screen, (255, 255, 255), e2, 4)
            pygame.draw.circle(screen, (20, 20, 20), e1, 2)
            pygame.draw.circle(screen, (20, 20, 20), e2, 2)
        else:
            color = SNAKE_BODY if i % 2 == 0 else SNAKE_BODY_ALT
            draw_rounded_rect(screen, color, rect, radius=8)
def draw_trail(trail):
    for i, (tx, ty) in enumerate(trail):
        alpha = max(0, 1.0 - i / len(trail)) * 40 if trail else 0
        if alpha <= 0:
            continue
        cx = MARGIN + tx * CELL
        cy = MARGIN + ty * CELL
        surf = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 255, 255, int(alpha)), (3, 3), 3)
        screen.blit(surf, (cx - 3, cy - 3))
def draw_particles(particles):
    for p in particles:
        alpha = int(255 * p["life"])
        size = max(1, int(p["size"] * p["life"]))
        cx = MARGIN + p["x"] * CELL
        cy = MARGIN + p["y"] * CELL
        surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        r = int(p["r"] * 255)
        g = int(p["g"] * 255)
        b = int(p["b"] * 255)
        pygame.draw.circle(surf, (min(255,r), min(255,g), min(255,b), alpha), (size, size), size)
        screen.blit(surf, (cx - size, cy - size))
def draw_grid():
    for x in range(GRID_W + 1):
        pygame.draw.line(grid_surface, (255, 255, 255, GRID_LINE_ALPHA),
                         (x * CELL, 0), (x * CELL, GRID_H * CELL))
    for y in range(GRID_H + 1):
        pygame.draw.line(grid_surface, (255, 255, 255, GRID_LINE_ALPHA),
                         (0, y * CELL), (GRID_W * CELL, y * CELL))
def draw_score(score, tick):
    pygame.draw.rect(screen, (34, 80, 34), (0, 0, SCREEN_W, MARGIN))
    score_text = font_large.render(f"Score: {score}", True, TEXT_COLOR)
    shadow = font_large.render(f"Score: {score}", True, TEXT_SHADOW)
    screen.blit(shadow, (SCREEN_W // 2 - score_text.get_width() // 2 + 2, 22))
    screen.blit(score_text, (SCREEN_W // 2 - score_text.get_width() // 2, 20))
def draw_game_over(score):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))
    box_w, box_h = 340, 200
    bx = (SCREEN_W - box_w) // 2
    by = (SCREEN_H - box_h) // 2
    draw_rounded_rect(screen, (34, 80, 34), (bx, by, box_w, box_h), radius=16)
    pygame.draw.rect(screen, (60, 130, 55), (bx, by, box_w, box_h), width=3, border_radius=16)
    go_text = font_large.render("Game Over", True, FOOD_GLOW)
    screen.blit(go_text, (SCREEN_W // 2 - go_text.get_width() // 2, by + 25))
    sc_text = font_medium.render(f"Score: {score}", True, TEXT_COLOR)
    screen.blit(sc_text, (SCREEN_W // 2 - sc_text.get_width() // 2, by + 80))
    hint = font_small.render("Press SPACE to restart  |  ESC to quit", True, (180, 220, 180))
    screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, by + 140))
def draw_start_screen():
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))
    box_w, box_h = 380, 260
    bx = (SCREEN_W - box_w) // 2
    by = (SCREEN_H - box_h) // 2
    draw_rounded_rect(screen, (34, 80, 34), (bx, by, box_w, box_h), radius=16)
    pygame.draw.rect(screen, (60, 130, 55), (bx, by, box_w, box_h), width=3, border_radius=16)
    title = font_large.render("SNAKE", True, (120, 220, 100))
    screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, by + 20))
    snake_art = font_medium.render("~~~~~>", True, SNAKE_BODY)
    screen.blit(snake_art, (SCREEN_W // 2 - snake_art.get_width() // 2, by + 75))
    start = font_medium.render("Press SPACE to start", True, TEXT_COLOR)
    screen.blit(start, (SCREEN_W // 2 - start.get_width() // 2, by + 130))
    controls = [
        "WASD / Arrow Keys to move",
        "SPACE to restart",
        "ESC to quit",
    ]
    for i, line in enumerate(controls):
        t = font_small.render(line, True, (180, 220, 180))
        screen.blit(t, (SCREEN_W // 2 - t.get_width() // 2, by + 180 + i * 24))
def main():
    tick = 0
    move_delay = 120
    last_move = pygame.time.get_ticks()
    state = "start"
    draw_grid()
    running = True
    while running:
        dt = clock.tick(FPS)
        tick += 1
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if state == "start":
                    if event.key == pygame.K_SPACE:
                        engine.engine_reset()
                        state = "playing"
                        last_move = now
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                elif state == "playing":
                    if event.key in (pygame.K_w, pygame.K_UP):
                        engine.engine_set_direction(0)
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        engine.engine_set_direction(1)
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        engine.engine_set_direction(2)
                    elif event.key in (pygame.K_a, pygame.K_LEFT):
                        engine.engine_set_direction(3)
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                elif state == "gameover":
                    if event.key == pygame.K_SPACE:
                        engine.engine_reset()
                        state = "playing"
                        last_move = now
                    elif event.key == pygame.K_ESCAPE:
                        running = False
        if state == "playing" and now - last_move >= move_delay:
            result = engine.engine_step()
            last_move = now
            if result == 0:
                state = "gameover"
        engine.engine_update_particles()
        s = get_state()
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, GRID_COLOR, (MARGIN - 4, MARGIN - 4,
                          GRID_W * CELL + 8, GRID_H * CELL + 8), border_radius=6)
        screen.blit(grid_surface, (MARGIN, MARGIN))
        draw_trail(s["trail"])
        draw_food(s["food"], tick)
        draw_snake(s["snake"], s["direction"], tick)
        draw_particles(s["particles"])
        draw_score(s["score"], tick)
        if state == "start":
            draw_start_screen()
        elif state == "gameover":
            draw_game_over(s["score"])
        pygame.display.flip()
    engine.engine_free()
    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()
