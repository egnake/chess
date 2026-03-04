import random

# Puzzles format: (FEN, Description)
PUZZLES_LIST = [
    # Mate in 1 / Temel Matlar
    ("6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1", "Koridor Matı (Beyaz Oynar)"),
    ("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", "Çoban Matı Örneği (Beyaz Oynar)"),
    ("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 1", "Gerçek Aptal Matı (Siyah Oynar)"),
    ("R7/8/8/8/8/5k2/8/5K2 w - - 0 1", "Basit Kale Matı (Beyaz Oynar)"),
    
    # Pratik ve Taktik
    ("3q1k2/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1", "Vezir Fedası Taktiği"),
    ("8/p7/kp2R3/8/1P6/PK6/8/8 w - - 0 1", "Basit Kale Oyun Sonu"),
    ("4r1k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1", "Ağır Taş Değişimi"),
    ("2r3k1/5ppp/8/8/8/8/1Q2BPPP/6K1 b - - 0 1", "Kale'nin Vezir Tehdidi"),
    ("6k1/1p3ppp/8/8/8/8/1P3PPP/3R2K1 w - - 0 1", "Kritik E-Hattı Baskısı"),
    
    # Pozisyonel Orta Oyun ve Oyun Sonu
    ("8/8/8/8/p7/1k6/1P6/1K6 b - - 0 1", "Piyon Oyunu - Opozisyon"),
    ("r1b1k2r/ppppqppp/2n2n2/4p3/1bB1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1", "İtalyan Açılışı Gelişimi"),
    ("r2qk2r/ppp2ppp/2n1bn2/2bnp3/2B5/2P2N2/PP1P1PPP/RNBQR1K1 w kq - 0 1", "Merkez Gerilimi (E4)"),
    ("8/2p5/1p1p4/pP1P1k1p/P1P2P1P/5K2/8/8 w - - 0 1", "Kilitlenmiş Piyon Zinciri"),
    ("2rq1rk1/1p2bppp/p2p1n2/4p3/4P1P1/1NN1Q3/PPP2P1P/2KR3R b - - 0 1", "Sicilya E-Hattı Savunması"),
    ("1k1r4/pp3ppp/2n1q3/8/8/4Q3/PP3PPP/1K1R4 w - - 0 1", "Merkez Değiş Tokuş Kararı"),
]

def get_random_puzzle():
    return random.choice(PUZZLES_LIST)

def get_puzzle(index):
    if 0 <= index < len(PUZZLES_LIST):
        return PUZZLES_LIST[index]
    return PUZZLES_LIST[0]

def get_all_puzzles():
    return PUZZLES_LIST
