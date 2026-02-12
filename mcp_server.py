from mcp.server.fastmcp import FastMCP
from tools.doc_tool import extract_text_from_any_file
from tools.accounting_tools import (
    get_banka_hesaplari,
    get_vergi_borclari,
    get_mukellefler,
    get_odemeler,
    get_mukellef_detay,
    get_beyannameler,
    get_sicil_kayitlari,
    get_tum_borclu_mukellefler
)
from starlette.responses import HTMLResponse

# Sanal Müşavir MCP Sunucusu Başlatma
mcp = FastMCP("Sanal Musavir MCP")


# --- MUHASEBE VE MÜKELLEF ARAÇLARI ---

@mcp.tool()
def banka_hesaplari(mukellef_unvani: str) -> str:
    """Bir mükellefin banka hesaplarını listeler."""
    return get_banka_hesaplari(mukellef_unvani)


@mcp.tool()
def vergi_borclari(mukellef_unvani: str) -> str:
    """Bir mükellefin vergi borçlarını listeler."""
    return get_vergi_borclari(mukellef_unvani)


@mcp.tool()
def mukellefler() -> str:
    """Sistemde kayıtlı olan tüm mükellefleri listeler."""
    return get_mukellefler()


@mcp.tool()
def odemeler(mukellef_unvani: str) -> str:
    """Bir mükellefin geçmiş ödeme kayıtlarını getirir."""
    return get_odemeler(mukellef_unvani)


@mcp.tool()
def mukellef_detaylari(mukellef_unvani: str) -> str:
    """Mükellefin resmi dilekçelerde kullanılacak tam bilgilerini (Vergi No, Adres, Unvan) getirir."""
    data = get_mukellef_detay(mukellef_unvani)
    if isinstance(data, dict):
        return (f"Tam Unvan: {data['unvan']}\n"
                f"Vergi No: {data['vergi_no']}\n"
                f"Vergi Dairesi: {data['vergi_dairesi']}\n"
                f"Adres: {data['adres']}")
    return data


@mcp.tool()
def sicil_kayitlari(mukellef_unvani: str) -> str:
    """Mükellefin ticaret sicil gazetesi geçmişini (kuruluş, adres değişikliği, sermaye artırımı vb.) getirir."""
    return get_sicil_kayitlari(mukellef_unvani)


@mcp.tool()
def beyannameler(mukellef_unvani: str) -> str:
    """Bir mükellefin sisteme girilmiş olan beyannamelerini (KDV, Muhtasar vb.) listeler."""
    return get_beyannameler(mukellef_unvani)


@mcp.tool()
def tum_borclu_mukellefler() -> str:
    """Veritabanındaki tüm mükellefleri tarar ve sadece borcu olanları toplu olarak listeler."""
    return get_tum_borclu_mukellefler()


# --- BELGE ANALİZ ARACI ---

@mcp.tool()
def read_file(file_path: str) -> str:
    """
    Belirtilen yoldaki dosyayı okur.
    Desteklenen formatlar: PDF (OCR destekli), DOCX, DOC, TXT, PNG, JPG, JPEG.
    Belge içeriğini metin olarak döndürür.
    """
    return extract_text_from_any_file(file_path)



# --- TEST VE SSE İZLEME SAYFASI ---

@mcp.custom_route("/", methods=["GET"])
async def _root_index(request):
    html = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Sanal Müşavir - SSE Test Paneli</title>
    <style>
        body{font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin:40px; background-color: #f4f7f6;} 
        pre{background:#2d2d2d; color:#ccc; padding:15px; border-radius:8px; overflow-x: auto;}
        h2{color: #2c3e50;}
        .status{color: green; font-weight: bold;}
    </style>
  </head>
  <body>
    <h2>🚀 Sanal Müşavir MCP Sunucusu Aktif</h2>
    <p>Durum: <span class="status">Çalışıyor</span></p>
    <p>Sunucu <code>/sse</code> endpoint'i üzerinden EventSource bağlantılarını kabul etmektedir.</p>
    <pre id="log">Bağlantı bekleniyor...\n</pre>

    <script>
      const logEl = document.getElementById('log');
      function log(msg){ logEl.textContent += msg + '\\n'; }

      const es = new EventSource('/sse');

      es.addEventListener('open', () => log('✅ SSE Bağlantısı Başarıyla Açıldı.'));
      es.addEventListener('error', (e) => log('❌ SSE Hatası: Sunucu kapalı olabilir.'));

      es.addEventListener('endpoint', (e) => {
        log('🔗 Mesaj Endpointi: ' + decodeURIComponent(e.data));
      });

      es.addEventListener('message', (e) => {
        log('📩 GELEN MESAJ: ' + e.data);
      });
    </script>
  </body>
</html>"""
    return HTMLResponse(html)


if __name__ == "__main__":
    # Sunucuyu SSE transportu ile başlat
    mcp.run(transport="sse")