<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Pygame-2.0+-green?style=for-the-badge&logo=python&logoColor=white" alt="Pygame">
  <img src="https://img.shields.io/badge/Stockfish-AI-orange?style=for-the-badge" alt="Stockfish">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License">
</p>

<h1 align="center">♟️ GrandMaster Chess</h1>

<p align="center">
  <b>Python & Pygame ile geliştirilmiş, Stockfish destekli çevrimdışı satranç oyunu.</b><br>
  <i>5 farklı zorluk seviyesi • 10 süre kontrolü • 15 bulmaca • Chess.com tarzı arayüz</i>
</p>

---

## ✨ Özellikler

| Özellik | Açıklama |
|---|---|
| 🤖 **Yapay Zeka** | Stockfish motoru ile 5 zorluk seviyesi (Kolay → Nakamura) |
| ⏱️ **Süre Kontrolü** | Bullet, Blitz ve Rapid dahil 10 farklı zaman ayarı |
| 🧩 **Bulmaca Modu** | Mat, taktik ve pozisyonel temalar içeren 15 bulmaca |
| 🎨 **Modern Arayüz** | Chess.com'dan ilham alan renk paleti ve tasarım |
| 📊 **Değerlendirme Çubuğu** | Canlı pozisyon değerlendirmesi (eval bar) |
| 💡 **İpucu Sistemi** | Sıkıştığınızda Stockfish'ten en iyi hamle önerisi |
| 🔊 **Ses Efektleri** | Taş oynatma, yeme, şah, rok ve terfi sesleri |
| 🏳️ **Oyun Kontrolleri** | Hamle geri alma, teslim olma, ok çizme |
| 🏆 **Taş Yakalama** | Yenen taşların ve materyal avantajının gösterimi |
| ↕️ **Tahta Çevirme** | Beyaz veya siyah taraftan oynama seçeneği |

## 📸 Ekran Görüntüleri

>
> ```md

> <img width="1257" height="901" alt="1" src="https://github.com/user-attachments/assets/251c314a-f022-401c-97bd-1eb3e3a69746" />

> <img width="1275" height="898" alt="2" src="https://github.com/user-attachments/assets/fc823d2d-f713-4c9a-a3fa-7626dd136430" />

> ```

## 🚀 Kurulum

### Gereksinimler

- **Python 3.8+**
- **Stockfish** satranç motoru (yapay zekaya karşı oynamak için)

### Adımlar

```bash
# 1. Depoyu klonlayın
git clone https://github.com/egnake/chess.git
cd chess

# 2. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 3. Stockfish motorunu indirin (isteğe bağlı, bot modu için gerekli)
#    https://stockfishchess.org/download/ adresinden indirip
#    proje dizinine "stockfish-windows-x86-64-avx2.exe" adıyla koyun.

# 4. Oyunu başlatın
python satranc.py
```

> [!NOTE]
> Stockfish motoru olmadan da **Bulmaca Modu**'nu oynayabilirsiniz.
> Bot modunda Stockfish bulunamazsa program uyarı verecektir.

## 🎮 Nasıl Oynanır

| Eylem | Kontrol |
|---|---|
| Taş seçme / bırakma | Sol tık veya sürükle-bırak |
| Ok çizme | Sağ tık + sürükle |
| Kare işaretleme | Sağ tık |
| İşaretleri temizleme | Sol tık (boş kareye) |

### Zorluk Seviyeleri

| Seviye | Stockfish Depth | Hedef Oyuncu |
|---|---|---|
| Kolay | 1 | Yeni başlayanlar |
| Orta | 5 | Amatör oyuncular |
| Zor | 10 | Orta düzey oyuncular |
| Usta | 15 | İleri düzey oyuncular |
| Nakamura | 20 | En üst seviye deneyim |

## 📁 Proje Yapısı

```
chess/
├── satranc.py              # Ana uygulama (oyun motoru + arayüz)
├── moduller/
│   └── bulmacalar.py       # Satranç bulmacaları koleksiyonu
├── taslar/                 # Taş görselleri (PNG)
│   ├── beyaz_*.png
│   └── siyah_*.png
├── sesler/                 # Ses efektleri (MP3)
│   ├── capture.mp3
│   ├── castle.mp3
│   ├── move-check.mp3
│   ├── game-end.mp3
│   └── promote.mp3
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## 🛠️ Kullanılan Teknolojiler

- **[Python](https://www.python.org/)** — Ana programlama dili
- **[Pygame](https://www.pygame.org/)** — Grafik ve ses motoru
- **[python-chess](https://python-chess.readthedocs.io/)** — Satranç kuralları ve motor iletişimi
- **[Stockfish](https://stockfishchess.org/)** — Yapay zeka satranç motoru

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.

## 👤 Geliştirici

**EGNAKE**

---

<p align="center">
  <i>⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!</i>
</p>
