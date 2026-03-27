import pygame
import os
import ctypes
from ctypes import util
from pygame import Surface
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_1, K_2, K_3, K_4, K_5, K_6, NOFRAME, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from pixel_renderer import AnimatedFace, draw_loading, draw_exploding

# CONFIGURATION
RENDER_W, RENDER_H = 1000, 1000
INTERNAL_W, INTERNAL_H = 32, 32
WINDOW_W, WINDOW_H = 320, 320
FPS = 30

# SEMANTIC COLORS (Original Deep Blue Theme)
COLORS = {
    'BACKGROUND': (30, 30, 45),     # Deep Midnight Blue
    'VIGNETTE': (15, 15, 25),       # Dark Blue-tinted edges
    'FACE_MAIN': (0, 0, 0),         # Pure black
    'FACE_IRIS': (70, 130, 180),    # Steel Blue
    'FACE_SHADOW': (40, 40, 60),    # Muted dark blue shadow
    'LIGHT_BASE': (255, 255, 255)   # Pure white highlight
}

STATE_KEYS = {K_1: "idle", K_2: "working", K_3: "thinking", K_4: "speaking", K_5: "loading", K_6: "exploding"}

def main():
    pygame.init()
    clock = pygame.time.Clock()
    
    # Borderless Window
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), NOFRAME)
    pygame.display.set_caption("Pixel Display System")

    # Get SDL Window pointer for moving
    sdl2_lib = ctypes.CDLL(util.find_library('SDL2'))
    # In Pygame 2, wm_info has 'window' for Linux/X11
    wm_info = pygame.display.get_wm_info()
    sdl_window_ptr = wm_info.get('window') 
    
    # Instance for the face only
    face_renderer = AnimatedFace(RENDER_W, RENDER_H, COLORS)
    
    current_state = "idle"
    t = 0
    running = True

    # Mouse dragging state
    dragging = False
    drag_offset_x = 0
    drag_offset_y = 0

    while running:
        for event in pygame.event.get():
            if event.type == QUIT: running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE: running = False
                elif event.key in STATE_KEYS: current_state = STATE_KEYS[event.key]
            
            # Dragging logic
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    dragging = True
                    mx, my = pygame.mouse.get_pos()
                    drag_offset_x, drag_offset_y = mx, my
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False
            elif event.type == MOUSEMOTION:
                if dragging:
                    # Use SDL directly to get global screen mouse position
                    # SDL_GetGlobalMouseState(int *x, int *y)
                    mx_global = ctypes.c_int()
                    my_global = ctypes.c_int()
                    if sdl2_lib:
                        sdl2_lib.SDL_GetGlobalMouseState(ctypes.byref(mx_global), ctypes.byref(my_global))
                        # Calculate and set new window position
                        new_x = mx_global.value - drag_offset_x
                        new_y = my_global.value - drag_offset_y
                        if sdl_window_ptr:
                            sdl2_lib.SDL_SetWindowPosition(sdl_window_ptr, new_x, new_y)
        hq_surf = Surface((RENDER_W, RENDER_H))

        # ROUTING THE DRAWING ACCORDING TO STATE
        if current_state == "loading":
            draw_loading(hq_surf, t, RENDER_W, RENDER_H, COLORS)
        elif current_state == "exploding":
            draw_exploding(hq_surf, t, RENDER_W, RENDER_H, COLORS)
        else:
            # Drawing handled by the special AnimatedFace class
            face_renderer.render(hq_surf, current_state, t)

        # TRANSFORMATION 32X32 (PIXEL ART EFFECT)
        pixel_surf = pygame.transform.scale(hq_surf, (INTERNAL_W, INTERNAL_H))
        final_surf = pygame.transform.scale(pixel_surf, (WINDOW_W, WINDOW_H))

        screen.blit(final_surf, (0, 0))
        pygame.display.flip()
        t += 1
        clock.tick(FPS)

    pygame.quit()

if __name__ == '__main__':
    main()
