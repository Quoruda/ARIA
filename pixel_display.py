#!/usr/bin/env python3
import pygame
from pygame import Surface
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_1, K_2, K_3, K_4, K_5, K_6, NOFRAME, MOUSEBUTTONDOWN, MOUSEBUTTONUP

from pixel_renderer import AnimatedFace, draw_loading, draw_exploding
from window_manager import WindowManager

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

STATE_KEYS = {K_1: "idle", K_2: "working", K_3: "thinking", K_4: "speaking", K_5: "loading", K_6: "exploding"}

def main():
    pygame.init()
    clock = pygame.time.Clock()
    
    # Borderless Window
    pygame.display.set_mode((WINDOW_W, WINDOW_H), NOFRAME)
    pygame.display.set_caption("Pixel Display System")

    # Cross-platform window management
    win_manager = WindowManager()

    face_renderer = AnimatedFace(RENDER_W, RENDER_H, COLORS)
    current_state = "idle"
    t = 0
    running = True

    # Mouse dragging state
    dragging = False
    drag_offset_x, drag_offset_y = 0, 0

    while running:
        for event in pygame.event.get():
            if event.type == QUIT: running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE: running = False
                elif event.key in STATE_KEYS: current_state = STATE_KEYS[event.key]
            
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    dragging = True
                    mx, my = pygame.mouse.get_pos()
                    drag_offset_x, drag_offset_y = mx, my
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False
            
        if dragging:
            # Multi-platform global mouse and window move
            gx, gy = win_manager.get_global_mouse_pos()
            win_manager.move_window(gx - drag_offset_x, gy - drag_offset_y)

        # Rendering logic
        hq_surf = Surface((RENDER_W, RENDER_H))
        if current_state == "loading":
            draw_loading(hq_surf, t, RENDER_W, RENDER_H, COLORS)
        elif current_state == "exploding":
            draw_exploding(hq_surf, t, RENDER_W, RENDER_H, COLORS)
        else:
            face_renderer.render(hq_surf, current_state, t)

        # Pixel Art transformation
        pixel_surf = pygame.transform.scale(hq_surf, (INTERNAL_W, INTERNAL_H))
        final_surf = pygame.transform.scale(pixel_surf, (WINDOW_W, WINDOW_H))

        screen = pygame.display.get_surface()
        screen.blit(final_surf, (0, 0))
        pygame.display.flip()
        
        t += 1
        clock.tick(FPS)

    win_manager.close()
    pygame.quit()

if __name__ == '__main__':
    main()
