#!/usr/bin/env python3
import os
import argparse
import math

parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true")
args = parser.parse_args()

if args.headless:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Surface
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_1, K_2, K_3, K_4

RENDER_W, RENDER_H = 1000, 1000
INTERNAL_W, INTERNAL_H = 32, 32
WINDOW_W, WINDOW_H = 320, 320
FPS = 30

STATES = ["idle", "travail", "reflexion", "parle"]
CURRENT_STATE = "idle"


def draw_eyes(surface: Surface, t: int, state: str) -> None:
    width, height = surface.get_size()
    surface.fill((255, 255, 255))

    face_offset_x = int((width // 50) * math.sin(t * 0.015))
    face_offset_y = int((height // 50) * math.cos(t * 0.02))

    eye_radius = width // 8
    iris_radius = eye_radius // 2.5
    pupil_radius = iris_radius // 2

    left_eye_x = width // 3 + face_offset_x
    right_eye_x = 2 * width // 3 + face_offset_x
    eye_y = height // 2 + face_offset_y

    if state == "idle":
        head_offset_x = int((width // 50) * math.sin(t * 0.02))
        head_offset_y = int((height // 60) * math.cos(t * 0.03))
    elif state == "travail":
        head_offset_x = int((width // 40) * math.sin(t * 0.06))
        head_offset_y = int((height // 50) * math.cos(t * 0.05))
    elif state == "reflexion":
        head_offset_x = int((width // 60) * math.sin(t * 0.03))
        head_offset_y = int((height // 40) * math.sin(t * 0.04))
    elif state == "parle":
        head_offset_x = int((width // 45) * math.sin(t * 0.1))
        head_offset_y = int((height // 50) * math.sin(t * 0.08))
    else:
        head_offset_x = 0
        head_offset_y = 0

    blink = (t % 120) < 10

    def draw_eye(cx, cy):
        pygame.draw.circle(surface, (0, 0, 0), (cx, cy), eye_radius)

        if not blink:
            iris_x = cx + head_offset_x
            iris_y = cy + head_offset_y

            iris_x = max(cx - iris_radius, min(iris_x, cx + iris_radius))
            iris_y = max(cy - iris_radius, min(iris_y, cy + iris_radius))

            pygame.draw.circle(surface, (70, 130, 180), (iris_x, iris_y), int(iris_radius))
            pygame.draw.circle(surface, (0, 0, 0), (iris_x, iris_y), int(pupil_radius))

    draw_eye(left_eye_x, eye_y)
    draw_eye(right_eye_x, eye_y)

    mouth_y = int(height * 0.7) + face_offset_y
    mouth_width = width // 5
    mouth_center = width // 2 + face_offset_x
    mouth_height = int(mouth_width // 3)

    if state == "idle":
        y_offset = int(mouth_height * 0.3 * math.sin(t * 0.04))
        pygame.draw.arc(surface, (0, 0, 0), (mouth_center - mouth_width, mouth_y + y_offset, mouth_width * 2, mouth_height), 0, math.pi, 3)
    elif state == "travail":
        pygame.draw.line(surface, (0, 0, 0), (mouth_center - mouth_width // 2, mouth_y), (mouth_center + mouth_width // 2, mouth_y), 3)
    elif state == "reflexion":
        pygame.draw.circle(surface, (0, 0, 0), (mouth_center, mouth_y), int(mouth_width // 4), 3)
    elif state == "parle":
        y_offset = int(mouth_height * 0.5 * (0.5 + 0.5 * math.sin(t * 0.15)))
        pygame.draw.ellipse(surface, (0, 0, 0), (mouth_center - mouth_width // 2, mouth_y - y_offset, mouth_width, y_offset * 2))


def main():
    global CURRENT_STATE
    pygame.init()
    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Eyes")

    t = 0
    running = True

    if args.headless:
        hq = Surface((RENDER_W, RENDER_H))
        draw_eyes(hq, t, "idle")
        logical = pygame.transform.scale(hq, (INTERNAL_W, INTERNAL_H))
        scaled = pygame.transform.scale(logical, (WINDOW_W, WINDOW_H))
        pygame.image.save(scaled, "output.png")
        print("Saved output.png")
        pygame.quit()
        return

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_1:
                    CURRENT_STATE = "idle"
                elif event.key == K_2:
                    CURRENT_STATE = "travail"
                elif event.key == K_3:
                    CURRENT_STATE = "reflexion"
                elif event.key == K_4:
                    CURRENT_STATE = "parle"

        hq = Surface((RENDER_W, RENDER_H))
        draw_eyes(hq, t, CURRENT_STATE)
        logical = pygame.transform.scale(hq, (INTERNAL_W, INTERNAL_H))
        scaled = pygame.transform.scale(logical, (WINDOW_W, WINDOW_H))
        screen.blit(scaled, (0, 0))
        pygame.display.flip()

        t += 1
        clock.tick(FPS)

    pygame.quit()


if __name__ == '__main__':
    main()
