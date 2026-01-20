import sqlite3
import os

# Scriptin bulunduğu klasörü (db klasörünü) tam yol olarak alalım
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Veritabanı dosyasını bu klasörün içine koyalım
DB_PATH = os.path.join(BASE_DIR, "accounting.db")


def update_and_create_db():
    # Klasörün var olduğundan emin olalım (Genelde zaten vardır ama garanti olsun)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print(f"📂 Veritabanı yolu: {DB_PATH}")

        # --- 1. MEVCUT TABLOLARI GÜNCELLEME (Sütun Ekleme) ---
        try:
            cursor.execute("ALTER TABLE mukellefler ADD COLUMN adres TEXT")
            print("✅ 'mukellefler' tablosuna 'adres' sütunu eklendi.")
        except sqlite3.OperationalError:
            print("ℹ️ 'adres' sütunu zaten mevcut, atlanıyor.")

        # --- 2. YENİ TABLOLARI OLUŞTURMA ---

        # Beyannameler
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS beyannameler
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           mukellef_id
                           INTEGER,
                           beyanname_turu
                           TEXT,
                           donem
                           TEXT,
                           verilme_tarihi
                           TEXT,
                           tahakkuk_no
                           TEXT,
                           durum
                           TEXT
                           DEFAULT
                           'Onaylandı',
                           FOREIGN
                           KEY
                       (
                           mukellef_id
                       ) REFERENCES mukellefler
                       (
                           id
                       )
                           )
                       """)

        # Sicil Gazetesi
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS sicil_gazetesi
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           mukellef_id
                           INTEGER,
                           tarih
                           TEXT,
                           sayi
                           TEXT,
                           konu
                           TEXT,
                           aciklama
                           TEXT,
                           FOREIGN
                           KEY
                       (
                           mukellef_id
                       ) REFERENCES mukellefler
                       (
                           id
                       )
                           )
                       """)

        # Diğer tabloları da IF NOT EXISTS ile garantiye alalım
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS banka_hesaplari (id INTEGER PRIMARY KEY AUTOINCREMENT, mukellef_id INTEGER, banka_adi TEXT, iban TEXT, hesap_tipi TEXT, FOREIGN KEY (mukellef_id) REFERENCES mukellefler(id))")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS vergiler (id INTEGER PRIMARY KEY AUTOINCREMENT, mukellef_id INTEGER, vergi_turu TEXT, donem TEXT, borc_tutari REAL, durum TEXT CHECK(durum IN ('odendi', 'odenmedi')), FOREIGN KEY (mukellef_id) REFERENCES mukellefler(id))")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS odemeler (id INTEGER PRIMARY KEY AUTOINCREMENT, vergi_id INTEGER, odeme_tarihi TEXT, tutar REAL, FOREIGN KEY (vergi_id) REFERENCES vergiler(id))")

        conn.commit()
        conn.close()
        print("🚀 Veritabanı başarıyla güncellendi.")

    except sqlite3.Error as e:
        print(f"❌ Veritabanı hatası: {e}")


if __name__ == "__main__":
    update_and_create_db()