import sqlite3

DB_PATH = "db/accounting.db"

def get_banka_hesaplari(mukellef_unvani: str):
    print("get_banka_hesaplari")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT b.banka_adi, b.iban, b.hesap_tipi
    FROM banka_hesaplari b
    JOIN mukellefler m ON m.id = b.mukellef_id
    WHERE LOWER(m.unvan) LIKE ?
    """

    cursor.execute(query, (f"%{mukellef_unvani.lower()}%",))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "Bu mükellefe ait banka hesabı bulunamadı."

    result = []
    for banka_adi, iban, hesap_tipi in rows:
        result.append(f"- {banka_adi} | {hesap_tipi} | {iban}")

    return "\n".join(result)

def get_vergi_borclari(mukellef_unvani: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("vergi_borclari")
    query = """
    SELECT v.vergi_turu, v.donem, v.borc_tutari, v.durum
    FROM vergiler v
    JOIN mukellefler m ON m.id = v.mukellef_id
    WHERE LOWER(m.unvan) LIKE ?
    """

    cursor.execute(query, (f"%{mukellef_unvani.lower()}%",))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "Bu mükellefe ait vergi kaydı bulunamadı."

    result = ["Vergi durumu:"]
    for tur, donem, borc, durum in rows:
        result.append(f"- {tur} | {donem} | {borc} TL | {durum}")

    return "\n".join(result)

def get_mukellefler():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT unvan, vergi_no, vergi_dairesi, tip, id
    FROM mukellefler
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "Kayıtlı mükellef bulunamadı."

    result = ["Kayıtlı Mükellefler:"]
    for unvan, vergi_no, vergi_dairesi, tip, id_ in rows:
        # use a local variable name id_ to avoid shadowing built-in id
        result.append(f"- {unvan} | Vergi No: {vergi_no} | Vergi Dairesi: {vergi_dairesi} | Tip: {tip}, ID: {id_}")

    return "\n".join(result)

def _normalize_tr(s: str) -> str:
    # Normalize common Turkish characters for case-insensitive matching
    if s is None:
        return ""
    return s.lower().replace('ı', 'i').replace('ç', 'c').replace('ş', 's').replace('ü', 'u').replace('ö', 'o').replace('ğ', 'g').strip()

def get_odemeler(mukellef_unvani: str):
    """Return payments for a given mukellef.
    Accepts either a numeric mukellef id (as string or int) or a company name (unvan).
    If an empty string is provided, behaves like a wildcard and returns all payments.

    Matching on company names is performed using a normalized comparison to handle Turkish characters reliably.
    Token-based matching is used so short queries like 'aydınlık firması' will match 'Aydınlık Tekstil'.
    If no payments exist, fall back to listing related tax records (vergiler) so the user sees relevant debt info.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Normalize input
    if mukellef_unvani is None:
        mukellef_unvani = ""
    mukellef_raw = str(mukellef_unvani).strip()

    searched_by_id = False

    # If the user supplied a numeric id, query by id for exact matches
    if mukellef_raw.isdigit():
        searched_by_id = True
        cursor.execute("SELECT o.odeme_tarihi, o.tutar FROM odemeler o JOIN vergiler v ON v.id = o.vergi_id JOIN mukellefler m ON m.id = v.mukellef_id WHERE m.id = ?", (int(mukellef_raw),))
        rows = cursor.fetchall()
    else:
        # Perform normalized unvan matching in Python to handle Turkish characters reliably
        norm_search = _normalize_tr(mukellef_raw)
        tokens = [t for t in norm_search.split() if len(t) >= 2]
        cursor.execute("SELECT id, unvan FROM mukellefler")
        mukellef_rows = cursor.fetchall()
        matched_ids = []
        for mid, unvan in mukellef_rows:
            if norm_search == "":
                matched_ids.append(mid)
                continue
            u_norm = _normalize_tr(unvan)
            matched_flag = False
            # exact substring match first
            if norm_search in u_norm:
                matched_flag = True
            else:
                # token-based partial matching
                for tok in tokens:
                    if tok in u_norm:
                        matched_flag = True
                        break
            if matched_flag:
                matched_ids.append(mid)

        rows = []
        if matched_ids:
            placeholders = ",".join(["?"] * len(matched_ids))
            sql = f"SELECT o.odeme_tarihi, o.tutar FROM odemeler o JOIN vergiler v ON v.id = o.vergi_id WHERE v.mukellef_id IN ({placeholders})"
            cursor.execute(sql, tuple(matched_ids))
            rows = cursor.fetchall()
        else:
            # no matched IDs; early set rows to empty so fallback will trigger
            rows = []

    # If no payments found, try to surface related tax records so the user can see outstanding debts
    if not rows:
        if searched_by_id:
            cursor.execute("SELECT vergi_turu, donem, borc_tutari, durum FROM vergiler WHERE mukellef_id = ?", (int(mukellef_raw),))
        else:
            # If we had matched mukellef ids, use those to retrieve vergiler; otherwise try normalized name join
            if 'matched_ids' in locals() and matched_ids:
                placeholders = ",".join(["?"] * len(matched_ids))
                sql = f"SELECT vergi_turu, donem, borc_tutari, durum FROM vergiler WHERE mukellef_id IN ({placeholders})"
                cursor.execute(sql, tuple(matched_ids))
            else:
                cursor.execute("SELECT v.vergi_turu, v.donem, v.borc_tutari, v.durum FROM vergiler v JOIN mukellefler m ON m.id = v.mukellef_id WHERE LOWER(m.unvan) LIKE ?", (f"%{mukellef_raw.lower()}%",))
        vergiler = cursor.fetchall()
        conn.close()

        if not vergiler:
            return "Bu mükellefe ait ödeme kaydı bulunamadı."

        result = ["Ödeme kaydı bulunamadı — ilgili vergi kayıtları:"]
        for tur, donem, borc, durum in vergiler:
            result.append(f"- {tur} | {donem} | {borc} TL | {durum}")
        return "\n".join(result)

    conn.close()
    result = ["Ödeme Geçmişi:"]
    for odeme_tarihi, tutar in rows:
        result.append(f"- {odeme_tarihi} | {tutar} TL")
    return "\n".join(result)


