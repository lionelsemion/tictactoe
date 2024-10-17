from __future__ import annotations
from math import atan, pi, tau
from PIL import Image, ImageDraw, ImageEnhance
from board import Board
from explorer import GameState, generate_game_tree, PlayerSymbol
from random import random
import cv2
import numpy as np


class Vec3:
    x: int
    y: int
    z: int

    def __init__(self, x, y, z) -> None:
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return self + -other

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def __mul__(self, other):
        return Vec3(other * self.x, other * self.y, other * self.z)

    __rmul__ = __mul__

    def __truediv__(self, other):
        return Vec3(self.x / other, self.y / other, self.z / other)

    def abs_squared(self):
        return self.x * self.x + self.y * self.y + self.z * self.z

    def abs(self):
        return self.abs_squared() ** 0.5

    def xy(self):
        return self.x, self.y

    def normal(self):
        return self / abs(self)

    __abs__ = abs

    def __repr__(self) -> str:
        return f"|{self.x} {self.y} {self.z}|"


class VisualBoard:
    image: Image.Image
    state: GameState
    pos: Vec3
    vel: Vec3

    @property
    def x(self):
        return self.pos.x

    @property
    def y(self):
        return self.pos.y

    @property
    def z(self):
        return self.pos.z

    def __init__(self, state: GameState) -> None:
        self.state = state
        self.image = self.board_image()
        self.pos = Vec3(random() - 0.5, random() - 0.5, random() - 0.5)
        self.vel = Vec3(random() - 0.5, random() - 0.5, random() - 0.5)

    def player_symbol2color(self, player: PlayerSymbol):
        return (
            (0, 0, 255)
            if player == 1
            else (255, 0, 0) if player == -1 else (64, 64, 64)
        )

    def board_image(self, size=24, padding=1):
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        color = self.player_symbol2color(self.state.lead)
        draw.line((size / 3, 0, size / 3, size), fill=color)
        draw.line((size / 3 * 2, 0, size / 3 * 2, size), fill=color)
        draw.line((0, size / 3, size, size / 3), fill=color)
        draw.line((0, size / 3 * 2, size, size / 3 * 2), fill=color)

        third_size = size // 3

        for x, y, cell in self.state.board.iterate():
            match cell:
                case -1:
                    x *= third_size
                    y *= third_size
                    draw.ellipse(
                        (
                            x + padding,
                            y + padding,
                            x + third_size - padding,
                            y + third_size - padding,
                        ),
                        outline=self.player_symbol2color(cell),
                    )
                    continue
                case 1:
                    x *= third_size
                    y *= third_size
                    draw.line(
                        (
                            x + padding,
                            y + padding,
                            x + third_size - padding,
                            y + third_size - padding,
                        ),
                        fill=self.player_symbol2color(cell),
                    )
                    draw.line(
                        (
                            x + third_size - padding,
                            y + padding,
                            x + padding,
                            y + third_size - padding,
                        ),
                        fill=self.player_symbol2color(cell),
                    )
                    continue
        return image

    def update_position(self, other_boards: list[VisualBoard]):
        for other_board in other_boards:
            if other_board != self:
                self.vel += (
                    10
                    * (self.pos - other_board.pos).normal()
                    / max(20, (self.pos - other_board.pos).abs2())
                )

                if (
                    self.state.idx
                    in other_board.state.next_idx + other_board.state.before_idx
                ):
                    self.vel += (
                        -0.0001
                        * (self.pos - other_board.pos).normal()
                        * ((self.pos - other_board.pos).abs() - 30)
                    )

                self.pos += self.vel
                self.vel *= 0.99


class VisualGameTree:
    boards: list[VisualBoard]
    boards_on_stock: list[VisualBoard]
    image: Image.Image

    def __init__(
        self,
        start_board: Board | None = None,
        start_player: PlayerSymbol = PlayerSymbol(1),
    ) -> None:
        game_tree = generate_game_tree(
            start_board=start_board, start_player=start_player
        )
        self.boards_on_stock = [VisualBoard(state) for state in game_tree]
        self.boards = [self.boards_on_stock.pop(0)]

    def draw_tree(self, shape: tuple[int, int] = (1024, 1024)) -> Image:
        def transform(x, y):
            return (
                int(x + shape[0] / 2),
                int(y + shape[1] / 2),
            )

        self.image = Image.new("RGBA", shape, (0, 0, 0, 255))
        draw = ImageDraw.Draw(self.image)
        for board in self.boards:
            for other_idx in board.state.next_idx:
                if other_idx < len(self.boards):
                    draw.line(
                        (
                            *transform(board.x, board.y),
                            *transform(
                                self.boards[other_idx].x, self.boards[other_idx].y
                            ),
                        ),
                        fill=(64, 64, 64),
                    )
        for board in self.boards:
            img = board.image.copy()
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(atan(board.z) / pi / 1.5 + 1)

            self.image.paste(
                img,
                transform(board.x - img.width / 2, board.y - img.height / 2),
                img,
            )

    def update_positions(self):
        for board in self.boards[1:]:
            board.update_position(self.boards)

    def spawn_new(self):
        depth = self.boards[-1].state.depth + 1
        while len(self.boards_on_stock) > 0:
            if self.boards_on_stock[0].state.depth != depth:
                break
            self.boards.append(self.boards_on_stock.pop(0))
            self.boards[-1].pos += self.boards[self.boards[-1].state.before_idx[0]].pos


tree = VisualGameTree()
while True:
    tree.update_positions()
    tree.draw_tree()
    cv2.imshow("", np.array(tree.image))
    if (k := cv2.waitKey(10)) == 27:
        break
    if k == 32:
        tree.spawn_new()
