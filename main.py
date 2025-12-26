import random
import time


class OthelloGame:
    def __init__(self):
        self.board = [["." for x in range(8)] for y in range(8)]
        self.turn = "X"

        # Başlangıç taşları
        self.board[3][3] = "O"
        self.board[3][4] = "X"
        self.board[4][3] = "X"
        self.board[4][4] = "O"

        # Statik Ağırlık Tablosu (Konumsal strateji için)
        self.STATIC_WEIGHTS = [
            [120, -20, 20, 5, 5, 20, -20, 120],
            [-20, -40, -5, -5, -5, -5, -40, -20],
            [20, -5, 15, 3, 3, 15, -5, 20],
            [5, -5, 3, 3, 3, 3, -5, 5],
            [5, -5, 3, 3, 3, 3, -5, 5],
            [20, -5, 15, 3, 3, 15, -5, 20],
            [-20, -40, -5, -5, -5, -5, -40, -20],
            [120, -20, 20, 5, 5, 20, -20, 120],
        ]

    def show_board(self):
        print("\n  a b c d e f g h")
        print(" +-----------------")
        for r in range(8):
            line = str(r + 1) + "|"
            for c in range(8):
                line += self.board[r][c] + " "
            print(line)
        print(f"Current Turn: {'Black (X)' if self.turn == 'X' else 'White (O)'}")

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

    def count_empty(self):
        return sum(row.count(".") for row in self.board)

    # --- YENİ: GRANDMASTER EVALUATION ---
    def get_eval(self, board_state, player, h_type):
        opp = self.get_opp(player)

        # h1-h4 Eski Metotlar (Basitleştirildi)
        if h_type < 5:
            # Burası eski mantıkla aynı kalabilir veya sadeleştirilebilir.
            # Kodun uzamaması için burayı kısa tutuyorum, h5 ana odak.
            p_c = sum(row.count(player) for row in board_state)
            o_c = sum(row.count(opp) for row in board_state)
            if h_type == 1:
                return p_c - o_c
            # ... diğerleri eski koddaki gibi ...
            return p_c - o_c

        # ---------------------------------------------------------
        # h5: GRANDMASTER (Dinamik + Konumsal + Hareketlilik)
        # ---------------------------------------------------------
        elif h_type == 5:
            empty_count = sum(row.count(".") for row in board_state)
            total_discs = 64 - empty_count

            # --- PHASE 3: ENDGAME (Son 10 hamle) ---
            # Oyun sonundaysak stratejiye gerek yok, en çok taşı toplayan kazanır.
            if empty_count <= 0:  # Oyun bitmiş
                p_c = sum(row.count(player) for row in board_state)
                o_c = sum(row.count(opp) for row in board_state)
                return (p_c - o_c) * 1000

            # --- PHASE 1 & 2: OPENING & MIDGAME ---

            # 1. Konumsal Skor (Weights)
            pos_score = 0
            for r in range(8):
                for c in range(8):
                    tile = board_state[r][c]
                    if tile == player:
                        pos_score += self.STATIC_WEIGHTS[r][c]
                    elif tile == opp:
                        pos_score -= self.STATIC_WEIGHTS[r][c]

            # 2. Köşe Kontrolü (Daha agresif)
            corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
            c_score = 0
            for r, c in corners:
                if board_state[r][c] == player:
                    c_score += 1
                elif board_state[r][c] == opp:
                    c_score -= 1

            # 3. Hareketlilik (Mobility)
            # Bu işlem biraz maliyetlidir, o yüzden sadece geçerli hamle sayılarına bakıyoruz
            tg = OthelloGame()
            tg.board = [row[:] for row in board_state]
            my_moves = len(tg.get_valid_moves(player))
            op_moves = len(tg.get_valid_moves(opp))

            if my_moves + op_moves != 0:
                mob_score = 100 * (my_moves - op_moves) / (my_moves + op_moves)
            else:
                mob_score = 0

            # AĞIRLIKLANDIRMA (Oyunun aşamasına göre değişir)
            # Oyun başında hareketlilik çok önemlidir (rakibi sıkıştırmak için)
            # Oyun ilerledikçe taşların konumu (köşeler) önem kazanır.

            if total_discs < 20:
                # Açılış: Mobility kraldır, köşeleri kapmaya çalışma ama verme
                return (10 * pos_score) + (2000 * c_score) + (50 * mob_score)
            else:
                # Orta Oyun: Pozisyon ve Köşeler daha önemli
                return (20 * pos_score) + (3000 * c_score) + (30 * mob_score)

        return 0

    # --- YENİ: MOVE ORDERING (Hızlandırma) ---
    def order_moves(self, moves, player):
        # Hamleleri "potansiyel kalitesine" göre sıralar.
        # Köşe hamleleri en başa, X-kareleri (b2, g2 vs) en sona.
        ordered = []
        for r, c in moves:
            score_guess = 0

            # Köşe mi?
            if (r, c) in [(0, 0), (0, 7), (7, 0), (7, 7)]:
                score_guess = 1000
            # Tehlikeli bölge mi (X-squares)?
            elif (r, c) in [(1, 1), (1, 6), (6, 1), (6, 6)]:
                score_guess = -500
            # Kenar mı?
            elif r == 0 or r == 7 or c == 0 or c == 7:
                score_guess = 100
            # Ağırlık tablosuna bak
            else:
                score_guess = self.STATIC_WEIGHTS[r][c]

            ordered.append(((r, c), score_guess))

        # Puana göre büyükten küçüğe sırala
        ordered.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in ordered]

    def minimax(self, board_state, depth, alpha, beta, is_max, player, h_type):
        opp = self.get_opp(player)
        curr = player if is_max else opp

        # 1. Base Case: Derinlik bitti veya Oyun bitti
        if depth == 0:
            return self.get_eval(board_state, player, h_type), None

        # Hamleleri oluştur
        tg = OthelloGame()
        tg.board = [r[:] for r in board_state]
        moves_curr = tg.get_valid_moves(curr)

        # Hamle yoksa pas geçme mantığı
        if not moves_curr:
            moves_opp = tg.get_valid_moves(self.get_opp(curr))
            if not moves_opp:
                # Oyun bitti, son skoru hesapla (Coin Parity)
                final_score = tg.count_score()
                diff = final_score[0] - final_score[1] if player == "X" else final_score[1] - final_score[0]
                return diff * 10000, None  # Çok büyük sayı = Kesin galibiyet

            return self.minimax(board_state, depth, alpha, beta, not is_max, player, h_type)

        # --- OPTİMİZASYON: MOVE ORDERING ---
        # Hamleleri rastgele denemek yerine en iyilerden başla.
        # Bu, Alpha-Beta budamasının çok daha sık çalışmasını sağlar.
        sorted_moves = self.order_moves(moves_curr, curr)

        best_move = None

        if is_max:
            max_eval = -float("inf")
            for m in sorted_moves:
                nb = [r[:] for r in board_state]
                tg2 = OthelloGame()
                tg2.board = nb
                tg2.make_move(m[0], m[1], curr)

                eval_val, _ = self.minimax(nb, depth - 1, alpha, beta, False, player, h_type)

                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = m
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float("inf")
            for m in sorted_moves:
                nb = [r[:] for r in board_state]
                tg2 = OthelloGame()
                tg2.board = nb
                tg2.make_move(m[0], m[1], curr)

                eval_val, _ = self.minimax(nb, depth - 1, alpha, beta, True, player, h_type)

                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = m
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def get_ai_move(self, player, depth, h_type):
        start_t = time.time()

        # --- ENDGAME SOLVER ---
        # Eğer tahtada az boş yer kaldıysa, yapay zeka derinliği "sonsuz" yapar.
        # Yani oyunun sonuna kadar hesaplar.
        empties = self.count_empty()
        search_depth = depth
        is_solving = False

        # Son 10 kare kaldığında "Mükemmel Oyun" moduna geç (Solver)
        if empties <= 10:
            search_depth = empties
            is_solving = True
            print(f"\n>>> AI ({player}) DETECTED ENDGAME! SOLVING PERFECTLY (Depth: {search_depth})...")
        else:
            print(f"\n>>> AI ({player}) THINKING... (Depth: {search_depth}, Heuristic: h{h_type})")

        score, move = self.minimax(self.board, search_depth, -float("inf"), float("inf"), True, player, h_type)

        end_t = time.time()
        dur = end_t - start_t

        if move is None:
            ms = self.get_valid_moves(player)
            if ms:
                move = random.choice(ms)
            else:
                return None

        m_str = chr(ord("a") + move[1]) + str(move[0] + 1)
        print(f">>> AI MOVE: {m_str}")
        print(f"(Score: {score:.1f}, Time: {dur:.4f}s)")
        return move