import re

def clean_company_name(name: str) -> str:
    name = name.lower()
    # Sadece yasal takıları temizle, sektörel kelimeleri (yazılım vb.) bırak
    noise_words = ["firması", "şirketi", "limited", "ltd", "şti", "anonim", "as", "a.ş", "şirket"]
    for word in noise_words:
        name = name.replace(word, "")
    return name.strip()


def get_mukellef_detay(mukellef_unvani: str):
    """Mükellefin tüm detaylarını (dilekçe için) getirir.
    Turkish character support and token matching added.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Girişi normalize et (i-ı, ş-s gibi dönüşümler)
    norm_search = _normalize_tr(mukellef_unvani)
    # Gürültü kelimeleri temizle (teknoloji, yazılım, ltd vb.)
    clean_search = clean_company_name(norm_search)

    # 2. Kelimelere böl (Örn: ["ozkan", "yazilim"])
    tokens = [t for t in clean_search.split() if len(t) >= 2]

    # 3. Tüm mükellefleri çek ve Python tarafında eşleştir (En güvenli yol)
    cursor.execute("SELECT id, unvan, vergi_no, vergi_dairesi, tip, adres FROM mukellefler")
    all_rows = cursor.fetchall()

    matched_row = None

    for row in all_rows:
        db_unvan_norm = _normalize_tr(row[1])

        # Tam eşleşme var mı?
        if clean_search in db_unvan_norm:
            matched_row = row
            break

        # Token bazlı eşleşme (Kelimelerin en az yarısı tutuyorsa)
        match_count = sum(1 for tok in tokens if tok in db_unvan_norm)
        if tokens and match_count >= (len(tokens) / 2):
            matched_row = row
            break

    conn.close()

    if matched_row:
        return {
            "unvan": matched_row[1],
            "vergi_no": matched_row[2],
            "vergi_dairesi": matched_row[3],
            "tip": matched_row[4],
            "adres": matched_row[5]
        }

    return "Mükellef bulunamadı. Lütfen listeden kontrol edin veya unvanı değiştirin."
def get_beyannameler(mukellef_unvani: str):
    """Bir mükellefin verilmiş olan beyannamelerini listeler."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    norm_search = _normalize_tr(mukellef_unvani)

    query = """
    SELECT b.beyanname_turu, b.donem, b.verilme_tarihi, b.tahakkuk_no, b.durum
    FROM beyannameler b
    JOIN mukellefler m ON m.id = b.mukellef_id
    WHERE LOWER(m.unvan) LIKE ?
    """
    cursor.execute(query, (f"%{norm_search}%",))
    rows = cursor.fetchall()
    conn.close()

    if not rows: return "Beyanname kaydı bulunamadı."

    result = ["Verilen Beyannameler:"]
    for tur, donem, tarih, no, durum in rows:
        result.append(f"- {tur} | Dönem: {donem} | Tarih: {tarih} | Tahakkuk No: {no} ({durum})")
    return "\n".join(result)

def get_sicil_kayitlari(mukellef_unvani: str):
    """Mükellefin ticaret sicil gazetesi geçmişini (kuruluş, adres değişikliği vb.) getirir."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    norm_search = _normalize_tr(mukellef_unvani)

    query = """
    SELECT s.tarih, s.sayi, s.konu, s.aciklama
    FROM sicil_gazetesi s
    JOIN mukellefler m ON m.id = s.mukellef_id
    WHERE LOWER(m.unvan) LIKE ?
    """
    cursor.execute(query, (f"%{norm_search}%",))
    rows = cursor.fetchall()
    conn.close()

    if not rows: return "Sicil gazetesi kaydı bulunamadı."

    result = ["Ticaret Sicil Kayıtları:"]
    for tarih, sayi, konu, aciklama in rows:
        result.append(f"📅 {tarih} | Sayı: {sayi} | Konu: {konu}\n   Açıklama: {aciklama}")
    return "\n".join(result)


def get_tum_borclu_mukellefler():
    """Veritabanındaki tüm mükellefleri tarar ve sadece borcu olanları listeler."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
            SELECT m.unvan, v.vergi_turu, v.borc_tutari, v.donem
            FROM vergiler v
                     JOIN mukellefler m ON m.id = v.mukellef_id
            WHERE v.durum = 'odenmedi' \
            """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "Şu anda borcu olan herhangi bir mükellef bulunmamaktadır."

    result = ["⚠️ Borcu Bulunan Mükellefler:"]
    for unvan, tur, borc, donem in rows:
        result.append(f"- {unvan}: {donem} dönemi {tur} borcu {borc} TL")
    return "\n".join(result)

