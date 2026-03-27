#!/usr/bin/env python3
import math
import pygame
from pygame import Surface

class AnimatedFace:
    """Class dedicated to rendering the animated face."""
    def __init__(self, width, height, colors):
        self.width = width
        self.height = height
        self.colors = colors
        self.thickness = 40

    def render(self, surface: Surface, state: str, t: int):
        # 1. Global Drift
        face_offset_x = int((self.width // 60) * math.sin(t * 0.01))
        face_offset_y = int((self.height // 60) * math.cos(t * 0.015))
        
        # 2. Background
        surface.fill(self.colors['BACKGROUND'])
        
        # 3. Ambient Glows (Cumulative for depth) - Warm theme aware
        for i in range(8):
            gx = self.width // 2 + int(self.width // 4 * math.sin(i * 1.5)) + (face_offset_x // 2)
            gy = self.height // 2 + int(self.width // 4 * math.cos(i * 0.7)) + (face_offset_y // 2)
            radius = int(self.width // 1.4 + (i * 120))
            shade = 35 + i * 4
            # Use base background color to derive shades
            bg_r, bg_g, bg_b = self.colors['BACKGROUND']
            c_val = (min(255, bg_r + i*3), min(255, bg_g + i*3), min(255, bg_b + i*5))
            pygame.draw.circle(surface, c_val, (gx, gy), radius)

        # 4. Cinematic Grain
        for _ in range(600):
            nx = (97 * _) % self.width
            ny = (131 * _) % self.height
            n_shade = 5 + (math.sin(_) * 10)
            bg_r, bg_g, bg_b = self.colors['BACKGROUND']
            surface.set_at((nx, ny), (min(255, int(bg_r + n_shade)), min(255, int(bg_g + n_shade)), min(255, int(bg_b + n_shade))))

        # 5. Light fog/glow behind face
        for r in range(self.width // 2, 0, -self.width // 10):
            shade = 20 + (self.width // 2 - r) // 10
            ir, ig, ib = self.colors['FACE_IRIS']
            c_val = (min(255, max(0, ir // 4 + shade)), min(255, max(0, ig // 4 + shade)), min(255, max(0, ib // 4 + shade)))
            pygame.draw.circle(surface, c_val, (self.width // 2 + face_offset_x, self.height // 2 + face_offset_y), r)

        # 6. Vignette
        for i in range(6):
            rect = (-150 - i*60 + face_offset_x, -150 - i*60 + face_offset_y, self.width + 300 + i*120, self.height + 300 + i*120)
            pygame.draw.ellipse(surface, self.colors['VIGNETTE'], rect, 150)

        # 7. Animation Logic
        pupil_offset_x, pupil_offset_y = 0, 0
        mouth_y_base = int(self.height * 0.7)
        mouth_w, mouth_h = self.width // 3, self.width // 6
        mouth_shape = "smile"
        eye_open_factor = 1.0 # Default fully open
        
        if state == "booting":
            eye_open_factor = 0.0 # Eyes closed during boot
            mouth_shape = "smile"
        elif state == "opening":
            # Smoothly open eyes over 30 frames
            eye_open_factor = min(1.0, t / 30.0)
            mouth_shape = "smile"
        elif state == "idle":
            face_offset_y += int((self.height // 80) * math.sin(t * 0.03))
            pupil_offset_x = int((self.width // 30) * math.sin(t * 0.01))
            mouth_shape = "smile"
        elif state == "working":
            face_offset_y += int((self.height // 100) * math.sin(t * 0.05))
            pupil_offset_x = int((self.width // 20) * math.sin(t * 0.1))
            mouth_shape = "focus"
        elif state == "thinking":
            face_offset_x += int((self.width // 100) * math.sin(t * 0.02))
            face_offset_y += int((self.height // 80) * math.cos(t * 0.02))
            pupil_offset_x, pupil_offset_y = int(self.width // 40), -int(self.height // 20)
            mouth_shape = "think"
        elif state == "speaking":
            mouth_open = 0.5 + 0.4 * math.sin(t * 0.8)
            face_offset_y += int((self.height // 100) * math.sin(t * 0.1))
            pupil_offset_y = int((self.height // 80) * math.sin(t * 0.05))
            mouth_shape = "speak"
            mouth_h = int(self.width // 24 * mouth_open)

        # Draw features
        self._draw_eyes(surface, face_offset_x, face_offset_y, pupil_offset_x, pupil_offset_y, t, eye_open_factor)
        self._draw_mouth(surface, face_offset_x, face_offset_y, mouth_y_base, mouth_w, mouth_h, mouth_shape)

    def _draw_eyes(self, surface, fx, fy, px, py, t, open_factor=1.0):
        eye_radius, iris_radius, pupil_radius = self.width // 8, self.width // 20, self.width // 40
        shadow_offset = self.thickness // 2
        # Normal blink every 5 seconds
        blink = (t % 150) < 10
        
        # Combined factor
        current_open = open_factor if not blink else 0.0
        
        centers = [(self.width // 3 + fx, self.height // 2 + fy), (2 * self.width // 3 + fx, self.height // 2 + fy)]
        for c in centers:
            # Shadow
            pygame.draw.circle(surface, self.colors['FACE_SHADOW'], (c[0] + shadow_offset, c[1] + shadow_offset), eye_radius)
            
            # Eye socket / lid
            if current_open <= 0.1:
                # Closed: just a line
                pygame.draw.line(surface, self.colors['FACE_MAIN'], (c[0] - eye_radius, c[1]), (c[0] + eye_radius, c[1]), self.thickness)
            else:
                # Open: circle
                pygame.draw.circle(surface, self.colors['FACE_MAIN'], c, eye_radius)
                # Iris and Pupil (only if open enough)
                if current_open > 0.5:
                    ix = max(c[0] - eye_radius//2, min(c[0] + px, c[0] + eye_radius//2))
                    iy = max(c[1] - eye_radius//2, min(c[1] + py, c[1] + eye_radius//2))
                    pygame.draw.circle(surface, self.colors['FACE_IRIS'], (ix, iy), int(iris_radius * current_open))
                    pygame.draw.circle(surface, self.colors['FACE_MAIN'], (ix, iy), int(pupil_radius * current_open))

    def _draw_mouth(self, surface, fx, fy, y_base, w, h, shape):
        mx, my, so = self.width // 2 + fx, y_base + fy, self.thickness // 2
        def _put(x, y, color):
            if shape == "smile": pygame.draw.arc(surface, color, (x - w // 2, y - h // 2, w, h), math.pi, 2 * math.pi, self.thickness)
            elif shape == "focus": pygame.draw.line(surface, color, (x - w // 2, y), (x + w // 2, y), self.thickness)
            elif shape == "think": pygame.draw.circle(surface, color, (x, y), int(w // 6), self.thickness)
            elif shape == "speak": pygame.draw.ellipse(surface, color, (x - w // 4, y - h, w // 2, h * 2 + self.thickness))
        _put(mx + so, my + so, self.colors['FACE_SHADOW'])
        _put(mx, my, self.colors['FACE_MAIN'])


# CLASSIC FUNCTIONS (SYSTEM MODES)

def draw_loading(surface: Surface, t: int, width: int, height: int, colors: dict):
    """Displays a theme-aware classic loading spinner without the face."""
    surface.fill(colors['BACKGROUND'])
    center = (width // 2, height // 2)
    radius, dot_r, num_dots = width // 6, width // 30, 8
    ir, ig, ib = colors['FACE_IRIS']
    for i in range(num_dots):
        angle = (t * 0.1) + (i * (2 * math.pi / num_dots))
        dx, dy = center[0] + int(radius * math.cos(angle)), center[1] + int(radius * math.sin(angle))
        # Fade based on the iris color
        p = i / num_dots
        c_val = (min(255, int(ir * p)), min(255, int(ig * p)), min(255, int(ib * p)))
        pygame.draw.circle(surface, c_val, (dx, dy), dot_r)

def draw_exploding(surface: Surface, t: int, width: int, height: int, colors: dict):
    """Displays a theme-aware particle explosion from all sides."""
    surface.fill(colors['BACKGROUND'])
    ir, ig, ib = colors['FACE_IRIS']
    center, num_particles = (width // 2, height // 2), 120
    GOLDEN_RATIO = 1.61803398875
    
    for i in range(num_particles):
        p_t = ((t + i * GOLDEN_RATIO * 10) % 60) / 60.0
        angle = (i * (2 * math.pi / num_particles)) + (t * 0.03) + (math.sin(i) * 0.5)
        speed_var = 0.4 + (hash(str(i*13)) % 100) / 100.0
        dist = int(width * 0.7 * (p_t ** 1.3) * speed_var)
        px, py = center[0] + int(dist * math.cos(angle)), center[1] + int(dist * math.sin(angle))
        r = int(width // 25 * (1.0 - p_t))
        if r > 0:
            # Shift from highlight to iris color
            c = (min(255, int(255*(1-p_t) + ir*p_t)), min(255, int(240*(1-p_t) + ig*p_t)), min(255, int(200*(1-p_t) + ib*p_t)))
            pygame.draw.circle(surface, c, (px, py), r)
            if p_t < 0.15:
                # Use current highlight color
                pygame.draw.circle(surface, colors['LIGHT_BASE'], (px, py), max(1, r // 2))
