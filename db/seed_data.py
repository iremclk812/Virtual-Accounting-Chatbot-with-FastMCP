import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "accounting.db")


def seed_data():
    if not os.path.exists(DB_PATH):
        print(f"❌ Hata: {DB_PATH} bulunamadı!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print(f"🧹 Eski veriler temizleniyor...")
        cursor.execute("DELETE FROM odemeler")
        cursor.execute("DELETE FROM vergiler")
        cursor.execute("DELETE FROM banka_hesaplari")
        cursor.execute("DELETE FROM beyannameler")
        cursor.execute("DELETE FROM sicil_gazetesi")
        cursor.execute("DELETE FROM mukellefler")
        # ID counter'ları sıfırla
        cursor.execute(
            "DELETE FROM sqlite_sequence WHERE name IN ('mukellefler', 'vergiler', 'banka_hesaplari', 'beyannameler', 'sicil_gazetesi', 'odemeler')")

        print(f"🏗️ Yeni mükellefler ve veriler oluşturuluyor...")

        # --- MÜKELLEF LİSTESİ ---
        mukellefler = [
            ('Aydınlık Tekstil Sanayi ve Ticaret Ltd. Şti.', '1234567890', 'Kadıköy', 'Atatürk Mah. No:45 Kadıköy/İst',
             'sirket'),
            ('Demir İnşaat Yapı Malzemeleri A.Ş.', '9876543210', 'Beşiktaş', 'Levent Plaza K:12 Beşiktaş/İst',
             'sirket'),
            ('Özkan Yazılım ve Danışmanlık - Ahmet Özkan', '1112223334', 'Çankaya', 'Kızılay Sok. No:10 Çankaya/Ankara',
             'sahis'),
            ('Güneş Restoran Hizmetleri Ltd. Şti.', '5556667778', 'Konak', 'Kordon Boyu No:102 Konak/İzmir', 'sirket')
        ]

        for unvan, v_no, v_daire, adres, tip in mukellefler:
            cursor.execute("""
                           INSERT INTO mukellefler (unvan, vergi_no, vergi_dairesi, adres, tip)
                           VALUES (?, ?, ?, ?, ?)
                           """, (unvan, v_no, v_daire, adres, tip))
            m_id = cursor.lastrowid

            # --- HER MÜKELLEFE ÖZEL VERİLER ---

            # 1. Banka Hesapları
            if tip == 'sirket':
                cursor.execute(
                    "INSERT INTO banka_hesaplari (mukellef_id, banka_adi, iban, hesap_tipi) VALUES (?, ?, ?, ?)",
                    (m_id, 'Ziraat Bankası', f'TR{m_id}0001', 'TL Ticari'))
                cursor.execute(
                    "INSERT INTO banka_hesaplari (mukellef_id, banka_adi, iban, hesap_tipi) VALUES (?, ?, ?, ?)",
                    (m_id, 'Garanti BBVA', f'TR{m_id}0002', 'USD Döviz'))
            else:
                cursor.execute(
                    "INSERT INTO banka_hesaplari (mukellef_id, banka_adi, iban, hesap_tipi) VALUES (?, ?, ?, ?)",
                    (m_id, 'İş Bankası', f'TR{m_id}0003', 'Şahıs Hesabı'))

            # 2. Vergi Tahakkukları ve Ödemeler
            # Herkese bir KDV borcu ekle (Biri ödenmiş, biri ödenmemiş olsun)
            durum = 'odendi' if m_id % 2 == 0 else 'odenmedi'
            tutar = 5000 * m_id
            cursor.execute("""
                           INSERT INTO vergiler (mukellef_id, vergi_turu, donem, borc_tutari, durum)
                           VALUES (?, ?, ?, ?, ?)
                           """, (m_id, 'KDV', '2024-11', tutar, durum))
            v_id = cursor.lastrowid

            if durum == 'odendi':
                cursor.execute("INSERT INTO odemeler (vergi_id, odeme_tarihi, tutar) VALUES (?, ?, ?)",
                               (v_id, '2024-12-20', tutar))

            # 3. Beyannameler
            cursor.execute("""
                           INSERT INTO beyannameler (mukellef_id, beyanname_turu, donem, verilme_tarihi, tahakkuk_no)
                           VALUES (?, 'KDV-1', '2024-11', '2024-12-24', ?)
                           """, (m_id, f'T-BYN-{m_id}00'))

            # 4. Sicil Gazetesi Kayıtları
            cursor.execute("""
                           INSERT INTO sicil_gazetesi (mukellef_id, tarih, sayi, konu, aciklama)
                           VALUES (?, '2023-01-10', ?, 'Kuruluş', 'Firma resmi olarak faaliyetine başlamıştır.')
                           """, (m_id, f'SG-{m_id}01'))

            if m_id == 1:  # Sadece Aydınlık Tekstil'e ekstra bir kayıt
                cursor.execute("""
                               INSERT INTO sicil_gazetesi (mukellef_id, tarih, sayi, konu, aciklama)
                               VALUES (?, '2024-05-20', '11200', 'Adres Değişikliği',
                                       'Eski adres Beşiktaştan Kadıköye taşınmıştır.')
                               """, (m_id,))

        conn.commit()
        print(f"✅ Başarıyla {len(mukellefler)} mükellef ve ilişkili tüm veriler eklendi.")

    except sqlite3.Error as e:
        print(f"❌ Hata oluştu: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    seed_data()