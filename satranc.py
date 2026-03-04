import chess
import chess.engine
import pygame
import sys
import os
import time
import math
import threading
import struct
import random

if sys.platform == "win32":
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- CHESS.COM COLORS ---
C_BG = (49, 46, 43)
C_LIGHT = (235, 236, 208)
C_DARK = (119, 149, 86)
C_PANEL = (38, 36, 33)
C_PANEL2 = (44, 42, 39)
C_GREEN = (129, 182, 76)
C_GREEN_HOVER = (148, 200, 95)
C_WHITE = (255, 255, 255)
C_GRAY = (160, 160, 160)
C_RED = (231, 76, 60)
C_LAST_FROM = (186, 202, 68, 160)
C_LAST_TO = (246, 246, 105, 160)
C_SELECTED = (255, 255, 100, 120)
C_ARROW_USER = (80, 200, 80, 180)
C_ARROW_HINT = (255, 170, 0, 200)
C_EVAL_WHITE = (240, 240, 240)
C_EVAL_BLACK = (50, 50, 50)

# --- CONSTANTS ---
WIDTH, HEIGHT = 1280, 900
BOARD_MARGIN_LEFT = 80
BOARD_MARGIN_TOP = 70
BOARD_SIZE = 720
SQ = BOARD_SIZE // 8
PANEL_X = BOARD_MARGIN_LEFT + BOARD_SIZE + 30
PANEL_W = WIDTH - PANEL_X - 20
EVAL_BAR_W = 28
EVAL_BAR_X = BOARD_MARGIN_LEFT - EVAL_BAR_W - 12
FPS = 60

TIME_PRESETS = [
    ("1+0", 60, 0), ("1+1", 60, 1), ("2+1", 120, 1),
    ("3+0", 180, 0), ("3+2", 180, 2), ("5+0", 300, 0),
    ("5+3", 300, 3), ("10+0", 600, 0), ("15+10", 900, 10),
    ("30+0", 1800, 0)
]
DIFF_LABELS = ["Kolay", "Orta", "Zor", "Usta", "Nakamura"]
DIFF_VALUES = [1, 5, 10, 15, 20]
PIECE_VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

from moduller.bulmacalar import get_all_puzzles, get_random_puzzle

# Captured piece display using small piece images instead of unicode
PIECE_ORDER = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]
PIECE_SYM_MAP = {chess.PAWN: 'P', chess.KNIGHT: 'N', chess.BISHOP: 'B', chess.ROOK: 'R', chess.QUEEN: 'Q'}


def gen_wood_sound(sound_type='move'):
    sr = 22050
    dur_ms = 120 if sound_type == 'check' else 90
    n = int(sr * dur_ms / 1000.0)
    buf = bytearray()
    
    for i in range(n):
        t = i / sr
        
        v = 0
        if sound_type == 'move':
            noise_env = math.exp(-t * 250)
            body_env = math.exp(-t * 50)
            noise = random.uniform(-1, 1) * 0.4 * noise_env
            body = (math.sin(2 * math.pi * 320 * t) * 0.4 + math.sin(2 * math.pi * 600 * t) * 0.2) * body_env
            v = noise + body
            
        elif sound_type == 'capture':
            noise_env = math.exp(-t * 120)
            body_env = math.exp(-t * 45)
            noise = random.uniform(-1, 1) * 0.6 * noise_env
            body = (math.sin(2 * math.pi * 280 * t) * 0.5 + math.sin(2 * math.pi * 500 * t) * 0.3) * body_env
            v = noise + body
            
        elif sound_type == 'check':
            noise_env = math.exp(-t * 180)
            body_env = math.exp(-t * 30)
            noise = random.uniform(-1, 1) * 0.2 * noise_env
            body = (math.sin(2 * math.pi * 400 * t) * 0.5 + math.sin(2 * math.pi * 800 * t) * 0.2) * body_env
            v = noise + body
            
        elif sound_type == 'castle':
            noise_env = math.exp(-t * 200)
            body_env = math.exp(-t * 60)
            noise = random.uniform(-1, 1) * 0.3 * noise_env
            body = (math.sin(2 * math.pi * 300 * t) * 0.5) * body_env
            v = noise + body
            
        elif sound_type == 'end':
            body_env = math.exp(-t * 20)
            v = math.sin(2 * math.pi * 220 * t) * 0.5 * body_env
            
        sample = int(v * 32767 * 0.9)
        buf.extend(struct.pack('<h', max(-32768, min(32767, sample))))
        
    return pygame.mixer.Sound(buffer=bytes(buf))


def create_icon_surface():
    """Create a chess knight icon for the window."""
    s = pygame.Surface((32, 32), pygame.SRCALPHA)
    # Green rounded square background
    pygame.draw.rect(s, C_GREEN, (0, 0, 32, 32), border_radius=6)
    # Simple knight silhouette - draw with shapes
    # Head
    pygame.draw.ellipse(s, C_WHITE, (8, 4, 16, 14))
    # Neck
    pygame.draw.rect(s, C_WHITE, (10, 14, 12, 10))
    # Base
    pygame.draw.rect(s, C_WHITE, (6, 22, 20, 6), border_radius=2)
    # Eye
    pygame.draw.circle(s, C_GREEN, (18, 10), 2)
    # Ear notch
    pygame.draw.polygon(s, C_GREEN, [(10, 4), (14, 4), (12, 8)])
    return s


