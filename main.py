import copy
import random
import time

class OthelloGame:
    def __init__(self):
        self.board = [["." for x in range(8)] for y in range(8)]
        self.turn = "X"
        self.ply_depth = 4
        self.heuristic_type = 1

        self.board[3][3] = "O"
        self.board[3][4] = "X"
        self.board[4][3] = "X"
        self.board[4][4] = "O"

    def show_board(self):
        print("  a b c d e f g h")
        for r in range(8):
            line = str(r + 1) + " "
            for c in range(8):
                line += self.board[r][c] + " "
            print(line)
        print("Current Turn: " + self.turn)

    def is_inside(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_opp(self, player):
        return "O" if player == "X" else "X"

    def check_move(self, r, c, player):
        if self.board[r][c] != ".":
            return []

        opp = self.get_opp(player)
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        to_flip = []

        for dr, dc in dirs:
            temp_flip = []
            cr, cc = r + dr, c + dc
            while self.is_inside(cr, cc) and self.board[cr][cc] == opp:
                temp_flip.append((cr, cc))
                cr += dr
                cc += dc
            if self.is_inside(cr, cc) and self.board[cr][cc] == player and temp_flip:
                to_flip.extend(temp_flip)

        return to_flip

    def get_valid_moves(self, player):
        moves = []
        for r in range(8):
            for c in range(8):
                if len(self.check_move(r, c, player)) > 0:
                    moves.append((r, c))
        return moves

    def make_move(self, r, c, player):
        flips = self.check_move(r, c, player)
        if len(flips) == 0:
            return False
        self.board[r][c] = player
        for fr, fc in flips:
            self.board[fr][fc] = player
        return True

    def is_game_over(self):
        p1 = self.get_valid_moves("X")
        p2 = self.get_valid_moves("O")
        return len(p1) == 0 and len(p2) == 0

    def count_score(self):
        x_cnt = sum(row.count("X") for row in self.board)
        o_cnt = sum(row.count("O") for row in self.board)
        return x_cnt, o_cnt

    def get_eval(self, board_state, player, h_type):
        opp = self.get_opp(player)

        if h_type == 1:
            p_c = sum(row.count(player) for row in board_state)
            o_c = sum(row.count(opp) for row in board_state)
            return p_c - o_c

        elif h_type == 2:
            weights = [
                [100, -20, 10, 5, 5, 10, -20, 100],
                [-20, -50, -2, -2, -2, -2, -50, -20],
                [10, -2, -1, -1, -1, -1, -2, 10],
                [5, -2, -1, -1, -1, -1, -2, 5],
                [5, -2, -1, -1, -1, -1, -2, 5],
                [10, -2, -1, -1, -1, -1, -2, 10],
                [-20, -50, -2, -2, -2, -2, -50, -20],
                [100, -20, 10, 5, 5, 10, -20, 100],
            ]
            score = 0
            for r in range(8):
                for c in range(8):
                    if board_state[r][c] == player:
                        score += weights[r][c]
                    elif board_state[r][c] == opp:
                        score -= weights[r][c]
            return score

        elif h_type == 3:
            tg = OthelloGame()
            tg.board = [row[:] for row in board_state]
            my_m = len(tg.get_valid_moves(player))
            op_m = len(tg.get_valid_moves(opp))
            return my_m - op_m

        return 0

    def minimax(self, board_state, depth, alpha, beta, is_max, player):
        opp = self.get_opp(player)
        curr = player if is_max else opp

        if depth == 0:
            return self.get_eval(board_state, player, self.heuristic_type), None

        tg = OthelloGame()
        tg.board = [r[:] for r in board_state]
        moves_curr = tg.get_valid_moves(curr)

        if not moves_curr:
            moves_opp = tg.get_valid_moves(self.get_opp(curr))
            if not moves_opp:
                return self.get_eval(board_state, player, self.heuristic_type), None

            return self.minimax(board_state, depth - 1, alpha, beta, not is_max, player)

        best_move = None

        if is_max:
            max_eval = -999999999
            for m in moves_curr:
                nb = [r[:] for r in board_state]
                tg2 = OthelloGame()
                tg2.board = nb
                tg2.make_move(m[0], m[1], curr)

                eval_val, _ = self.minimax(nb, depth - 1, alpha, beta, False, player)

                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = m
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval, best_move

        else:
            min_eval = 999999999
            for m in moves_curr:
                nb = [r[:] for r in board_state]
                tg2 = OthelloGame()
                tg2.board = nb
                tg2.make_move(m[0], m[1], curr)

                eval_val, _ = self.minimax(nb, depth - 1, alpha, beta, True, player)

                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = m
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def get_ai_move(self, player):
        start_t = time.time()
        print(f"AI ({player}) thinking... (Depth: {self.ply_depth}, H: {self.heuristic_type})")

        score, move = self.minimax(self.board, self.ply_depth, -float("inf"), float("inf"), True, player)

        end_t = time.time()
        dur = end_t - start_t

        if move is None:
            ms = self.get_valid_moves(player)
            if ms:
                move = random.choice(ms)
            else:
                return None

        m_str = chr(ord("a") + move[1]) + str(move[0] + 1)
        print(
            f"AI Move: {m_str}, Heuristic: {self.heuristic_type}, "
            f"Depth: {self.ply_depth}, Score: {score}, Time: {dur:.4f} sec"
        )

        return move

if __name__ == "__main__":
    g = OthelloGame()
    print("Othello Project - CSE4082")
    print("1: Human vs Human")
    print("2: Human vs AI")
    print("3: AI vs AI")

    m = input("Choose mode: ")

    p1_h = 1
    p2_h = 1
    depth = 4
    p1_depth = 4
    p2_depth = 4

    if m in ["2", "3"]:
        try:
            if m == "2":
                depth = int(input("Enter AI depth (ply): "))
                g.ply_depth = depth
                g.heuristic_type = int(input("Heuristic for AI (1,2,3): "))
            else:
                print("Config for AI 1 (Black / X):")
                p1_depth = int(input("Depth for AI 1 (Black): "))
                p1_h = int(input("Heuristic for AI 1 (1,2,3): "))

                print("Config for AI 2 (White / O):")
                p2_depth = int(input("Depth for AI 2 (White): "))
                p2_h = int(input("Heuristic for AI 2 (1,2,3): "))

        except Exception as e:
            print("input error, using defaults")
            print("Error detail:", e)

    while not g.is_game_over():
        g.show_board()
        valid = g.get_valid_moves(g.turn)

        if not valid:
            print(f"{g.turn} has no moves, skipping.")
            g.turn = g.get_opp(g.turn)
            continue

        move = None
        is_human = False

        if m == "1":
            is_human = True
        elif m == "2":
            is_human = g.turn == "X"
        elif m == "3":
            is_human = False

        if is_human:
            formatted_moves = []
            for r, c in valid:
                m_str = chr(ord("a") + c) + str(r + 1)
                formatted_moves.append(m_str)

            print(f"Valid moves: {', '.join(formatted_moves)}")

            u = input(f"Player {g.turn} move (ex: c4): ")

            try:
                r, c = -1, -1

                if len(u) == 2 and u[0].isalpha() and u[1].isdigit():
                    c = ord(u[0].lower()) - ord("a")
                    r = int(u[1]) - 1
                else:
                    parts = u.split()
                    r, c = int(parts[0]) - 1, int(parts[1]) - 1

                if (r, c) in valid:
                    move = (r, c)
                else:
                    print("Invalid move, try again.")
                    continue
            except:
                print("Bad format. Try 'c4' or 'row col'")
                continue
        else:
            if m == "3":
                if g.turn == "X":
                    g.heuristic_type = p1_h
                    g.ply_depth = p1_depth
                else:
                    g.heuristic_type = p2_h
                    g.ply_depth = p2_depth

            move = g.get_ai_move(g.turn)

            if move is None:
                print(f"{g.turn} (AI) has no moves, skipping.")
                g.turn = g.get_opp(g.turn)
                continue

        g.make_move(move[0], move[1], g.turn)
        g.turn = g.get_opp(g.turn)

    g.show_board()
    x, o = g.count_score()
    print(f"Game Over! X: {x}, O: {o}")
    if x > o:
        print("Black Wins")
    elif o > x:
        print("White Wins")
    else:
        print("Draw")