from tools.accounting_tools import (
    get_banka_hesaplari,
    get_vergi_borclari,
    get_mukellefler,
    get_odemeler,
    get_mukellef_detay,
    clean_company_name,
)


TOOLS = {
    "get_vergi_borclari": {
        "function": get_vergi_borclari,
        "description": "Bir mükellefin vergi borçlarını getirir",
        "parameters": {
            "mukellef_unvani": "string"
        },
        "aliases": ["vergi", "vergi borcu", "vergi borçları", "borç", "borçları", "vergiler", "vergi durumu"]
    },
    "get_banka_hesaplari": {
        "function": get_banka_hesaplari,
        "description": "Bir mükellefin banka hesaplarını getirir",
        "parameters": {
            "mukellef_unvani": "string"
        },
        "aliases": ["banka", "banka hesap", "banka hesapları", "hesap", "hesaplar", "iban", "swift"]
    },
    "get_mukellefler": {
        "function": get_mukellefler,
        "description": "Tüm mükelleflerin listesini getirir",
        "parameters": {

        },
        "aliases": ["mükellefler", "mukellefler", "mükellef listesi", "mukellef listesi"]
    },
    "get_odemeler": {
        "function": get_odemeler,
        "description": "Bir mükellefin ödeme geçmişini getirir",
        "parameters": {
            "mukellef_unvani": "string"
        },
        "aliases": ["ödemeler", "odemeler", "ödeme geçmişi", "odeme gecmisi", "ödeme", "odeme"]
    },
    "clean_company_name": {
        "function": clean_company_name,
        "description": "Şirket unvanını temizler ve standart bir formata getirir",
        "parameters": {
            "name": "string"
        },
        "aliases": ["şirket adı temizle", "firma adı temizle", "şirket unvanı düzenle", "firma unvanı düzenle"]
    },
    "get_mukellef_detay": {
        "function": get_mukellef_detay,
        "description": "Mükellefin tüm detaylarını getirir",
        "parameters": {
            "mukellef_unvani": "string"
        },
    },
}