class ChessApp:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(22050, -16, 1, 512)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("GrandMaster Chess")
        self.clock = pygame.time.Clock()

        # Add variables for right-click highlights and initial fen
        self.right_clicked_sqs = set()
        self.start_fen = chess.STARTING_FEN

        # Set window icon
        icon = create_icon_surface()
        pygame.display.set_icon(icon)

        # Fonts
        self.f_logo = pygame.font.SysFont("Segoe UI", 52, bold=True)
        self.f_title = pygame.font.SysFont("Segoe UI", 36, bold=True)
        self.f_big = pygame.font.SysFont("Segoe UI", 28, bold=True)
        self.f_ui = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.f_sm = pygame.font.SysFont("Segoe UI", 16)
        self.f_xs = pygame.font.SysFont("Segoe UI", 14)
        self.f_coord = pygame.font.SysFont("Segoe UI", 13, bold=True)
        self.f_timer = pygame.font.SysFont("Consolas", 38, bold=True)
        self.f_eval = pygame.font.SysFont("Consolas", 12, bold=True)

        # Sound loading with procedural fallback
        def load_snd(name, fallback_type):
            exts = ['.ogg', '.mp3', '.wav']
            for ext in exts:
                path = os.path.join(SCRIPT_DIR, "sesler", name + ext)
                if os.path.exists(path):
                    try:
                        return pygame.mixer.Sound(path)
                    except Exception:
                        pass
            # Specific check for Move.ogg in root if not in sesler
            root_move = os.path.join(SCRIPT_DIR, "Move.ogg")
            if name == "move" and os.path.exists(root_move):
                try:
                    return pygame.mixer.Sound(root_move)
                except Exception:
                    pass
            return gen_wood_sound(fallback_type)

        self.snd_move = load_snd("move", "move")
        self.snd_capture = load_snd("capture", "capture")
        self.snd_check = load_snd("move-check", "check")
        self.snd_castle = load_snd("castle", "castle")
        self.snd_end = load_snd("game-end", "end")
        self.snd_promote = load_snd("promote", "move")

        # State
        self.state = "MENU"
        self.board = chess.Board()
        self.images = {}
        self.mini_images = {}
        self.load_images()

        self.time_scroll = 0
        self.puz_scroll = 0
        
        # Scrollbar Dragging States
        self.dragging_scrollbar = None
        self.drag_start_y = 0
        self.drag_start_scroll = 0
        self.time_thumb_rect = None
        self.puz_thumb_rect = None

        # Settings
        self.sel_diff = 2
        self.sel_time = 3
        self.player_color = chess.WHITE
        self.flipped = False

        # Game state
        self.selected_sq = None
        self.dragging_piece = None
        self.drag_pos = (0, 0)
        self.legal_targets = []
        self.user_arrows = []
        self.arrow_start = None
        self.hint_arrow = None
        self.last_move = None
        self.white_time = 600
        self.black_time = 600
        self.increment = 0
        self.last_tick = 0
        self.animating = False
        self.anim_piece = None
        self.anim_start = None
        self.anim_end = None
        self.anim_t = 0
        self.anim_duration = 0.15
        self.anim_move = None

        # Eval
        self.eval_score = 0.0
        self.eval_thread = None

        # Promotion
        self.promoting = False
        self.promo_move = None
        self.promo_sq = None

        # Bot async
        self.bot_thinking = False
        self.bot_result = None
        self.bot_think_until = 0

        # Game Mode
        self.mode = "VS_BOT" # VS_BOT or PUZZLE
        self.puzzle_idx = 0
        self.menu_bg_offset = 0
        self.time_dd_open = False
        self.time_dd_rect = None
        self.time_items_rects = []
        self.puz_dd_open = False
        self.puz_dd_rect = None
        self.puz_items_rects = []

        # Engine
        eng_path = os.path.join(SCRIPT_DIR, "stockfish-windows-x86-64-avx2.exe")
        self._engine_lock = threading.Lock()
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(eng_path)
        except Exception:
            print("UYARI: Stockfish bulunamad\u0131!")
            self.engine = None
        self._resigned = False

    def load_images(self):
        pieces = {
            'P': 'beyaz_piyon', 'N': 'beyaz_at', 'B': 'beyaz_fil',
            'R': 'beyaz_kale', 'Q': 'beyaz_vezir', 'K': 'beyaz_sah',
            'p': 'siyah_piyon', 'n': 'siyah_at', 'b': 'siyah_fil',
            'r': 'siyah_kale', 'q': 'siyah_vezir', 'k': 'siyah_sah'
        }
        for code, name in pieces.items():
            path = os.path.join(SCRIPT_DIR, "taslar", f"{name}.png")
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.images[code] = pygame.transform.smoothscale(img, (int(SQ * 0.88), int(SQ * 0.88)))
                self.mini_images[code] = pygame.transform.smoothscale(img, (22, 22))

    def sq_to_px(self, sq):
        f, r = chess.square_file(sq), chess.square_rank(sq)
        if self.flipped:
            return BOARD_MARGIN_LEFT + (7 - f) * SQ, BOARD_MARGIN_TOP + r * SQ
        return BOARD_MARGIN_LEFT + f * SQ, BOARD_MARGIN_TOP + (7 - r) * SQ

    def px_to_sq(self, mx, my):
        c = (mx - BOARD_MARGIN_LEFT) // SQ
        r = (my - BOARD_MARGIN_TOP) // SQ
        if not (0 <= c < 8 and 0 <= r < 8):
            return None
        if self.flipped:
            return chess.square(7 - c, r)
        return chess.square(c, 7 - r)

    def get_captured(self, color):
        opp = not color
        initial = {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2, chess.ROOK: 2, chess.QUEEN: 1}
        on_board = {}
        for sq in chess.SQUARES:
            p = self.board.piece_at(sq)
            if p and p.color == opp:
                on_board[p.piece_type] = on_board.get(p.piece_type, 0) + 1
        captured = []
        for pt in PIECE_ORDER:
            diff = initial.get(pt, 0) - on_board.get(pt, 0)
            for _ in range(diff):
                captured.append(pt)
        return captured

    def material_advantage(self, color):
        cap = self.get_captured(color)
        opp_cap = self.get_captured(not color)
        return sum(PIECE_VALUES.get(p, 0) for p in cap) - sum(PIECE_VALUES.get(p, 0) for p in opp_cap)

    # menü
    def draw_menu(self):
        self.menu_bg_offset = (self.menu_bg_offset + 0.5) % 80
        for y in range(0, HEIGHT + 80, 80):
            for x in range(0, WIDTH + 80, 80):
                c = (43, 40, 37) if ((x + y) // 80) % 2 == 0 else (47, 44, 41)
                pygame.draw.rect(self.screen, c, (x - self.menu_bg_offset, y - self.menu_bg_offset, 80, 80))
        pygame.draw.rect(self.screen, C_GREEN, (0, 0, WIDTH, 6))

        pw, ph = 600, 760
        px, py = WIDTH // 2 - pw // 2, HEIGHT // 2 - ph // 2 + 10
        
        # Soft shadow
        sh = pygame.Surface((pw + 20, ph + 20), pygame.SRCALPHA)
        for i in range(10):
            pygame.draw.rect(sh, (0, 0, 0, 15 - i*1.5), (i, i, pw + 20 - i*2, ph + 20 - i*2), border_radius=20)
        self.screen.blit(sh, (px - 10, py - 10))
        
        # Main panel
        pygame.draw.rect(self.screen, C_PANEL, (px, py, pw, ph), border_radius=16)
        pygame.draw.rect(self.screen, (65, 63, 60), (px, py, pw, ph), 1, border_radius=16)

        #Logo 
        lx = WIDTH // 2
        pygame.draw.circle(self.screen, C_GREEN, (lx, py + 50), 30)
        # Custom knight silhouette in the circle
        pygame.draw.ellipse(self.screen, C_WHITE, (lx - 12, py + 34, 20, 18))
        pygame.draw.rect(self.screen, C_WHITE, (lx - 8, py + 48, 16, 12))
        pygame.draw.rect(self.screen, C_WHITE, (lx - 14, py + 58, 28, 8), border_radius=3)
        pygame.draw.circle(self.screen, C_GREEN, (lx, py + 42), 3) # Eye
        
        logo = self.f_logo.render("GrandMaster", True, C_WHITE)
        chess_txt = self.f_title.render("CHESS", True, C_GREEN_HOVER)
        self.screen.blit(logo, (lx - logo.get_width()//2, py + 95))
        self.screen.blit(chess_txt, (lx - chess_txt.get_width()//2, py + 155))
        
        sub = self.f_sm.render("Offline Chess", True, C_GRAY)
        self.screen.blit(sub, (lx - sub.get_width() // 2, py + 195))
        pygame.draw.line(self.screen, (70, 68, 64), (px + 40, py + 225), (px + pw - 40, py + 225))

        # Mod Selection Buttons (VS_BOT / PUZZLE)
        mod_w = (pw - 80 - 15) // 2
        
        self.btn_vs_bot = pygame.Rect(px + 40, py + 240, mod_w, 48)
        self.btn_puzzle = pygame.Rect(px + 40 + mod_w + 15, py + 240, mod_w, 48)
        
        # Draw Mod Selection
        sel_bot = (self.mode == "VS_BOT")
        pygame.draw.rect(self.screen, C_GREEN if sel_bot else (60, 58, 55), self.btn_vs_bot, border_radius=8)
        tt = self.f_ui.render("Bilgisayara Kar\u015f\u0131", True, C_WHITE if sel_bot else C_GRAY)
        self.screen.blit(tt, (self.btn_vs_bot.centerx - tt.get_width()//2, self.btn_vs_bot.centery - tt.get_height()//2))

        sel_puz = (self.mode == "PUZZLE")
        pygame.draw.rect(self.screen, C_GREEN if sel_puz else (60, 58, 55), self.btn_puzzle, border_radius=8)
        tt = self.f_ui.render("Satran\u00e7 Bulmacalar\u0131", True, C_WHITE if sel_puz else C_GRAY)
        self.screen.blit(tt, (self.btn_puzzle.centerx - tt.get_width()//2, self.btn_puzzle.centery - tt.get_height()//2))

        # Configuration Area depending on mode
        if self.mode == "VS_BOT":
            # Difficulty
            self.screen.blit(self.f_ui.render("Zorluk Seviyesi", True, C_WHITE), (px + 40, py + 310))
            self.diff_btns = []
            bw = (pw - 80 - 4 * 8) // 5
            for i, label in enumerate(DIFF_LABELS):
                bx = px + 40 + i * (bw + 8)
                by = py + 345
                r = pygame.Rect(bx, by, bw, 42)
                self.diff_btns.append(r)
                sel = (i == self.sel_diff)
                pygame.draw.rect(self.screen, C_WHITE if sel else (60, 58, 55), r, border_radius=8)
                t = self.f_sm.render(label, True, (40, 40, 40) if sel else C_GRAY)
                self.screen.blit(t, (r.centerx - t.get_width() // 2, r.centery - t.get_height() // 2))

            # Dropdown for Time Control
            self.screen.blit(self.f_ui.render("S\u00fcre Kontrol\u00fc", True, C_WHITE), (px + 40, py + 405))
            self.time_dd_rect = pygame.Rect(px + 40, py + 440, 240, 44)
            pygame.draw.rect(self.screen, (60, 58, 55), self.time_dd_rect, border_radius=8)
            sel_lbl = TIME_PRESETS[self.sel_time][0]
            ts = self.f_ui.render(sel_lbl + " \u25bc", True, C_WHITE)
            self.screen.blit(ts, (self.time_dd_rect.x + 15, self.time_dd_rect.centery - ts.get_height() // 2))

            # Color choice
            self.screen.blit(self.f_ui.render("Taraf Se\u00e7imi", True, C_WHITE), (px + 40, py + 505))
            cw = 80
            self.color_btns = []
            for i, (label, col) in enumerate([("Beyaz", chess.WHITE), ("Siyah", chess.BLACK)]):
                bx = px + 40 + i * (cw + 12)
                by = py + 540
                r = pygame.Rect(bx, by, cw, 44)
                self.color_btns.append((r, col))
                sel = (self.player_color == col)
                pygame.draw.rect(self.screen, C_WHITE if sel else (60, 58, 55), r, border_radius=8)
                t = self.f_ui.render(label, True, (40, 40, 40) if sel else C_GRAY)
                self.screen.blit(t, (r.centerx - t.get_width() // 2, r.centery - t.get_height() // 2))

        else:
            # PUZZLE MODE Configuration with Dropdown
            self.screen.blit(self.f_ui.render("Bulmaca Se\u00e7", True, C_WHITE), (px + 40, py + 310))
            self.puz_dd_rect = pygame.Rect(px + 40, py + 345, pw - 80, 44)
            pygame.draw.rect(self.screen, (60, 58, 55), self.puz_dd_rect, border_radius=8)
            puzz_list = get_all_puzzles()
            self.puzzle_idx = min(self.puzzle_idx, len(puzz_list)-1)
            sel_lbl = f"#{self.puzzle_idx+1}: {puzz_list[self.puzzle_idx][1]}"
            ts = self.f_ui.render(sel_lbl + " \u25bc", True, C_WHITE)
            self.screen.blit(ts, (self.puz_dd_rect.x + 15, self.puz_dd_rect.centery - ts.get_height() // 2))

            # Color choice for puzzle
            self.screen.blit(self.f_ui.render("Taraf Se\u00e7imi", True, C_WHITE), (px + 40, py + 410))
            
            # Lowered the info text significantly to avoid overlapping the radio buttons
            self.screen.blit(self.f_sm.render("(Taraf bulmacaya g\u00f6re otomatik ayarlan\u0131r. Tahta yönü değişir.)", True, C_GRAY), (px + 40, py + 500))
            cw = 80
            self.color_btns = []
            for i, (label, col) in enumerate([("Beyaz", chess.WHITE), ("Siyah", chess.BLACK)]):
                bx = px + 40 + i * (cw + 12)
                by = py + 445
                r = pygame.Rect(bx, by, cw, 44)
                self.color_btns.append((r, col))
                sel = (self.player_color == col)
                pygame.draw.rect(self.screen, C_WHITE if sel else (60, 58, 55), r, border_radius=8)
                t = self.f_ui.render(label, True, (40, 40, 40) if sel else C_GRAY)
                self.screen.blit(t, (r.centerx - t.get_width() // 2, r.centery - t.get_height() // 2))

        # Play button (positioned at the bottom absolute)
        pbw, pbh = 320, 72
        self.play_btn = pygame.Rect(WIDTH // 2 - pbw // 2, py + 620, pbw, pbh)
        mx, my = pygame.mouse.get_pos()
        hov = self.play_btn.collidepoint(mx, my)
        bc = C_GREEN_HOVER if hov else C_GREEN
        if hov:
            gs = pygame.Surface((pbw + 20, pbh + 20), pygame.SRCALPHA)
            pygame.draw.rect(gs, (129, 182, 76, 40), (0, 0, pbw + 20, pbh + 20), border_radius=18)
            self.screen.blit(gs, (self.play_btn.x - 10, self.play_btn.y - 10))
        pygame.draw.rect(self.screen, bc, self.play_btn, border_radius=14)
        pt = self.f_big.render("OYNA", True, C_WHITE)
        self.screen.blit(pt, (self.play_btn.centerx - pt.get_width() // 2, self.play_btn.centery - pt.get_height() // 2))

        # Render Dropdown Lists (On Top)
        if hasattr(self, 'time_dd_open') and self.time_dd_open and self.mode == "VS_BOT":
            self.time_items_rects = []
            max_visible = 5
            item_h = 40
            dh = min(len(TIME_PRESETS), max_visible) * item_h
            
            # Draw dropdown container
            dd_surface = pygame.Surface((self.time_dd_rect.width, dh))
            dd_surface.fill((50, 48, 45))
            
            for i, (label, _, _) in enumerate(TIME_PRESETS):
                visible_y = (i - self.time_scroll) * item_h
                # Check if item is within visible bounds of the surface
                if 0 <= visible_y < dh:
                    ir = pygame.Rect(0, visible_y, self.time_dd_rect.width, item_h)
                    abs_ir = pygame.Rect(self.time_dd_rect.x, self.time_dd_rect.bottom + visible_y, self.time_dd_rect.width, item_h)
                    self.time_items_rects.append((i, abs_ir))
                    if abs_ir.collidepoint(mx, my):
                        pygame.draw.rect(dd_surface, (70, 68, 64), ir)
                    t = self.f_sm.render(label, True, C_WHITE)
                    dd_surface.blit(t, (15, ir.centery - t.get_height() // 2))

            # Draw visual scrollbar for time_dd
            if len(TIME_PRESETS) > max_visible:
                sb_width = 8
                sb_x = self.time_dd_rect.width - sb_width - 4
                sb_y = 4
                sb_h = max(20, int(dh * (max_visible / len(TIME_PRESETS)))) - 8
                # Track
                pygame.draw.rect(dd_surface, (40, 38, 35), (sb_x, 0, sb_width + 4, dh))
                # Thumb
                max_scroll = len(TIME_PRESETS) - max_visible
                thumb_y = sb_y + (self.time_scroll / max_scroll) * (dh - sb_h - 8)
                thumb_rect = pygame.Rect(sb_x, thumb_y, sb_width, sb_h)
                pygame.draw.rect(dd_surface, (90, 88, 85), thumb_rect, border_radius=4)
                
                # Store absolute thumb rect for event handling
                self.time_thumb_rect = pygame.Rect(
                    self.time_dd_rect.x + thumb_rect.x,
                    self.time_dd_rect.bottom + thumb_rect.y,
                    thumb_rect.width, thumb_rect.height
                )
            else:
                self.time_thumb_rect = None
                    
            pygame.draw.rect(self.screen, (65, 63, 60), (self.time_dd_rect.x, self.time_dd_rect.bottom, self.time_dd_rect.width, dh), 1, border_radius=8)
            self.screen.blit(dd_surface, (self.time_dd_rect.x, self.time_dd_rect.bottom))

        if hasattr(self, 'puz_dd_open') and self.puz_dd_open and self.mode == "PUZZLE":
            self.puz_items_rects = []
            puzz_list = get_all_puzzles()
            max_visible = 5
            item_h = 40
            dh = min(len(puzz_list), max_visible) * item_h
            
            # Draw dropdown container
            dd_surface = pygame.Surface((self.puz_dd_rect.width, dh))
            dd_surface.fill((50, 48, 45))
            
            for i, (_, desc) in enumerate(puzz_list):
                visible_y = (i - self.puz_scroll) * item_h
                if 0 <= visible_y < dh:
                    ir = pygame.Rect(0, visible_y, self.puz_dd_rect.width, item_h)
                    abs_ir = pygame.Rect(self.puz_dd_rect.x, self.puz_dd_rect.bottom + visible_y, self.puz_dd_rect.width, item_h)
                    self.puz_items_rects.append((i, abs_ir))
                    if abs_ir.collidepoint(mx, my):
                        pygame.draw.rect(dd_surface, (70, 68, 64), ir)
                    t = self.f_sm.render(f"#{i+1}: {desc}", True, C_WHITE)
                    dd_surface.blit(t, (15, ir.centery - t.get_height() // 2))

            # Draw visual scrollbar for puzzle dd
            if len(puzz_list) > max_visible:
                sb_width = 8
                sb_x = self.puz_dd_rect.width - sb_width - 4
                sb_y = 4
                sb_h = max(20, int(dh * (max_visible / len(puzz_list)))) - 8
                # Track
                pygame.draw.rect(dd_surface, (40, 38, 35), (sb_x, 0, sb_width + 4, dh))
                # Thumb
                max_scroll = len(puzz_list) - max_visible
                thumb_y = sb_y + (self.puz_scroll / max_scroll) * (dh - sb_h - 8)
                thumb_rect = pygame.Rect(sb_x, thumb_y, sb_width, sb_h)
                pygame.draw.rect(dd_surface, (90, 88, 85), thumb_rect, border_radius=4)
                
                # Store absolute rect
                self.puz_thumb_rect = pygame.Rect(
                    self.puz_dd_rect.x + thumb_rect.x,
                    self.puz_dd_rect.bottom + thumb_rect.y,
                    thumb_rect.width, thumb_rect.height
                )
            else:
                self.puz_thumb_rect = None

            pygame.draw.rect(self.screen, (65, 63, 60), (self.puz_dd_rect.x, self.puz_dd_rect.bottom, self.puz_dd_rect.width, dh), 1, border_radius=8)
            self.screen.blit(dd_surface, (self.puz_dd_rect.x, self.puz_dd_rect.bottom))

        ft = self.f_xs.render("Designed by:EGNAKE", True, (90, 90, 90))
        self.screen.blit(ft, (WIDTH // 2 - ft.get_width() // 2, HEIGHT - 30))

    # ===================== BOARD =====================
    def draw_board(self):
        pygame.draw.rect(self.screen, (30, 30, 30),
                         (BOARD_MARGIN_LEFT - 3, BOARD_MARGIN_TOP - 3, BOARD_SIZE + 6, BOARD_SIZE + 6), border_radius=2)
        for row in range(8):
            for col in range(8):
                sq = chess.square(col, 7 - row) if not self.flipped else chess.square(7 - col, row)
                color = C_LIGHT if (row + col) % 2 == 0 else C_DARK
                rx = col * SQ + BOARD_MARGIN_LEFT
                ry = row * SQ + BOARD_MARGIN_TOP
                pygame.draw.rect(self.screen, color, (rx, ry, SQ, SQ))

                # Last move
                if self.last_move:
                    if sq == self.last_move.from_square:
                        s = pygame.Surface((SQ, SQ), pygame.SRCALPHA); s.fill(C_LAST_FROM)
                        self.screen.blit(s, (rx, ry))
                    elif sq == self.last_move.to_square:
                        s = pygame.Surface((SQ, SQ), pygame.SRCALPHA); s.fill(C_LAST_TO)
                        self.screen.blit(s, (rx, ry))

                # Selected
                if self.selected_sq is not None and sq == self.selected_sq:
                    s = pygame.Surface((SQ, SQ), pygame.SRCALPHA); s.fill(C_SELECTED)
                    self.screen.blit(s, (rx, ry))

                # Check glow
                if self.board.is_check():
                    p = self.board.piece_at(sq)
                    if p and p.piece_type == chess.KING and p.color == self.board.turn:
                        s = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
                        # Softer pale red like chess.com
                        pygame.draw.circle(s, (235, 64, 52, 100), (SQ // 2, SQ // 2), SQ // 2)
                        # A slight intense center
                        for rad in range(SQ // 2 - 4, 0, -4):
                            a = int(100 + 100 * (1 - rad / (SQ // 2)))
                            pygame.draw.circle(s, (255, 64, 52, a), (SQ // 2, SQ // 2), rad)
                        self.screen.blit(s, (rx, ry))

                # Right click square highlights
                if sq in getattr(self, "right_clicked_sqs", set()):
                    s = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
                    s.fill((235, 64, 52, 120))  # Pale transparent red
                    self.screen.blit(s, (rx, ry))

                # Legal move dots
                if self.selected_sq is not None and sq in self.legal_targets:
                    s = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
                    if self.board.piece_at(sq):
                        pygame.draw.circle(s, (0, 0, 0, 50), (SQ // 2, SQ // 2), SQ // 2 - 4, 5)
                    else:
                        pygame.draw.circle(s, (0, 0, 0, 50), (SQ // 2, SQ // 2), 14)
                    self.screen.blit(s, (rx, ry))

                # Coords inside board
                if self.flipped:
                    actual_col, actual_row = 7 - col, row
                else:
                    actual_col, actual_row = col, 7 - row
                tc = C_DARK if (row + col) % 2 == 0 else C_LIGHT
                if col == 0:
                    ct = self.f_coord.render(str(actual_row + 1), True, tc)
                    self.screen.blit(ct, (rx + 3, ry + 2))
                if row == 7:
                    ct = self.f_coord.render(chr(97 + actual_col), True, tc)
                    self.screen.blit(ct, (rx + SQ - ct.get_width() - 3, ry + SQ - ct.get_height() - 1))

    def draw_pieces(self):
        for sq in chess.SQUARES:
            if self.dragging_piece and sq == self.selected_sq:
                continue
            if self.animating and self.anim_move and sq == self.anim_move.to_square:
                continue
            p = self.board.piece_at(sq)
            if p:
                img = self.images.get(p.symbol())
                if img:
                    px, py = self.sq_to_px(sq)
                    off = (SQ - img.get_width()) // 2
                    sh = pygame.Surface((img.get_width(), img.get_height()), pygame.SRCALPHA)
                    sh.fill((0, 0, 0, 20))
                    self.screen.blit(sh, (px + off + 3, py + off + 3))
                    self.screen.blit(img, (px + off, py + off))

        if self.dragging_piece:
            img = self.images.get(self.dragging_piece.symbol())
            if img:
                self.screen.blit(img, (self.drag_pos[0] - img.get_width() // 2, self.drag_pos[1] - img.get_height() // 2))

        if self.animating and self.anim_piece:
            img = self.images.get(self.anim_piece)
            if img:
                t = min(1.0, self.anim_t / self.anim_duration)
                t = t * t * (3 - 2 * t)
                cx = self.anim_start[0] + (self.anim_end[0] - self.anim_start[0]) * t
                cy = self.anim_start[1] + (self.anim_end[1] - self.anim_start[1]) * t
                off = (SQ - img.get_width()) // 2
                self.screen.blit(img, (cx + off, cy + off))

    def draw_arrow(self, start_sq, end_sq, color):
        p1x, p1y = self.sq_to_px(start_sq)
        p2x, p2y = self.sq_to_px(end_sq)
        p1 = (p1x + SQ // 2, p1y + SQ // 2)
        p2 = (p2x + SQ // 2, p2y + SQ // 2)
        if p1 == p2: return
        angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        # Professional thick arrow head
        le = (p1[0] + (dist - 14) * math.cos(angle), p1[1] + (dist - 14) * math.sin(angle))
        # Draw thick shaft with rounded caps
        pygame.draw.line(s, color, p1, le, 14)
        pygame.draw.circle(s, color, (int(p1[0]), int(p1[1])), 7)
        # Draw huge sharp arrow head
        hs = 24 # head size
        hw = 0.65 # head width angle
        h1 = (p2[0] - hs * math.cos(angle - hw), p2[1] - hs * math.sin(angle - hw))
        h2 = (p2[0] - hs * math.cos(angle + hw), p2[1] - hs * math.sin(angle + hw))
        pygame.draw.polygon(s, color, [p2, h1, h2])
        self.screen.blit(s, (0, 0))

    # ===================== EVAL BAR =====================
    def draw_eval_bar(self):
        bar_h = BOARD_SIZE
        pygame.draw.rect(self.screen, C_EVAL_BLACK, (EVAL_BAR_X, BOARD_MARGIN_TOP, EVAL_BAR_W, bar_h), border_radius=3)
        clamped = max(-10, min(10, self.eval_score))
        white_pct = 0.5 + (clamped / 20.0)
        white_h = int(bar_h * white_pct)
        wy = BOARD_MARGIN_TOP + bar_h - white_h
        pygame.draw.rect(self.screen, C_EVAL_WHITE, (EVAL_BAR_X, wy, EVAL_BAR_W, white_h), border_radius=3)
        if abs(self.eval_score) < 100:
            txt = f"{self.eval_score:+.1f}"
        else:
            txt = "M" if self.eval_score > 0 else "-M"
        if self.eval_score >= 0:
            et = self.f_eval.render(txt, True, (40, 40, 40))
            self.screen.blit(et, (EVAL_BAR_X + EVAL_BAR_W // 2 - et.get_width() // 2, BOARD_MARGIN_TOP + bar_h - 18))
        else:
            et = self.f_eval.render(txt, True, (200, 200, 200))
            self.screen.blit(et, (EVAL_BAR_X + EVAL_BAR_W // 2 - et.get_width() // 2, BOARD_MARGIN_TOP + 4))

    def update_eval_async(self):
        if self.engine and not self.board.is_game_over():
            board_copy = self.board.copy()
            def _eval():
                try:
                    with self._engine_lock:
                        info = self.engine.analyse(board_copy, chess.engine.Limit(time=0.15))
                    score = info.get("score")
                    if score:
                        cp = score.white().score(mate_score=10000)
                        self.eval_score = cp / 100.0
                except Exception:
                    pass
            if self.eval_thread is None or not self.eval_thread.is_alive():
                self.eval_thread = threading.Thread(target=_eval, daemon=True)
                self.eval_thread.start()

    # ===================== DRAW ICONS =====================
    def _draw_icon_undo(self, surface, x, y, color):
        pygame.draw.arc(surface, color, (x-8, y-6, 16, 12), math.pi/2, 3*math.pi/2 + 0.5, 3)
        pygame.draw.polygon(surface, color, [(x-8, y+2), (x-13, y-3), (x-3, y-3)])

    def _draw_icon_bulb(self, surface, x, y, color):
        pygame.draw.circle(surface, color, (x, y-3), 6, 2)
        pygame.draw.line(surface, color, (x-3, y+5), (x+3, y+5), 2)
        pygame.draw.line(surface, color, (x-2, y+7), (x+2, y+7), 2)
        pygame.draw.line(surface, color, (x, y-12), (x, y-10), 2)
        pygame.draw.line(surface, color, (x-7, y-6), (x-5, y-5), 2)
        pygame.draw.line(surface, color, (x+7, y-6), (x+5, y-5), 2)

    def _draw_icon_flag(self, surface, x, y, color):
        pygame.draw.line(surface, color, (x-4, y+8), (x-4, y-8), 2)
        pygame.draw.polygon(surface, color, [(x-4, y-8), (x+6, y-4), (x-4, y)])

    # ===================== SIDEBAR =====================
    def draw_sidebar(self):
        bot_label = "Stockfish " + DIFF_LABELS[self.sel_diff]
        player_label = "Oyuncu"
        top_is_bot = not self.flipped
        top_name = bot_label if top_is_bot else player_label
        bot_name = player_label if top_is_bot else bot_label
        top_time = self.black_time if top_is_bot else self.white_time
        bot_time = self.white_time if top_is_bot else self.black_time
        top_color = chess.BLACK if top_is_bot else chess.WHITE
        bot_color = chess.WHITE if top_is_bot else chess.BLACK

        card_h = 80
        # Top player card
        self._draw_player_card(PANEL_X, BOARD_MARGIN_TOP, top_name, top_time, top_color,
                               self.board.turn == top_color, card_h)
        # Bottom player card
        self._draw_player_card(PANEL_X, BOARD_MARGIN_TOP + BOARD_SIZE - card_h, bot_name, bot_time, bot_color,
                               self.board.turn == bot_color, card_h)

        # Control buttons - beautifully styled with custom Pygame drawn icons
        btn_h = 44
        btn_gap = 10
        total_btn_h = 3 * btn_h + 2 * btn_gap
        btn_y = BOARD_MARGIN_TOP + BOARD_SIZE - card_h - total_btn_h - 16
        self.undo_btn = pygame.Rect(PANEL_X, btn_y, PANEL_W, btn_h)
        self.hint_btn = pygame.Rect(PANEL_X, btn_y + btn_h + btn_gap, PANEL_W, btn_h)
        self.resign_btn = pygame.Rect(PANEL_X, btn_y + 2 * (btn_h + btn_gap), PANEL_W, btn_h)

        mx, my = pygame.mouse.get_pos()
        btn_data = [
            (self.undo_btn, "Geri Al", self._draw_icon_undo),
            (self.hint_btn, "\u0130pucu", self._draw_icon_bulb),
            (self.resign_btn, "Teslim Ol", self._draw_icon_flag),
        ]
        for r, txt, draw_func in btn_data:
            hov = r.collidepoint(mx, my)
            c = (75, 73, 69) if hov else (55, 53, 50)
            
            # Button background with hover scale effect
            br = r.copy()
            if hov:
                br.inflate_ip(4, 0)
            pygame.draw.rect(self.screen, c, br, border_radius=8)
            pygame.draw.rect(self.screen, (85, 83, 79), br, 1, border_radius=8)
            
            # Custom drawn icon in a subtle well
            pygame.draw.circle(self.screen, (40, 38, 35), (br.x + 28, br.centery), 16)
            draw_func(self.screen, br.x + 28, br.centery, C_WHITE if hov else C_GRAY)
            
            # Crisp text
            t = self.f_ui.render(txt, True, C_WHITE if hov else C_GRAY)
            self.screen.blit(t, (br.x + 56, br.centery - t.get_height() // 2))

        # Move history panel - between top card and buttons
        mh_y = BOARD_MARGIN_TOP + card_h + 12
        mh_h = btn_y - mh_y - 12
        if mh_h > 50:
            pygame.draw.rect(self.screen, C_PANEL2, (PANEL_X, mh_y, PANEL_W, mh_h), border_radius=8)
            ht = self.f_sm.render("Hamle Ge\u00e7mi\u015fi", True, C_GRAY)
            self.screen.blit(ht, (PANEL_X + 10, mh_y + 6))
            pygame.draw.line(self.screen, (60, 58, 55), (PANEL_X + 10, mh_y + 28), (PANEL_X + PANEL_W - 10, mh_y + 28))

            y_off = mh_y + 34
            max_vis = (mh_h - 40) // 22
            moves_san = []
            temp = chess.Board(self.start_fen)
            for m in self.board.move_stack:
                moves_san.append(temp.san(m))
                temp.push(m)
            start = max(0, len(moves_san) - max_vis * 2)
            for i in range(start, len(moves_san), 2):
                num = i // 2 + 1
                w = moves_san[i] if i < len(moves_san) else ""
                b = moves_san[i + 1] if i + 1 < len(moves_san) else ""
                line = f"{num}. {w}  {b}"
                ct = self.f_sm.render(line, True, (190, 190, 190))
                if y_off + 20 < mh_y + mh_h - 6:
                    self.screen.blit(ct, (PANEL_X + 12, y_off))
                    y_off += 22

        # Status text below history (replaces learning mode errors)
        if self.mode == "PUZZLE":
            puzz_list = get_all_puzzles()
            if self.puzzle_idx < len(puzz_list):
                msg = puzz_list[self.puzzle_idx][1]
                lt = self.f_sm.render(f"BULMACA: {msg}", True, (240, 190, 80))
                self.screen.blit(lt, (PANEL_X + 5, BOARD_MARGIN_TOP - 26))

        # Bot thinking indicator
        if self.bot_thinking:
            dots = "." * (1 + int(time.time() * 2) % 3)
            ti = self.f_xs.render(f"D\u00fc\u015f\u00fcn\u00fcyor{dots}", True, C_GREEN)
            self.screen.blit(ti, (PANEL_X + 10, BOARD_MARGIN_TOP + BOARD_SIZE + 10))

    def _draw_player_card(self, x, y, name, time_left, color, is_active, h):
        w = PANEL_W
        bg = (52, 50, 46) if is_active else C_PANEL2
        pygame.draw.rect(self.screen, bg, (x, y, w, h), border_radius=10)
        if is_active:
            pygame.draw.rect(self.screen, C_GREEN, (x, y, 4, h), border_radius=2)

        # Avatar - use mini piece image instead of unicode
        ac = C_WHITE if color == chess.WHITE else (60, 60, 60)
        pygame.draw.circle(self.screen, ac, (x + 28, y + 26), 16)
        pygame.draw.circle(self.screen, (100, 100, 100), (x + 28, y + 26), 16, 2)
        # Draw king mini image
        king_sym = 'K' if color == chess.WHITE else 'k'
        ki = self.mini_images.get(king_sym)
        if ki:
            self.screen.blit(ki, (x + 28 - 11, y + 26 - 11))

        # Name
        nt = self.f_ui.render(name, True, C_WHITE)
        self.screen.blit(nt, (x + 52, y + 8))

        # Captured pieces as mini images
        cap = self.get_captured(color)
        cx = x + 52
        for pt in cap:
            sym = PIECE_SYM_MAP.get(pt)
            if sym:
                key = sym if color == chess.WHITE else sym.lower()
                # Captured pieces are opponent's, so flip the case
                key = sym.lower() if color == chess.WHITE else sym
                mi = self.mini_images.get(key)
                if mi:
                    self.screen.blit(mi, (cx, y + 32))
                    cx += 16
        adv = self.material_advantage(color)
        if adv > 0:
            at = self.f_xs.render(f"+{adv}", True, C_GRAY)
            self.screen.blit(at, (cx + 4, y + 36))

        # Timer
        mins, secs = divmod(max(0, int(time_left)), 60)
        timer_str = f"{mins:02d}:{secs:02d}"
        if is_active and time_left < 30:
            tc = (235, 64, 52)
        elif is_active:
            tc = C_WHITE
        else:
            tc = C_GRAY
        tr = pygame.Rect(x + w - 140, y + h - 46, 126, 38)
        tbg = (35, 33, 30) if not is_active else (52, 50, 46)
        pygame.draw.rect(self.screen, tbg, tr, border_radius=6)
        tt = self.f_timer.render(timer_str, True, tc)
        self.screen.blit(tt, (tr.centerx - tt.get_width() // 2, tr.centery - tt.get_height() // 2))

    # ===================== PROMOTION =====================
    def draw_promotion(self):
        if not self.promoting:
            return
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 120))
        self.screen.blit(s, (0, 0))
        px_pos, py_pos = self.sq_to_px(self.promo_sq)
        is_white = self.board.turn == chess.WHITE
        pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        syms = ['Q', 'R', 'B', 'N'] if is_white else ['q', 'r', 'b', 'n']
        self.promo_rects = []
        going_down = (is_white and not self.flipped) or (not is_white and self.flipped)
        for i, (pt, sym) in enumerate(zip(pieces, syms)):
            ry = py_pos + i * SQ if going_down else py_pos - i * SQ
            r = pygame.Rect(px_pos, ry, SQ, SQ)
            pygame.draw.rect(self.screen, C_LIGHT if i % 2 == 0 else (200, 200, 180), r)
            pygame.draw.rect(self.screen, (100, 100, 100), r, 2)
            img = self.images.get(sym)
            if img:
                off = (SQ - img.get_width()) // 2
                self.screen.blit(img, (r.x + off, r.y + off))
            self.promo_rects.append((r, pt))

    # ===================== GAME OVER =====================
    def draw_game_over(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))
        pw, ph = 400, 260
        px, py = WIDTH // 2 - pw // 2, HEIGHT // 2 - ph // 2
        pygame.draw.rect(self.screen, C_PANEL, (px, py, pw, ph), border_radius=16)
        pygame.draw.rect(self.screen, C_GREEN, (px, py, pw, 6), border_top_left_radius=16, border_top_right_radius=16)

        if self.board.is_checkmate():
            winner = "Beyaz" if self.board.turn == chess.BLACK else "Siyah"
            res = f"{winner} Kazand\u0131!"
            detail = "\u015eah Mat"
        elif self.board.is_stalemate():
            res, detail = "Berabere!", "Pat"
        elif self.board.is_insufficient_material():
            res, detail = "Berabere!", "Yetersiz Materyal"
        elif self._resigned:
            res, detail = "Teslim Oldunuz!", "\u0130stifa"
        elif self.white_time <= 0:
            res, detail = "Siyah Kazand\u0131!", "S\u00fcre Bitti"
        elif self.black_time <= 0:
            res, detail = "Beyaz Kazand\u0131!", "S\u00fcre Bitti"
        else:
            res, detail = "Oyun Bitti!", ""

        rt = self.f_title.render(res, True, C_WHITE)
        self.screen.blit(rt, (px + pw // 2 - rt.get_width() // 2, py + 30))
        dt = self.f_ui.render(detail, True, C_GRAY)
        self.screen.blit(dt, (px + pw // 2 - dt.get_width() // 2, py + 80))

        # New Game
        self.newgame_btn = pygame.Rect(px + pw // 2 - 120, py + 130, 240, 55)
        mx, my = pygame.mouse.get_pos()
        hov = self.newgame_btn.collidepoint(mx, my)
        pygame.draw.rect(self.screen, C_GREEN_HOVER if hov else C_GREEN, self.newgame_btn, border_radius=10)
        nt = self.f_ui.render("Yeni Oyun", True, C_WHITE)  
        self.screen.blit(nt, (self.newgame_btn.centerx - nt.get_width() // 2, self.newgame_btn.centery - nt.get_height() // 2))

        # Back to menu
        self.quit_btn = pygame.Rect(px + pw // 2 - 80, py + 200, 160, 40)
        hov2 = self.quit_btn.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (70, 68, 64) if hov2 else (55, 53, 50), self.quit_btn, border_radius=8)
        qt = self.f_sm.render("Ana Men\u00fc", True, C_GRAY)
        self.screen.blit(qt, (self.quit_btn.centerx - qt.get_width() // 2, self.quit_btn.centery - qt.get_height() // 2))

    def start_bot_move(self):
        if self.engine and not self.board.is_game_over() and not self.bot_thinking:
            self.bot_thinking = True
            board_copy = self.board.copy()
            if self.mode == "PUZZLE":
                def _t():
                    try:
                        with self._engine_lock:
                            # Use analyse instead of play to avoid UCI history parsing errors on custom FENs
                            res = self.engine.analyse(board_copy, chess.engine.Limit(time=0.5))
                            if "pv" in res and res["pv"]:
                                self.bot_result = res["pv"][0]
                            else:
                                self.bot_result = None
                    except Exception:
                        self.bot_result = None
                        self.bot_thinking = False
                t = threading.Thread(target=_t, daemon=True)
                t.start()
                return

            diff = DIFF_VALUES[self.sel_diff]
            # Fast response for puzzles, human-like delay for VS BOT
            delay = 0.5 + random.uniform(0, 0.5) if diff < 10 else 0.3
            self.bot_think_until = time.time() + delay
            def _think():
                try:
                    with self._engine_lock:
                        self.engine.configure({"Skill Level": diff})
                        result = self.engine.play(board_copy, chess.engine.Limit(time=0.3))
                    self.bot_result = result.move
                except Exception:
                    self.bot_result = None
                    self.bot_thinking = False
            t = threading.Thread(target=_think, daemon=True)
            t.start()

    def apply_bot_move(self):
        move = self.bot_result
        self.bot_result = None
        self.bot_thinking = False
        if move is None:
            return
        piece = self.board.piece_at(move.from_square)
        is_capture = self.board.piece_at(move.to_square) is not None
        is_castle = self.board.is_castling(move)
        self.anim_piece = piece.symbol() if piece else None
        self.anim_start = self.sq_to_px(move.from_square)
        self.anim_end = self.sq_to_px(move.to_square)
        self.anim_t = 0
        self.anim_move = move
        self.animating = True
        self.board.push(move)
        self.last_move = move
        self.hint_arrow = None
        if self.board.is_check():
            self.snd_check.play()
        elif is_capture:
            self.snd_capture.play()
        elif is_castle:
            self.snd_castle.play()
        else:
            self.snd_move.play()
        self.update_eval_async()

    # ===================== EVENTS =====================
    def handle_menu_event(self, event, mx, my):
        if event.type == pygame.MOUSEWHEEL:
            if getattr(self, 'time_dd_open', False) and self.mode == "VS_BOT":
                self.time_scroll = max(0, min(len(TIME_PRESETS) - 5, self.time_scroll - event.y))
            elif getattr(self, 'puz_dd_open', False) and self.mode == "PUZZLE":
                self.puz_scroll = max(0, min(len(get_all_puzzles()) - 5, self.puz_scroll - event.y))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check scrollbar thumbs BEFORE checking list items to intercept drags
            if getattr(self, 'time_dd_open', False) and self.time_thumb_rect and self.time_thumb_rect.collidepoint(mx, my):
                self.dragging_scrollbar = "time"
                self.drag_start_y = my
                self.drag_start_scroll = self.time_scroll
                return
            
            if getattr(self, 'puz_dd_open', False) and self.puz_thumb_rect and self.puz_thumb_rect.collidepoint(mx, my):
                self.dragging_scrollbar = "puzzle"
                self.drag_start_y = my
                self.drag_start_scroll = self.puz_scroll
                return

            # Handle Dropdowns first (since they are drawn on top)
            if self.mode == "VS_BOT" and getattr(self, 'time_dd_open', False):
                # Ensure we also don't close the dropdown if we accidentally miss the thumb by a tiny bit
                if self.time_thumb_rect and pygame.Rect(self.time_dd_rect.x, self.time_dd_rect.bottom, self.time_dd_rect.width, 200).collidepoint(mx, my):
                    for idx, r in self.time_items_rects:
                        if r.collidepoint(mx, my):
                            self.sel_time = idx
                            self.time_dd_open = False
                            return
                    return # Missed item but still inside dropdown rect, stay open
                else:
                    self.time_dd_open = False

            if self.mode == "PUZZLE" and getattr(self, 'puz_dd_open', False):
                if self.puz_thumb_rect and pygame.Rect(self.puz_dd_rect.x, self.puz_dd_rect.bottom, self.puz_dd_rect.width, 200).collidepoint(mx, my):
                    for idx, r in self.puz_items_rects:
                        if r.collidepoint(mx, my):
                            self.puzzle_idx = idx
                            self.puz_dd_open = False
                            return
                    return 
                else:
                    self.puz_dd_open = False

            if hasattr(self, 'btn_vs_bot') and self.btn_vs_bot.collidepoint(mx, my):
                self.mode = "VS_BOT"
            elif hasattr(self, 'btn_puzzle') and self.btn_puzzle.collidepoint(mx, my):
                self.mode = "PUZZLE"
            
            if self.mode == "VS_BOT":
                if hasattr(self, 'diff_btns'):
                    for i, r in enumerate(self.diff_btns):
                        if r.collidepoint(mx, my):
                            self.sel_diff = i
                if hasattr(self, 'time_dd_rect'):
                    if self.time_dd_rect.collidepoint(mx, my):
                        self.time_dd_open = True
                if hasattr(self, 'color_btns'):
                    for r, col in self.color_btns:
                        if r.collidepoint(mx, my):
                            self.player_color = col
                            self.flipped = (col == chess.BLACK)
            else:
                if hasattr(self, 'puz_dd_rect') and self.puz_dd_rect is not None:
                    if self.puz_dd_rect.collidepoint(mx, my):
                        self.puz_dd_open = True
                if hasattr(self, 'color_btns'):
                    for r, col in self.color_btns:
                        if r.collidepoint(mx, my):
                            self.player_color = col
                            self.flipped = (col == chess.BLACK)

            if getattr(self, "play_btn", None) and self.play_btn.collidepoint(mx, my):
                self.start_game()
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_scrollbar = None

        if event.type == pygame.MOUSEMOTION:
            if self.dragging_scrollbar:
                dy = my - self.drag_start_y
                
                if self.dragging_scrollbar == "time" and self.time_thumb_rect:
                    max_scroll = len(TIME_PRESETS) - 5
                    dh = 5 * 40
                    sb_h = max(20, int(dh * (5 / len(TIME_PRESETS)))) - 8
                    track_h = dh - sb_h - 8
                    
                    if track_h > 0:
                        delta = (dy / track_h) * max_scroll
                        self.time_scroll = max(0, min(max_scroll, int(self.drag_start_scroll + delta)))
                        
                elif self.dragging_scrollbar == "puzzle" and self.puz_thumb_rect:
                    plen = len(get_all_puzzles())
                    max_scroll = plen - 5
                    dh = 5 * 40
                    sb_h = max(20, int(dh * (5 / plen))) - 8
                    track_h = dh - sb_h - 8
                    
                    if track_h > 0:
                        delta = (dy / track_h) * max_scroll
                        self.puz_scroll = max(0, min(max_scroll, int(self.drag_start_scroll + delta)))

    def start_game(self):
        if self.mode == "VS_BOT":
            self.start_fen = chess.STARTING_FEN
            self.board = chess.Board(self.start_fen)
            _, t, inc = TIME_PRESETS[self.sel_time]
            self.white_time = self.black_time = t
            self.increment = inc
        else:
            puzz_list = get_all_puzzles()
            self.puzzle_idx = min(self.puzzle_idx, len(puzz_list)-1)
            fen, _ = puzz_list[self.puzzle_idx]
            self.start_fen = fen
            self.board = chess.Board(self.start_fen)
            # Find which color is to move in the FEN
            self.player_color = self.board.turn
            self.flipped = (self.player_color == chess.BLACK)
            self.white_time = self.black_time = 3600 # 1 hour for puzzles
            self.increment = 0

        self.last_tick = time.time()
        self.last_move = None
        self.selected_sq = None
        self.legal_targets = []
        self.user_arrows = []
        self.hint_arrow = None
        self.eval_score = 0.0
        self._resigned = False
        self.promoting = False
        self.animating = False
        self.bot_thinking = False
        self.bot_result = None
        self.blunder_message = None
        self.last_eval = 0.0
        self.state = "PLAYING"
        if self.player_color == chess.BLACK:
            self.start_bot_move()

    def handle_game_event(self, event, mx, my):
        if self.promoting:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for r, pt in self.promo_rects:
                    if r.collidepoint(mx, my):
                        move = chess.Move(self.promo_move.from_square, self.promo_move.to_square, promotion=pt)
                        if move in self.board.legal_moves:
                            self.board.push(move)
                            self.last_move = move
                            self.snd_promote.play()
                            self.user_arrows = []
                            self.hint_arrow = None
                            self.update_eval_async()
                        self.promoting = False
                        self.promo_move = None
            return

        sq = self.px_to_sq(mx, my)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and sq is not None:
                p = self.board.piece_at(sq)
                if p and p.color == self.board.turn and self.board.turn == self.player_color:
                    self.selected_sq = sq
                    self.dragging_piece = p
                    self.drag_pos = (mx, my)
                    self.legal_targets = [m.to_square for m in self.board.legal_moves if m.from_square == sq]
                elif self.selected_sq is not None and sq in self.legal_targets:
                    self._try_move(self.selected_sq, sq)
                else:
                    self.selected_sq = None
                    self.legal_targets = []
            elif event.button == 3 and sq is not None:
                self.arrow_start = sq
            elif event.button == 1:
                # Left click on empty board clears arrows and highlights
                if sq is not None:
                    self.user_arrows = []
                    self.right_clicked_sqs.clear()
                    
                if hasattr(self, 'undo_btn') and self.undo_btn.collidepoint(mx, my):
                    if len(self.board.move_stack) >= 2:
                        self.board.pop()
                        self.board.pop()
                        self.last_move = self.board.peek() if self.board.move_stack else None
                        self.update_eval_async()
                elif hasattr(self, 'hint_btn') and self.hint_btn.collidepoint(mx, my):
                    self._request_hint()
                elif hasattr(self, 'resign_btn') and self.resign_btn.collidepoint(mx, my):
                    self._resigned = True
                    self.snd_end.play()
                    self.state = "GAME_OVER"

        elif event.type == pygame.MOUSEMOTION and self.dragging_piece:
            self.drag_pos = (mx, my)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging_piece and sq is not None:
                if sq != self.selected_sq and sq in self.legal_targets:
                    self._try_move(self.selected_sq, sq)
                self.dragging_piece = None
                if sq != self.selected_sq:
                    self.selected_sq = None
                    self.legal_targets = []
            elif event.button == 1:
                self.dragging_piece = None
                self.selected_sq = None
                self.legal_targets = []
            elif event.button == 3 and self.arrow_start is not None and sq is not None:
                if self.arrow_start != sq:
                    arrow = (self.arrow_start, sq)
                    if arrow in self.user_arrows:
                        self.user_arrows.remove(arrow)
                    else:
                        self.user_arrows.append(arrow)
                else:
                    # Right clicking the same square highlights it
                    if sq in self.right_clicked_sqs:
                        self.right_clicked_sqs.remove(sq)
                    else:
                        self.right_clicked_sqs.add(sq)
                self.arrow_start = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                if len(self.board.move_stack) >= 2:
                    self.board.pop()
                    self.board.pop()
                    self.last_move = self.board.peek() if self.board.move_stack else None
            elif event.key == pygame.K_f:
                self.flipped = not self.flipped

    def _request_hint(self):
        if self.engine and not self.bot_thinking:
            board_copy = self.board.copy()
            def _h():
                try:
                    with self._engine_lock:
                        # Give the hint engine a full 1.0 second to find the truly best move
                        res = self.engine.analyse(board_copy, chess.engine.Limit(time=1.0))
                    if "pv" in res:
                        m = res["pv"][0]
                        self.hint_arrow = (m.from_square, m.to_square)
                except Exception:
                    pass
            threading.Thread(target=_h, daemon=True).start()

    def _try_move(self, from_sq, to_sq):
        piece = self.board.piece_at(from_sq)
        if piece and piece.piece_type == chess.PAWN and chess.square_rank(to_sq) in [0, 7]:
            self.promoting = True
            self.promo_move = chess.Move(from_sq, to_sq)
            self.promo_sq = to_sq
            self.dragging_piece = None
            return
        move = chess.Move(from_sq, to_sq)
        if move in self.board.legal_moves:
            is_capture = self.board.piece_at(to_sq) is not None
            is_castle = self.board.is_castling(move)
            self.board.push(move)
            self.last_move = move
            self.selected_sq = None
            self.legal_targets = []
            self.dragging_piece = None
            self.user_arrows = []
            self.hint_arrow = None
            
            # Add increment
            if self.board.turn == chess.WHITE:
                self.black_time += self.increment
            else:
                self.white_time += self.increment

            if self.board.is_check():
                self.snd_check.play()
            elif is_capture:
                self.snd_capture.play()
            elif is_castle:
                self.snd_castle.play()
            else:
                self.snd_move.play()
            self.update_eval_async()

    def handle_gameover_event(self, event, mx, my):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hasattr(self, 'newgame_btn') and self.newgame_btn.collidepoint(mx, my):
                self.start_game()
            elif hasattr(self, 'quit_btn') and self.quit_btn.collidepoint(mx, my):
                self.state = "MENU"

    # ===================== MAIN LOOP =====================
    def run(self):
        while True:
            mx, my = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.engine:
                        self.engine.quit()
                    pygame.quit()
                    sys.exit()
                if self.state == "MENU":
                    self.handle_menu_event(event, mx, my)
                elif self.state == "PLAYING":
                    self.handle_game_event(event, mx, my)
                elif self.state == "GAME_OVER":
                    self.handle_gameover_event(event, mx, my)

            if self.state == "MENU":
                self.draw_menu()
            elif self.state == "PLAYING":
                now = time.time()
                if self.last_tick == 0:
                    self.last_tick = now
                dt = now - self.last_tick
                self.last_tick = now
                if self.board.turn == chess.WHITE:
                    self.white_time -= dt
                else:
                    self.black_time -= dt
                if self.white_time <= 0 or self.black_time <= 0:
                    self.snd_end.play()
                    self.state = "GAME_OVER"

                if self.animating:
                    self.anim_t += dt
                    if self.anim_t >= self.anim_duration:
                        self.animating = False

                if self.board.is_game_over():
                    self.snd_end.play()
                    self.state = "GAME_OVER"

                # Check if bot finished thinking (with minimum delay)
                if self.bot_result is not None and time.time() >= self.bot_think_until:
                    self.apply_bot_move()

                self.screen.fill(C_BG)
                self.draw_eval_bar()
                self.draw_board()
                self.draw_pieces()
                if self.hint_arrow:
                    self.draw_arrow(self.hint_arrow[0], self.hint_arrow[1], C_ARROW_HINT)
                for sa, ea in self.user_arrows:
                    self.draw_arrow(sa, ea, C_ARROW_USER)
                self.draw_sidebar()
                self.draw_promotion()

                # Start bot move if needed (non-blocking)
                if (not self.animating and not self.promoting and not self.bot_thinking
                        and self.board.turn != self.player_color and self.state == "PLAYING"):
                    self.start_bot_move()

            elif self.state == "GAME_OVER":
                self.screen.fill(C_BG)
                self.draw_eval_bar()
                self.draw_board()
                self.draw_pieces()
                self.draw_sidebar()
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    ChessApp().run()