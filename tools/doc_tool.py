import fitz # PDF için
import os
import pytesseract
from pdf2image import convert_from_path
import docx # .docx için
import shutil

# Mac Homebrew yolu
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

def extract_text_from_any_file(dosya_yolu: str) -> str:
    try:
        if not os.path.exists(dosya_yolu):
            return "Hata: Dosya bulunamadı."

        ext = os.path.splitext(dosya_yolu)[1].lower()
        content = ""

        # --- 1. PDF İŞLEME ---
        if ext == ".pdf":
            doc = fitz.open(dosya_yolu)
            content = "".join([page.get_text() for page in doc])
            doc.close()
            # Eğer boşsa OCR başlat
            if not content.strip() or len(content.strip()) < 50:
                images = convert_from_path(dosya_yolu, dpi=300)
                content = "".join([pytesseract.image_to_string(img, lang='tur') for img in images])

        # --- 2. DOCX İŞLEME ---
        elif ext == ".docx":
            doc = docx.Document(dosya_yolu)
            content = "\n".join([para.text for para in doc.paragraphs])

        # --- 3. DOC İŞLEME (Legacy) ---
        elif ext == ".doc":
            # .doc dosyaları moderndir ama kütüphanesi farklıdır.
            # En temiz yol 'textract' veya 'antiword' kullanmaktır.
            # Mac'te 'textutil' komutu yerleşiktir, onu kullanalım:
            content = os.popen(f"textutil -convert txt -stdout '{dosya_yolu}'").read()

        # --- 4. TXT İŞLEME ---
        elif ext == ".txt":
            with open(dosya_yolu, "r", encoding="utf-8") as f:
                content = f.read()

        else:
            return f"Desteklenmeyen dosya formatı: {ext}"

        if not content.strip():
            return "Dosya okundu ancak içerik boş."

        return f"BELGE İÇERİĞİ ({os.path.basename(dosya_yolu)}):\n\n{content}"

    except Exception as e:
        return f"Dosya işleme hatası: {str(e)}"