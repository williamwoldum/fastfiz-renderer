from typing import Tuple

import pygame


class GameBall:
    ball_colors = {
        0: (255, 255, 255),  # White
        1: (255, 255, 0),  # Yellow
        2: (0, 0, 255),  # Blue
        3: (255, 0, 0),  # Red
        4: (255, 0, 255),  # Purple
        5: (255, 150, 0),  # Orange
        6: (10, 200, 40),  # Green
        7: (150, 150, 150),  # Gray
        8: (10, 10, 10),  # Black
        9: (180, 180, 10)  # Gold
    }

    def __init__(self, radius: float, number: int, position: Tuple[float, float]):
        self.radius = radius
        self.number = number
        self.position = position
        self.color = GameBall.ball_colors[number if number <= 9 else number - 8]
        self.striped = number >= 9

    def draw(self, screen: pygame.Surface, scale=300):
        pygame.draw.circle(screen, self.color,
                           (self.position[0] * scale, self.position[1] * scale),
                           self.radius * scale)
        if self.striped:
            pygame.draw.circle(screen, (255, 255, 255),
                               (self.position[0] * scale, self.position[1] * scale),
                               0.01 * scale)
