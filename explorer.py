from board import Board, PlayerSymbol
from dataclasses import dataclass


@dataclass(slots=True, repr=False)
class GameState:
    board: Board
    next_player: PlayerSymbol
    lead: PlayerSymbol
    depth: int
    next_idx: list[int]
    before_idx: list[int]
    idx: int

    def __repr__(self) -> str:
        return f"Depth: {self.depth}\n{self.board}\nNext Player: {self.next_player}\nIndex: {self.idx}\nBefore: {self.before_idx}\nNext: {self.next_idx}"


def next_moves(board: Board, player: PlayerSymbol) -> list[Board]:
    boards: list[Board] = []
    for y_zero, row in enumerate(board):
        for x_zero, cell in enumerate(row):
            if cell == 0:
                boards.append(
                    Board(
                        tuple(
                            tuple(
                                row[:x_zero] + (player,) + row[x_zero + 1 :]
                                if y == y_zero
                                else row
                            )
                            for y, row in enumerate(board)
                        )
                    )
                )

    return boards


def detect_winner(board: Board) -> PlayerSymbol | None:
    for board in board.rotations():
        potential = board[0][0]
        if potential != 0:
            if potential == board[0][1] and potential == board[0][2]:
                return potential
            if potential == board[1][1] and potential == board[2][2]:
                return potential
        potential = board[1][0]
        if potential != 0:
            if potential == board[1][1] and potential == board[1][2]:
                return potential
    if sum([sum(1 if cell == 0 else 0 for cell in row) for row in board]) == 0:
        return PlayerSymbol(0)
    return None


def who_winns(
    lut: dict[int, int], board: Board, maximizing_player: PlayerSymbol
) -> PlayerSymbol:
    if (h := hash(board)) in lut:
        return lut[h]

    if (winner := detect_winner(board)) is not None:
        return winner

    boards = next_moves(board, maximizing_player)

    if maximizing_player == PlayerSymbol(1):
        value = -1
        for board in boards:
            value = max(value, who_winns(lut, board, -maximizing_player))
    else:
        value = 1
        for board in boards:
            value = min(value, who_winns(lut, board, -maximizing_player))

    value = PlayerSymbol(value)
    lut[h] = value
    return value


def generate_game_tree(
    max_depth=None,
    start_board=None,
    start_player=PlayerSymbol(1),
):
    start_board = Board() if start_board is None else start_board

    lut_winner = dict()
    lut_explored = dict()
    game_tree: list[GameState] = [
        GameState(
            start_board,
            start_player,
            who_winns(lut_winner, start_board, start_player),
            0,
            [],
            [],
            0,
        )
    ]

    def explore(state_idx, state: GameState):
        if max_depth is not None and state.depth >= max_depth:
            return

        if detect_winner(state.board) is not None:
            return

        for board in next_moves(state.board, state.next_player):
            if (h := hash(board)) in lut_explored:
                if lut_explored[h] not in state.next_idx:
                    state.next_idx.append(lut_explored[h])
                continue

            game_tree.append(
                GameState(
                    board,
                    -state.next_player,
                    who_winns(lut_winner, board, -state.next_player),
                    state.depth + 1,
                    [],
                    [],
                    len(game_tree),
                )
            )
            state.next_idx.append(l := (len(game_tree) - 1))
            game_tree[-1].before_idx.append(state_idx)
            lut_explored[h] = l

    k = 0
    while 1:
        if k >= len(game_tree):
            break
        explore(k, game_tree[k])
        k += 1

    return game_tree


if __name__ == "__main__":
    game_tree = generate_game_tree()
    print(*(f"{state}" for state in game_tree), sep="\n\n")
