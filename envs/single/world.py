from ast import List
from typing import Tuple
import pygame
from objects import (
    Corridor,
    CorridorOrientation,
    CorridorPosition,
    Goal,
    Room,
    Wall,
)
from players import NPC, Agent


class World:
    def __init__(self):
        self.agent: Agent = None
        self.npc: NPC = None
        self.goal: Goal = None

        self.players: pygame.sprite.Group = None
        self.maps: pygame.sprite.Group = None
        self.walls: List[Wall] = None

    def step(self):
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError

    def get_obstacle_lines(self) -> List:
        """
        レーザーとの交点を計算するために、すべての障害物の線分を取得する
        """
        lines = []
        for wall in self.walls:
            lines.append((wall.start, wall.end))
        lines.append((self.npc.rect.topleft, self.npc.rect.topright))
        lines.append((self.npc.rect.topleft, self.npc.rect.bottomleft))
        lines.append((self.npc.rect.topright, self.npc.rect.bottomright))
        lines.append((self.npc.rect.bottomleft, self.npc.rect.bottomright))
        return lines

    def draw(self, screen: pygame.Surface):
        raise NotImplementedError


class SimpleWorld(World):
    WIDTH = 600
    HEIGHT = 600

    AGENT_SIZE = 60
    ROOM_SIZE = 260
    GOAL_SIZE = 50
    CORRIDOR_WIDTH = AGENT_SIZE + 40
    WALL_WIDTH = 2
    WALL_OUTER_LENGTH = HEIGHT - ROOM_SIZE - (ROOM_SIZE - CORRIDOR_WIDTH) // 2
    WALL_INNER_LENGTH = WALL_OUTER_LENGTH - CORRIDOR_WIDTH
    ROOM_WALL_LENGTH = (ROOM_SIZE - CORRIDOR_WIDTH) // 2

    ROOM_COLOR = (45, 50, 56)
    CORRIDOR_COLOR = (80, 85, 90)
    WALL_COLOR = (60, 67, 75)
    GOAL_BLUE = (60, 150, 150)
    AGENT_BLUE = (70, 180, 180)
    AGENT_GREEN = (111, 200, 96)
    LASER_COLOR = (100, 105, 115)
    LASER_POINT_COLOR = (200, 60, 60)

    AGENT_POS = (ROOM_SIZE // 2, HEIGHT - ROOM_SIZE // 2)
    NPC_POS = (WIDTH - ROOM_SIZE // 2, ROOM_SIZE // 2)

    ACC = 1.7
    FRIC = -0.12
    MAX_SPEED = 6
    NPC_VEL = 6

    LIDAR_ANGLE = 360
    LIDAR_INTERVAL = 5
    LIDAR_RANGE = 1200

    room1 = Room(ROOM_SIZE // 2, HEIGHT - ROOM_SIZE // 2, ROOM_SIZE, ROOM_COLOR)
    room2 = Room(WIDTH - ROOM_SIZE // 2, ROOM_SIZE // 2, ROOM_SIZE, ROOM_COLOR)
    goal = Goal(room2.rect.centerx, room2.rect.centery, GOAL_SIZE, GOAL_BLUE)
    maps = pygame.sprite.Group(
        room1,
        room2,
        Corridor(
            room1.rect.center,
            room2.rect.center,
            CorridorOrientation.HORIZONTAL,
            CorridorPosition.TOPLEFT,
            CORRIDOR_WIDTH,
            ROOM_SIZE,
            CORRIDOR_COLOR,
        ),
        Corridor(
            room2.rect.center,
            room1.rect.center,
            CorridorOrientation.VERTICAL,
            CorridorPosition.TOPLEFT,
            CORRIDOR_WIDTH,
            ROOM_SIZE,
            CORRIDOR_COLOR,
        ),
        Corridor(
            room1.rect.center,
            room2.rect.center,
            CorridorOrientation.HORIZONTAL,
            CorridorPosition.BOTTOMRIGHT,
            CORRIDOR_WIDTH,
            ROOM_SIZE,
            CORRIDOR_COLOR,
        ),
        Corridor(
            room2.rect.center,
            room1.rect.center,
            CorridorOrientation.VERTICAL,
            CorridorPosition.BOTTOMRIGHT,
            CORRIDOR_WIDTH,
            ROOM_SIZE,
            CORRIDOR_COLOR,
        ),
        goal,
    )

    walls = pygame.sprite.Group(
        Wall(
            (
                (ROOM_SIZE - CORRIDOR_WIDTH) // 2,
                (ROOM_SIZE - CORRIDOR_WIDTH) // 2,
            ),
            WALL_OUTER_LENGTH,
            CorridorOrientation.VERTICAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (
                (ROOM_SIZE - CORRIDOR_WIDTH) // 2,
                (ROOM_SIZE - CORRIDOR_WIDTH) // 2,
            ),
            WALL_OUTER_LENGTH,
            CorridorOrientation.HORIZONTAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (
                ROOM_SIZE - (ROOM_SIZE - CORRIDOR_WIDTH) // 2,
                ROOM_SIZE - (ROOM_SIZE - CORRIDOR_WIDTH) // 2,
            ),
            WALL_INNER_LENGTH,
            CorridorOrientation.VERTICAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (
                ROOM_SIZE - (ROOM_SIZE - CORRIDOR_WIDTH) // 2,
                ROOM_SIZE - (ROOM_SIZE - CORRIDOR_WIDTH) // 2,
            ),
            WALL_INNER_LENGTH,
            CorridorOrientation.HORIZONTAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (
                WIDTH - (ROOM_SIZE - CORRIDOR_WIDTH) // 2,
                ROOM_SIZE,
            ),
            WALL_OUTER_LENGTH,
            CorridorOrientation.VERTICAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (
                WIDTH - ROOM_SIZE + (ROOM_SIZE - CORRIDOR_WIDTH) // 2,
                ROOM_SIZE,
            ),
            WALL_INNER_LENGTH,
            CorridorOrientation.VERTICAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (
                ROOM_SIZE,
                HEIGHT - (ROOM_SIZE - CORRIDOR_WIDTH) // 2,
            ),
            WALL_OUTER_LENGTH,
            CorridorOrientation.HORIZONTAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (
                ROOM_SIZE,
                HEIGHT - ROOM_SIZE + (ROOM_SIZE - CORRIDOR_WIDTH) // 2,
            ),
            WALL_INNER_LENGTH,
            CorridorOrientation.HORIZONTAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (0, HEIGHT - ROOM_SIZE),
            ROOM_SIZE,
            CorridorOrientation.VERTICAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (0, HEIGHT),
            ROOM_SIZE,
            CorridorOrientation.HORIZONTAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (WIDTH, 0),
            ROOM_SIZE,
            CorridorOrientation.VERTICAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (WIDTH - ROOM_SIZE, 0),
            ROOM_SIZE,
            CorridorOrientation.HORIZONTAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (0, HEIGHT - ROOM_SIZE),
            ROOM_WALL_LENGTH,
            CorridorOrientation.HORIZONTAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (ROOM_SIZE - ROOM_WALL_LENGTH, HEIGHT - ROOM_SIZE),
            ROOM_WALL_LENGTH,
            CorridorOrientation.HORIZONTAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (ROOM_SIZE, HEIGHT - ROOM_SIZE),
            ROOM_WALL_LENGTH,
            CorridorOrientation.VERTICAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (ROOM_SIZE, HEIGHT - ROOM_WALL_LENGTH),
            ROOM_WALL_LENGTH,
            CorridorOrientation.VERTICAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (WIDTH - ROOM_SIZE, 0),
            ROOM_WALL_LENGTH,
            CorridorOrientation.VERTICAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (WIDTH - ROOM_SIZE, ROOM_SIZE - ROOM_WALL_LENGTH),
            ROOM_WALL_LENGTH,
            CorridorOrientation.VERTICAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (WIDTH - ROOM_SIZE, ROOM_SIZE),
            ROOM_WALL_LENGTH,
            CorridorOrientation.HORIZONTAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
        Wall(
            (WIDTH - ROOM_WALL_LENGTH, ROOM_SIZE),
            ROOM_WALL_LENGTH,
            CorridorOrientation.HORIZONTAL,
            WALL_WIDTH,
            WALL_COLOR,
        ),
    )

    def __init__(self):
        self.agent = Agent(
            self.AGENT_BLUE,
            self.AGENT_SIZE,
            self.ACC,
            self.FRIC,
            self.MAX_SPEED,
            self.LIDAR_RANGE,
            self.LIDAR_ANGLE,
            self.LIDAR_INTERVAL,
        )
        self.npc = NPC(self.AGENT_GREEN, self.AGENT_SIZE, self.NPC_VEL)
        self.players = pygame.sprite.Group(self.agent, self.npc)

    def reset(self):
        self.agent.reset(self.AGENT_POS)
        self.npc.reset(self.NPC_POS)

    def step(self, action):
        self.agent.move(action)
        self.npc.auto_move(
            self.ROOM_SIZE // 2,
            self.HEIGHT - self.ROOM_SIZE // 2,
            self.HEIGHT - self.ROOM_SIZE // 2,
            self.ROOM_SIZE // 2,
        )

    def draw(self, screen):
        self.maps.draw(screen)
        self.walls.draw(screen)
        self.__draw_lasers(screen)
        self.players.draw(screen)

    def __draw_lasers(self, screen):
        lasers = self.agent.create_lasers()
        obstacle_lines = self.get_obstacle_lines()
        for laser in lasers:
            intersection = self.agent.laser_scan(laser, obstacle_lines)
            pygame.draw.line(screen, self.LASER_COLOR, self.agent.pos, intersection)
            pygame.draw.circle(screen, self.LASER_POINT_COLOR, intersection, 2.5)

    def check_collision(self):
        return pygame.sprite.spritecollideany(
            self.agent, self.walls
        ) or pygame.sprite.collide_rect(self.agent, self.npc)
