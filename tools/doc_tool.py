import os
import requests

OCR_API_URL = "http://127.0.0.1:8001/extract/file"


def extract_text_from_docker(file_path, docker_url=OCR_API_URL):
    """
    Docker sunucusuna dosyayı gönderir ve metni UTF-8 olarak alır.
    """
    try:
        if not os.path.exists(file_path):
            return "Hata: Dosya bulunamadı."

        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            data = {"ocr": "true", "lang": "tur"}

            response = requests.post(docker_url, files=files, data=data, timeout=30)

            response.encoding = 'utf-8'

            response.raise_for_status()

            result = response.json()
            text_content = result.get("text", "")

            # Metni temizle ve döndür
            return text_content.strip()

    except requests.exceptions.ConnectionError:
        return "Docker OCR hatası: Sunucuya bağlanılamadı. Docker Desktop'ı kontrol edin."
    except Exception as e:
        return f"Docker OCR hatası: {str(e)}"


def extract_text_from_any_file(dosya_yolu: str) -> str:
    """
    Gelen dosyayı türüne göre işler.
    - TXT dosyaları: Doğrudan okunur
    - Diğer tüm dosyalar (PDF, Excel, DOCX, PNG, JPG, JPEG vs.): Docker OCR kullanılır
    """
    if not os.path.exists(dosya_yolu):
        return "Hata: Dosya yolu geçersiz."

    ext = os.path.splitext(dosya_yolu)[1].lower()

    # TXT dosyaları için UTF-8 okuma
    if ext == ".txt":
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            return f.read()

    # Tüm diğer dosyalar (PDF, Excel, Görsel vs.) için Docker OCR'a gönder
    content = extract_text_from_docker(dosya_yolu)

    if content:
        return f"BELGE İÇERİĞİ ({os.path.basename(dosya_yolu)}):\n\n{content}"
    return "Belge işlendi ancak metin bulunamadı."

