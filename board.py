from __future__ import annotations
from random import randint
from dataclasses import dataclass
from typing import Generator


# @dataclass(slots=True, init=False)
class PlayerSymbol(int):
    def __repr__(self) -> str:
        return "X" if self == 1 else "O" if self == -1 else "."

    def __neg__(self) -> int:
        return PlayerSymbol(super().__neg__())


@dataclass(slots=True, init=False)
class Board:
    cells: tuple[tuple[PlayerSymbol]]

    def __init__(
        self,
        cells: tuple[tuple[PlayerSymbol]] = ((PlayerSymbol(0),) * 3,) * 3,
    ) -> None:
        self.cells = cells

    def rotate(self) -> Board:
        return Board(
            (
                (self.cells[0][2], self.cells[1][2], self.cells[2][2]),
                (self.cells[0][1], self.cells[1][1], self.cells[2][1]),
                (self.cells[0][0], self.cells[1][0], self.cells[2][0]),
            )
        )

    def mirror(self) -> Board:
        return Board(
            (
                (self.cells[0][2], self.cells[0][1], self.cells[0][0]),
                (self.cells[1][2], self.cells[1][1], self.cells[1][0]),
                (self.cells[2][2], self.cells[2][1], self.cells[2][0]),
            )
        )

    def __repr__(self) -> str:
        return "\n".join(["".join([str(cell) for cell in row]) for row in self.cells])

    def rotations(self) -> list[Board]:
        boards = [self]
        for _ in range(3):
            boards.append(boards[-1].rotate())
        return boards

    def symmetries(self) -> list[Board]:
        return self.rotations() + self.mirror().rotations()

    def __hash__(self) -> int:
        symetric_hashes = [
            board.hash_ignore_symmetries() for board in self.symmetries()
        ]

        return min(symetric_hashes)

    def standard_symmetry(self) -> Board:
        min_hash = 1e10
        for board in self.symmetries():
            if (h := board.hash_ignore_symmetries()) < min_hash:
                min_board = board
                min_hash = h

        return min_board

    def hash_ignore_symmetries(self) -> int:
        cell_id = 0
        total = 0
        for row in self.cells:
            for cell in row:
                if cell != 0:
                    total += 1 << (2 * cell_id + (cell == 1))
                cell_id += 1
        return total

    def __getitem__(self, index):
        return self.cells[index]

    def iterate(self) -> Generator[int, int, PlayerSymbol]:
        for y, row in enumerate(self):
            for x, cell in enumerate(row):
                yield x, y, cell

    @classmethod
    def random(Cls):
        return Cls(
            tuple(
                tuple(PlayerSymbol(randint(-1, 1)) for _ in range(3)) for _ in range(3)
            )
        )


if __name__ == "__main__":
    board = Board.random()
    print(board)
    print(hash(board))
    board = board.standard_symmetry()
    print(board)
    print(hash(board))

    print(board[0])
    print(board[1])
    print(board[2])
