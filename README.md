# GrandMaster Chess

Python ve Pygame kullanılarak geliştirilmiş çevrimdışı bir satranç oyunu.
Stockfish botuna karşı oynayabilir, zorluk seviyesi ve süre ayarlayabilir veya içinde bulunan yüzlerce satranç bulmacasını çözebilirsiniz.

## Kurulum ve Çalıştırma

1. Bilgisayarınızda Python yüklü olduğundan emin olun.
2. Gerekli kütüphaneleri yüklemek için terminalde/CMD'de projeye gelin ve şunu yazın:
   ```bash
   pip install -r requirements.txt
   ```
3. Pygame ve python-chess kütüphaneleri yüklendikten sonra oyunu başlatmak için:
   ```bash
   python satranc.py
   ```

## Not
Bilgisayara karşı oynayabilmek için projenin ana dizininde **Stockfish** satranç motoruna (Örnek: `stockfish-windows-x86-64-avx2.exe`) ihtiyacınız vardır. GitHub deposunu şişirmemek amacıyla bu dosya bilerek yüklenmemiştir ve `.gitignore` dosyasına eklenmiştir. Bilgisayara karşı oynamak istiyorsanız [Stockfish'in resmi sitesinden](https://stockfishchess.org/download/) indirip adını yukarıdaki gibi yaparak (veya `satranc.py` içindeki adını değiştirerek) dizine çıkarmanız gerekir. Bulmaca modunu oynamak için motora ihtiyaç yoktur.
