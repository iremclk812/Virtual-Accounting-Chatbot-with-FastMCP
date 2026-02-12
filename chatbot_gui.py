import streamlit as st
import asyncio
import os
import requests
from client.mcp_client import MCPToolClient
from client.ollama import chat_with_llm, chat_with_llm_stream, SYSTEM_PROMPT

# --- 1. KONFİGÜRASYON ---
MCP_SERVER_URL = "http://127.0.0.1:8000/sse"
OCR_API_URL = "http://127.0.0.1:8001/extract/file"  # Port 8001
temp_dir = "temp_uploads"
os.makedirs(temp_dir, exist_ok=True)

st.set_page_config(page_title="Sanal Müşavir AI", page_icon="💼", layout="centered")

# --- 2. CSS (MİNİMALİST CHATGPT STİLİ) ---
st.markdown("""
    <style>
    .stMainBlockContainer { max-width: 740px !important; }
    div[data-testid="stChatInput"] textarea { padding-left: 45px !important; }
    div[data-testid="stPopover"] {
        position: fixed; bottom: 53px; left: 50%;
        transform: translateX(-355px); z-index: 1000001; width: 30px !important;
    }
    div[data-testid="stPopover"] > button {
        background-color: transparent !important; border: none !important;
        color: #8e8ea0 !important; width: 28px !important; height: 28px !important;
        display: flex; align-items: center; justify-content: center;
    }
    div[data-testid="stPopover"] > button p { font-size: 18px !important; margin: 0px !important; }
    div[data-testid="stPopover"] svg[data-testid="stIcon"] { display: none !important; }
    div[data-testid="stPopover"] > button:hover { color: #ffffff !important; }
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stPopover"]) {
        height: 0px !important; margin: 0px !important; padding: 0px !important; pointer-events: none;
    }
    div[data-testid="stPopover"] { pointer-events: auto; }
    @media (max-width: 740px) { div[data-testid="stPopover"] { left: 15px; transform: none; } }
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE (HAFIZA YÖNETİMİ) ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

if "mcp_client" not in st.session_state:
    st.session_state.mcp_client = MCPToolClient(MCP_SERVER_URL)

# Docker'dan gelen metni hafızada tutmak için yeni state'ler
if "pending_file_text" not in st.session_state:
   st.session_state.pending_file_text = ""
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None


# --- 4. YARDIMCI FONKSİYONLAR ---

def extract_text_via_ocr(file_path):
    """
    Tüm dosya türleri için Docker OCR API kullanır.
    """
    try:
        with open(file_path, "rb") as f:
            files = f.read()
            response = requests.post(OCR_API_URL, files={"file": (os.path.basename(file_path), files)}, timeout=30)
            response.encoding = 'utf-8'
            response.raise_for_status()
            return response.json().get("text", "")
    except Exception as e:
        return f"OCR Hatası: {str(e)}"


async def get_tools_from_server():
    try:
        mcp = st.session_state.mcp_client
        tools = await mcp.list_tools()
        return [{"type": "function",
                 "function": {"name": t.name, "description": t.description, "parameters": t.inputSchema}} for t in
                tools]
    except:
        return []


async def process_interaction(user_input):
    # Dosya içeriği varsa kontrol et
    has_file_content = bool(st.session_state.pending_file_text)

    if has_file_content:

        tools_schema = []
        temp_messages = st.session_state.messages.copy()
        temp_messages.append({
            "role": "user",
            "content": f"{user_input}\n\n[SİSTEM NOTU: Kullanıcı bir dosya yükledi: '{st.session_state.last_uploaded_file}'. SADECE BU DOSYA İÇERİĞİNİ ANALİZ ET, veritabanını sorgulama!\n\nDosya İçeriği:\n{st.session_state.pending_file_text}]"
        })

        # LLM çağrısı (dosya içeriğiyle)
        with st.spinner("Dosya analiz ediliyor..."):
            response_msg = chat_with_llm(temp_messages, tools_schema)

        st.session_state.messages.append({"role": "user", "content": user_input})

        # ÖNEMLİ: Dosya modunu HEMEN kapat (bir sonraki soruda normal mod olsun)
        st.session_state.pending_file_text = ""
        st.session_state.last_uploaded_file = None
    else:
        # NORMAL MOD: Tool'ları kullanabilir (veritabanı sorguları)
        # Kullanıcı mesajını hafızaya ekle
        st.session_state.messages.append({"role": "user", "content": user_input})

        tools_schema = await get_tools_from_server()

        # Normal LLM çağrısı
        with st.spinner("Düşünüyor..."):
            response_msg = chat_with_llm(st.session_state.messages, tools_schema)

    # Tool çağrısı varsa işle
    if response_msg.get("tool_calls"):
        st.session_state.messages.append(response_msg)

        for tool_call in response_msg["tool_calls"]:
            t_name = tool_call["function"]["name"]
            t_args = tool_call["function"]["arguments"]

            with st.status(f"🛠️ {t_name}...", expanded=False) as status:
                try:
                    result = await st.session_state.mcp_client.run_tool(t_name, t_args)
                    st.write(f"✅ Sonuç alındı ({len(result)} karakter)")
                    status.update(label=f"✅ {t_name} tamamlandı", state="complete")
                except Exception as e:
                    result = f"Tool hatası: {str(e)}"
                    st.error(result)
                    status.update(label=f"❌ {t_name} başarısız", state="error")

            st.session_state.messages.append({
                "role": "tool",
                "content": result,
                "name": t_name
            })

        # Tool sonuçlarıyla final cevap al
        with st.spinner("Cevap hazırlanıyor..."):
            final_response = chat_with_llm(st.session_state.messages, tools_schema)

        st.session_state.messages.append(final_response)

        def gen():
            content = final_response.get('content', '')
            yield content if content else "Cevap oluşturulamadı."

        return gen()

    # Tool çağrısı yoksa direkt cevap ver
    st.session_state.messages.append(response_msg)

    def gen():
        content = response_msg.get('content', '')
        if content:
            yield content
        else:
            for chunk in chat_with_llm_stream(st.session_state.messages):
                yield chunk.get('message', {}).get('content', '')

    return gen()


# --- 5. ARAYÜZ (CHAT) ---
st.title("💼 Sanal Müşavir Asistanı")
st.caption("Vergi, Banka ve Belge Analizi (Docker OCR Destekli)")

for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"] and "content" in msg:
        clean_content = msg["content"].split("\n\n[SİSTEM NOTU:")[0]
        with st.chat_message(msg["role"]):
            st.markdown(clean_content)

# --- 6. GİRİŞ ALANI (ATAÇ VE BAR) ---
with st.popover("📎"):
    u_file = st.file_uploader("Belge Yükle", type=["pdf", "docx", "png", "jpg", "jpeg"], label_visibility="collapsed")
    if u_file:
        file_path = os.path.join(temp_dir, u_file.name)
        with open(file_path, "wb") as f:
            f.write(u_file.getbuffer())

        # Eğer yeni bir dosya yüklendiyse OCR yap
        if st.session_state.last_uploaded_file != u_file.name:
            with st.spinner(f"🔍 {u_file.name} taranıyor..."):
                extracted_text = extract_text_via_ocr(file_path)
                # Metni SESSION STATE'e kaydediyoruz (Hafızada kalacak)
                st.session_state.pending_file_text = extracted_text
                st.session_state.last_uploaded_file = u_file.name
            st.toast(f"📎 {u_file.name} analiz edildi.", icon="✅")

# Chat Input
if prompt := st.chat_input("Mesajınızı yazın..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_generator = asyncio.run(process_interaction(prompt))
        final_text = st.write_stream(response_generator)
        st.session_state.messages.append({"role": "assistant", "content": final_text})