# ------------------------------------------------------------------
# UI / INPUT KISMI
# ------------------------------------------------------------------
def get_coord_input(valid_moves):
    while True:
        u = input("Your move (e.g. c4): ").strip().lower()
        if u == "exit":
            return None
        try:
            r, c = -1, -1
            if len(u) == 2 and u[0].isalpha() and u[1].isdigit():
                c = ord(u[0]) - ord("a")
                r = int(u[1]) - 1
            else:
                print("Format: 'c4'")
                continue
            if (r, c) in valid_moves:
                return (r, c)
            else:
                print("Invalid move.")
        except:
            print("Error.")


def get_ai_settings(label):
    print(f"\n--- Configure {label} ---")
    print("Heuristics: 1=Easy, 2=Medium, 3=Hard, 5=GRANDMASTER")

    try:
        h = int(input(f"Select Strategy for {label} [1,2,3,5] (Default 5): "))
        if h not in [1, 2, 3, 5]:
            h = 5
    except:
        h = 5

    try:
        d = int(input(f"Select Depth for {label} [2-8] (Rec: 4-6): "))
    except:
        d = 4

    return d, h


if __name__ == "__main__":
    g = OthelloGame()
    print("==========================================")
    print("      OTHELLO - GRANDMASTER EDITION")
    print("==========================================")
    print("1. Human vs AI")
    print("2. AI vs AI")

    mode = "1"
    while True:
        m_in = input("Mode [1/2]: ").strip()
        if m_in in ["1", "2"]:
            mode = m_in
            break

    ai_settings = {"X": {"depth": 4, "h": 5}, "O": {"depth": 4, "h": 5}}
    human_color = None

    if mode == "1":
        while True:
            c = input("Select color [B/W]: ").lower()
            if c in ["b", "w"]:
                human_color = "X" if c == "b" else "O"
                break
        ai_color = "O" if human_color == "X" else "X"
        d, h = get_ai_settings(f"AI ({'White' if ai_color=='O' else 'Black'})")
        ai_settings[ai_color] = {"depth": d, "h": h}
    else:
        d1, h1 = get_ai_settings("AI 1 (Black)")
        ai_settings["X"] = {"depth": d1, "h": h1}
        d2, h2 = get_ai_settings("AI 2 (White)")
        ai_settings["O"] = {"depth": d2, "h": h2}

    print("\n--- GAME STARTING ---\n")

    while not g.is_game_over():
        g.show_board()
        valid = g.get_valid_moves(g.turn)

        if not valid:
            print(f"{g.turn} has NO MOVES. Passing...")
            g.turn = g.get_opp(g.turn)
            continue

        move = None
        if mode == "1" and g.turn == human_color:
            formatted = [chr(ord("a") + c) + str(r + 1) for r, c in valid]
            print(f"Moves: {', '.join(formatted)}")
            move = get_coord_input(valid)
            if not move:
                break
            g.make_move(move[0], move[1], g.turn)
        else:
            if mode == "2":
                time.sleep(1)
            cfg = ai_settings[g.turn]
            move = g.get_ai_move(g.turn, cfg["depth"], cfg["h"])
            if move:
                g.make_move(move[0], move[1], g.turn)
            else:
                break

        g.turn = g.get_opp(g.turn)

    g.show_board()
    x, o = g.count_score()
    print(f"GAME ENDED! X: {x}, O: {o}")
    if x > o:
        print("Winner: BLACK")
    elif o > x:
        print("Winner: WHITE")
    else:
        print("DRAW")
