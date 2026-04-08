#!/usr/bin/env python3
import os
import sys

# Add the parent directory to the Python path so we can import 'ui'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.name != 'nt':
    os.environ['SDL_VIDEODRIVER'] = 'x11'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
import random
import warnings
from pygame import Surface
from pygame.locals import (
    QUIT,
    KEYDOWN,
    K_ESCAPE,
    K_1,
    K_2,
    K_3,
    K_4,
    K_5,
    K_6,
    NOFRAME,
    MOUSEBUTTONDOWN,
    MOUSEBUTTONUP,
)

from ui.pixel_renderer import AnimatedFace, draw_loading, draw_exploding
from ui.window_manager import WindowManager

# CONFIGURATION
RENDER_W, RENDER_H = 1000, 1000
INTERNAL_W, INTERNAL_H = 32, 32
WINDOW_W, WINDOW_H = 320, 320
FPS = 30

# SEMANTIC COLORS
COLORS = {
    'BACKGROUND': (30, 30, 45),
    'VIGNETTE': (15, 15, 25),
    'FACE_MAIN': (0, 0, 0),
    'FACE_IRIS': (70, 130, 180),
    'FACE_SHADOW': (40, 40, 60),
    'LIGHT_BASE': (255, 255, 255)
}
COLOR_TRANSPARENT = (255, 0, 255) # Magic Pink

STATE_KEYS = {K_1: "idle", K_2: "working", K_3: "thinking", K_4: "speaking", K_5: "loading", K_6: "exploding"}

def main():
    pygame.init()
    clock = pygame.time.Clock()
    
    # Bordered Window
    pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Pixel Display System (Windowed)")

    face_renderer = AnimatedFace(RENDER_W, RENDER_H, COLORS)
    
    # STATIC MASK (Permanent jagged edges)
    static_mask = [[True for _ in range(INTERNAL_W)] for _ in range(INTERNAL_H)]
    for y in range(INTERNAL_H):
        for x in range(INTERNAL_W):
            # Distance from the very center
            cx, cy = 15.5, 15.5
            dist = ((x - cx)**2 + (y - cy)**2)**0.5
            # Threshold to cut: 
            # 15.5 is a circle, 21.9 is the corner
            # More aggressive and irregular:
            threshold = 18.2 + random.uniform(-1.8, 1.8)
            if dist > threshold:
                static_mask[y][x] = False

    # SYSTEM STATES
    current_state = "booting"
    state_t = 0 # Local timer for the current state
    
    # BOOT SEQUENCE DATA
    boot_grid = [[False for _ in range(INTERNAL_W)] for _ in range(INTERNAL_H)]
    # Only reveal pixels that are in the static_mask
    boot_coords = [(x, y) for y in range(INTERNAL_H) for x in range(INTERNAL_W) if static_mask[y][x]]
    # Sort by distance from center with jitter
    boot_coords.sort(key=lambda p: ((p[0]-15.5)**2 + (p[1]-15.5)**2)**0.5 + random.uniform(-2, 2))
    boot_idx = 0
    
    global_t = 0
    running = True

    # Mouse dragging state
    dragging = False

    while running:
        for event in pygame.event.get():
            if event.type == QUIT: running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE: running = False
                elif event.key in STATE_KEYS: 
                    current_state = STATE_KEYS[event.key]
                    state_t = 0
            
        # BOOT & OPENING SEQUENCES LOGIC
        if current_state == "booting":
            pixels_per_frame = 20
            for _ in range(pixels_per_frame):
                if boot_idx < len(boot_coords):
                    bx, by = boot_coords[boot_idx]
                    boot_grid[by][bx] = True
                    boot_idx += 1
                else:
                    current_state = "opening"
                    state_t = 0
                    break
        elif current_state == "opening":
            if state_t >= 30: # Open eyes for 1 second
                current_state = "idle"
                state_t = 0

        # Rendering
        hq_surf = Surface((RENDER_W, RENDER_H))
        
        # Determine what to draw
        if current_state == "loading":
            draw_loading(hq_surf, global_t, RENDER_W, RENDER_H, COLORS)
        elif current_state == "exploding":
            draw_exploding(hq_surf, global_t, RENDER_W, RENDER_H, COLORS)
        else:
            face_renderer.render(hq_surf, current_state, state_t if current_state == "opening" else global_t)

        # Final scaling and transparency blit
        pixel_surf = Surface((INTERNAL_W, INTERNAL_H))
        pygame.transform.scale(hq_surf, (INTERNAL_W, INTERNAL_H), pixel_surf)
        
        final_surf = pygame.transform.scale(pixel_surf, (WINDOW_W, WINDOW_H))
        screen = pygame.display.get_surface()
        screen.fill(COLORS['BACKGROUND'])
        screen.blit(final_surf, (0, 0))
        pygame.display.flip()
        
        global_t += 1
        state_t += 1
        clock.tick(FPS)

    pygame.quit()

if __name__ == '__main__':
    main()
