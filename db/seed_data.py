import sqlite3

conn = sqlite3.connect("accounting.db")
cursor = conn.cursor()
cursor.execute("""
INSERT INTO mukellefler (unvan, vergi_no, vergi_dairesi, tip)
VALUES ('Aydınlık Tekstil', '1234567890', 'Kadıköy', 'sirket')
""")

cursor.execute("""
INSERT INTO banka_hesaplari (mukellef_id, banka_adi, iban, hesap_tipi)
VALUES (1, 'Ziraat Bankası', 'TR000000000000000000000001', 'TL')
""")

cursor.execute("""
INSERT INTO vergiler (mukellef_id, vergi_turu, donem, borc_tutari, durum)
VALUES (1, 'KDV', '2024-12', 18500, 'odenmedi')
""")

cursor.execute("""
INSERT INTO odemeler (id,vergi_id,odeme_tarihi, tutar )
VALUES (1, 1, '2024-12-15', 18500)
""")
conn.commit()
conn.close()

print("✅ Örnek veriler eklendi.")
