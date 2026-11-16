import math

import pygame

from .marble import Marble
from .wall import Wall

# Game Engine

WHITE = (255, 255, 255)
DARK = (40, 40, 50)
WALL_COLOR = (90, 90, 110)
GOAL_COLOR = (60, 200, 120)


class GameEngine:
    DIFFICULTIES = {
        "easy": {"tilt_strength": 0.36, "friction": 0.014, "time_limit_ms": 65000},
        "medium": {"tilt_strength": 0.52, "friction": 0.022, "time_limit_ms": 50000},
        "hard": {"tilt_strength": 0.72, "friction": 0.032, "time_limit_ms": 35000},
    }

    def __init__(self, width, height, difficulty="medium"):
        pygame.init()
        self.width = width
        self.height = height
        self.current_difficulty = "medium"
        self.font = pygame.font.SysFont("Arial", 26)
        self.font_big = pygame.font.SysFont("Arial", 42)
        self.font_small = pygame.font.SysFont("Arial", 18)
        self.quit_requested = False
        self.sounds = {}
        self._load_audio()
        self.reset(difficulty)

    def _load_audio(self):
        try:
            pygame.mixer.init()
        except Exception:
            self.sounds = {}
            return

        def tone(frequency, duration, volume):
            if not pygame.mixer.get_init():
                return None
            sample_rate = 22050
            frames = int(sample_rate * duration)
            data = bytearray()
            for i in range(frames):
                t = i / sample_rate
                value = int(32767 * volume * math.sin(2 * math.pi * frequency * t))
                data.extend(value.to_bytes(2, byteorder="little", signed=True))
            return pygame.mixer.Sound(buffer=bytes(data))

        try:
            self.sounds = {
                "bounce": tone(260, 0.06, 0.15),
                "goal": tone(660, 0.14, 0.25),
                "timeout": tone(120, 0.22, 0.2),
            }
        except Exception:
            self.sounds = {}

    def _play_sound(self, sound_name):
        if not self.sounds:
            return
        sound = self.sounds.get(sound_name)
        if sound is None:
            return
        try:
            sound.play()
        except Exception:
            pass

    def reset(self, difficulty=None):
        if difficulty is not None:
            self.set_difficulty(difficulty)

        self.marble = Marble(50, 50)
        self.max_speed = 9
        self.tilt_strength = self.DIFFICULTIES[self.current_difficulty]["tilt_strength"]
        self.friction = self.DIFFICULTIES[self.current_difficulty]["friction"]
        self.time_limit_ms = self.DIFFICULTIES[self.current_difficulty]["time_limit_ms"]

        self.walls = self._build_maze()
        self.goal_x, self.goal_y, self.goal_radius = self.width - 60, self.height - 60, 22
        self.start_ticks = pygame.time.get_ticks()
        self.game_over = False
        self.result = None
        self.finish_time_ms = None
        self._game_over_logged = False
        self.quit_requested = False

    def set_difficulty(self, difficulty):
        normalized = str(difficulty).lower()
        if normalized not in self.DIFFICULTIES:
            normalized = "medium"
        self.current_difficulty = normalized

    def _build_maze(self):
        walls = []
        t = 16  # wall thickness

        # outer boundary
        walls.append(Wall(0, 0, self.width, t))
        walls.append(Wall(0, self.height - t, self.width, t))
        walls.append(Wall(0, 0, t, self.height))
        walls.append(Wall(self.width - t, 0, t, self.height))

        # a few internal walls forming a simple winding path
        walls.append(Wall(0, 140, self.width - 140, t))
        walls.append(Wall(140, 260, self.width - 140, t))
        walls.append(Wall(0, 380, self.width - 140, t))

        return walls

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or not self.game_over:
            return

        if event.key in (pygame.K_1, pygame.K_KP1):
            self.reset("easy")
        elif event.key in (pygame.K_2, pygame.K_KP2):
            self.reset("medium")
        elif event.key in (pygame.K_3, pygame.K_KP3):
            self.reset("hard")
        elif event.key == pygame.K_r:
            self.reset(self.current_difficulty)
        elif event.key == pygame.K_ESCAPE:
            self.quit_requested = True

    def handle_input(self):
        if self.game_over:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - self.width // 2
        dy = mouse_y - self.height // 2
        dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        ax = (dx / dist) * self.tilt_strength
        ay = (dy / dist) * self.tilt_strength
        self.marble.vx += ax
        self.marble.vy += ay

    def _elapsed_time_ms(self):
        if self.game_over and self.finish_time_ms is not None:
            return self.finish_time_ms
        return pygame.time.get_ticks() - self.start_ticks

    def update(self):
        if self.game_over:
            return

        elapsed = self._elapsed_time_ms()
        if elapsed >= self.time_limit_ms:
            self.game_over = True
            self.result = "timeout"
            self.finish_time_ms = self.time_limit_ms
            self._play_sound("timeout")
            return

        self.marble.vx *= (1 - self.friction)
        self.marble.vy *= (1 - self.friction)

        speed = (self.marble.vx ** 2 + self.marble.vy ** 2) ** 0.5
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.marble.vx *= scale
            self.marble.vy *= scale

        self.marble.x += self.marble.vx
        self.marble.y += self.marble.vy

        self._resolve_wall_collisions()

        gx = self.goal_x - self.marble.x
        gy = self.goal_y - self.marble.y
        if (gx ** 2 + gy ** 2) ** 0.5 <= self.goal_radius:
            self.game_over = True
            self.result = "solved"
            self.finish_time_ms = elapsed
            self._play_sound("goal")

    def _resolve_wall_collisions(self):
        for wall in self.walls:
            wall_rect = wall.rect()
            closest_x = max(wall_rect.left, min(self.marble.x, wall_rect.right))
            closest_y = max(wall_rect.top, min(self.marble.y, wall_rect.bottom))

            dx = self.marble.x - closest_x
            dy = self.marble.y - closest_y
            distance_sq = dx * dx + dy * dy
            if distance_sq >= self.marble.radius ** 2:
                continue

            if distance_sq == 0:
                nx = 0.0
                ny = 0.0
                if self.marble.x < wall_rect.centerx:
                    nx = -1.0
                elif self.marble.x > wall_rect.centerx:
                    nx = 1.0
                if self.marble.y < wall_rect.centery:
                    ny = -1.0
                elif self.marble.y > wall_rect.centery:
                    ny = 1.0
                if nx == 0 and ny == 0:
                    nx = 1.0
                dist = 0.0
            else:
                dist = math.sqrt(distance_sq)
                nx = dx / dist
                ny = dy / dist

            overlap = self.marble.radius - dist
            if overlap <= 0:
                continue

            self.marble.x += nx * overlap
            self.marble.y += ny * overlap

            velocity_along_normal = self.marble.vx * nx + self.marble.vy * ny
            if velocity_along_normal < 0:
                self.marble.vx -= 2 * velocity_along_normal * nx
                self.marble.vy -= 2 * velocity_along_normal * ny
                self.marble.vx *= 0.8
                self.marble.vy *= 0.8
                self._play_sound("bounce")

    def render(self, screen):
        screen.fill(DARK)

        for wall in self.walls:
            pygame.draw.rect(screen, WALL_COLOR, wall.rect())

        pygame.draw.circle(screen, GOAL_COLOR, (self.goal_x, self.goal_y), self.goal_radius)
        pygame.draw.circle(screen, WHITE, (int(self.marble.x), int(self.marble.y)), self.marble.radius)

        elapsed = self._elapsed_time_ms()
        seconds_left = max(0, (self.time_limit_ms - elapsed) // 1000)
        timer_text = self.font.render(f"Time: {seconds_left}s", True, WHITE)
        screen.blit(timer_text, (10, 10))

        if not self.game_over:
            return

        overlay = pygame.Surface((self.width * 0.7, self.height * 0.5), pygame.SRCALPHA)
        overlay.fill((15, 15, 20, 185))
        screen.blit(overlay, (self.width * 0.15, self.height * 0.2))

        if self.result == "solved":
            title = "Maze Solved!"
            detail = f"Finished in {self.finish_time_ms / 1000:.1f}s"
        else:
            title = "Time's Up!"
            detail = "The marble did not reach the goal in time."

        title_surface = self.font_big.render(title, True, WHITE)
        detail_surface = self.font_small.render(detail, True, WHITE)
        hint_surface = self.font_small.render("Press 1/2/3 for Easy/Medium/Hard or R to retry", True, WHITE)

        screen.blit(title_surface, (self.width * 0.5 - title_surface.get_width() / 2, self.height * 0.32))
        screen.blit(detail_surface, (self.width * 0.5 - detail_surface.get_width() / 2, self.height * 0.42))
        screen.blit(hint_surface, (self.width * 0.5 - hint_surface.get_width() / 2, self.height * 0.52))
