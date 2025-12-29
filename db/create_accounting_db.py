import sqlite3

DB_NAME = "accounting.db"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mukellefler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unvan TEXT NOT NULL,
        vergi_no TEXT UNIQUE,
        vergi_dairesi TEXT,
        tip TEXT CHECK(tip IN ('sahis', 'sirket')),
        aktif INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS banka_hesaplari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mukellef_id INTEGER,
        banka_adi TEXT,
        iban TEXT,
        hesap_tipi TEXT,
        FOREIGN KEY (mukellef_id) REFERENCES mukellefler(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vergiler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mukellef_id INTEGER,
        vergi_turu TEXT,
        donem TEXT,
        borc_tutari REAL,
        durum TEXT CHECK(durum IN ('odendi', 'odenmedi')),
        FOREIGN KEY (mukellef_id) REFERENCES mukellefler(id)
    )
    """)

    # 4️⃣ Ödemeler
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS odemeler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vergi_id INTEGER,
        odeme_tarihi TEXT,
        tutar REAL,
        FOREIGN KEY (vergi_id) REFERENCES vergiler(id)
    )
    """)

    conn.commit()
    conn.close()
    print("✅ accounting.db başarıyla oluşturuldu.")

if __name__ == "__main__":
    create_db()
