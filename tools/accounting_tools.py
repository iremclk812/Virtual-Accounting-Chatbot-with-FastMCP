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
    """Kullanıcının girdiği isimden 'firması, şirketi, ltd' gibi kelimeleri temizler."""
    name = name.lower()
    noise_words = ["firması", "şirketi", "limited", "ltd", "şti", "anonim", "as", "a.ş", "şirket"]
    for word in noise_words:
        name = name.replace(word, "")
    return name.strip()


def get_mukellef_detay(mukellef_unvani: str):
    """Mükellefin tüm detaylarını (dilekçe için) getirir."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Esnek arama için ismi temizle
    clean_name = clean_company_name(mukellef_unvani)

    query = """
            SELECT unvan, vergi_no, vergi_dairesi, tip, adres
            FROM mukellefler
            WHERE LOWER(unvan) LIKE ? \
            """
    cursor.execute(query, (f"%{clean_name}%",))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "unvan": row[0],
            "vergi_no": row[1],
            "vergi_dairesi": row[2],
            "tip": row[3],
            "adres": row[4]  # DB'de adres sütunu olduğunu varsayıyoruz
        }
    return "Mükellef bulunamadı."

