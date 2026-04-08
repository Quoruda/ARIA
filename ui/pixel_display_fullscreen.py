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
FACE_W, FACE_H = 320, 320
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
    
    # Borderless Window
    infoObject = pygame.display.Info()
    global WINDOW_W, WINDOW_H
    WINDOW_W, WINDOW_H = infoObject.current_w, infoObject.current_h
    pygame.display.set_mode((WINDOW_W, WINDOW_H), NOFRAME | pygame.FULLSCREEN)
    pygame.display.set_caption("Pixel Display System (Fullscreen)")

    # Calculate offsets to center the face on the screen
    OFFSET_X = (WINDOW_W - FACE_W) // 2
    OFFSET_Y = (WINDOW_H - FACE_H) // 2

    # Cross-platform window management
    win_manager = WindowManager()
    win_manager.enable_transparency(COLOR_TRANSPARENT)
    win_manager.set_always_on_top()

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
    dragging, d_ox, d_oy = False, 0, 0

    while running:
        for event in pygame.event.get():
            if event.type == QUIT: running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE: running = False
                elif event.key in STATE_KEYS: 
                    current_state = STATE_KEYS[event.key]
                    state_t = 0
            
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    dragging = True
                    d_ox, d_oy = pygame.mouse.get_pos()
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False
            
        if dragging:
            gx, gy = win_manager.get_global_mouse_pos()
            win_manager.move_window(gx - d_ox, gy - d_oy)

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
                    # Use static mask as the final shape
                    win_manager.apply_linux_mask(static_mask, offset_x=OFFSET_X, offset_y=OFFSET_Y)
                    break
            win_manager.apply_linux_mask(boot_grid, offset_x=OFFSET_X, offset_y=OFFSET_Y)

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
        
        # APPLY MASKS (Hardware mask + Surface mask)
        for y in range(INTERNAL_H):
            for x in range(INTERNAL_W):
                # Permanently hide pixels from static_mask
                # OR hide unrevealed pixels during boot
                if not static_mask[y][x] or (current_state == "booting" and not boot_grid[y][x]):
                    pixel_surf.set_at((x, y), COLOR_TRANSPARENT)
        
        final_surf = pygame.transform.scale(pixel_surf, (FACE_W, FACE_H))
        screen = pygame.display.get_surface()
        screen.set_colorkey(COLOR_TRANSPARENT)
        screen.fill(COLOR_TRANSPARENT) 
        screen.blit(final_surf, (OFFSET_X, OFFSET_Y))
        pygame.display.flip()
        
        global_t += 1
        state_t += 1
        clock.tick(FPS)

    win_manager.close()
    pygame.quit()

if __name__ == '__main__':
    main()
