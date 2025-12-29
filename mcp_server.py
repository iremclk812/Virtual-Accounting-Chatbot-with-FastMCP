from mcp.server.fastmcp import FastMCP
from tools.accounting_tools import (
    get_banka_hesaplari,
    get_vergi_borclari,
    get_mukellefler,
    get_odemeler, get_mukellef_detay,get_beyannameler,get_sicil_kayitlari,get_tum_borclu_mukellefler
)
from starlette.responses import HTMLResponse

mcp = FastMCP("Sanal Musavir MCP")


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
    """Tüm kayıtlı mükellefleri listeler."""
    return get_mukellefler()


@mcp.tool()
def odemeler(mukellef_unvani: str) -> str:
    """Bir mükellefin ödeme geçmişini getirir."""
    return get_odemeler(mukellef_unvani)
@mcp.tool()
def mukellef_detaylari(mukellef_unvani: str) -> str:
    """Bir mükellefin resmi dilekçelerde kullanılacak tam bilgilerini (Vergi No, Adres vb.) getirir."""
    data = get_mukellef_detay(mukellef_unvani)
    if isinstance(data, dict):
        return f"Tam Unvan: {data['unvan']}\nVergi No: {data['vergi_no']}\nVergi Dairesi: {data['vergi_dairesi']}\nAdres: {data['adres']}"

    return data
@mcp.tool()
def sicil_kayitlari(mukellef_unvani: str) -> str:
    """Mükellefin ticaret sicil gazetesi geçmişini (kuruluş, adres değişikliği vb.) getirir."""
    return get_sicil_kayitlari(mukellef_unvani)
@mcp.tool()
def beyannameler(mukellef_unvani: str) -> str:
    """Bir mükellefin verilmiş olan beyannamelerini listeler."""
    return get_beyannameler(mukellef_unvani)
@mcp.tool()
def tum_borclu_mukellefler() -> str:
    """Veritabanındaki tüm mükellefleri tarar ve sadece borcu olanları listeler."""
    return get_tum_borclu_mukellefler()


# Simple root HTML page for quick SSE/testing in a browser
@mcp.custom_route("/", methods=["GET"])
async def _root_index(request):
    html = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Sanal Müşavir - SSE Demo</title>
    <style>body{font-family: Arial, Helvetica, sans-serif; margin:20px;} pre{background:#f6f6f6;padding:10px;border-radius:6px}</style>
  </head>
  <body>
    <h2>Basit MCP SSE Demo</h2>
    <p>Bu sayfa yalnızca bağlantıyı test etmek içindir. Sunucu <code>/sse</code> endpoint'ine EventSource ile bağlanır.</p>
    <pre id="log">Bağlanıyor...\n</pre>
    <button id="btn" onclick="sendTest()">Test POST gönder</button>

    <script>
      const logEl = document.getElementById('log');
      function log(msg){ logEl.textContent += msg + '\n'; }

      // Connect to SSE
      const es = new EventSource('/sse');
      let postUrl = null;

      es.addEventListener('open', () => log('SSE açık'));
      es.addEventListener('error', (e) => log('SSE hata: ' + JSON.stringify(e)));

      es.addEventListener('endpoint', (e) => {
        postUrl = decodeURIComponent(e.data);
        log('POST endpoint alındı: ' + postUrl);
      });

      es.addEventListener('message', (e) => {
        // message event data is JSON-RPC payload from server
        log('SERVER MESSAGE: ' + e.data);
      });

      async function sendTest(){
        if(!postUrl){ alert('Henüz POST endpoint alınmadı. Birkaç saniye bekleyin ve sayfayı yenileyin.'); return; }
        try{
          // Basit JSON-RPC ping - server tarafında parse hatası olabilir; bu yalnızca demo amaçlıdır
          const body = JSON.stringify({jsonrpc: '2.0', method: 'ping', params: {}, id: 1});
          const resp = await fetch(postUrl, {method:'POST', headers:{'Content-Type':'application/json'}, body});
          const text = await resp.text();
          log('POST yanıtı: ' + resp.status + ' - ' + text);
        }catch(err){
          log('POST hata: ' + err);
        }
      }
    </script>
  </body>
</html>"""
    return HTMLResponse(html)


if __name__ == "__main__":
    mcp.run(transport="sse")
