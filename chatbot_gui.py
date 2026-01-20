import streamlit as st
import asyncio
import os
from client.mcp_client import MCPToolClient
from client.ollama import chat_with_llm, chat_with_llm_stream, SYSTEM_PROMPT

# --- 1. KONFİGÜRASYON ---
MCP_SERVER_URL = "http://127.0.0.1:8000/sse"
temp_dir = "temp_uploads"
os.makedirs(temp_dir, exist_ok=True)

st.set_page_config(page_title="Sanal Müşavir AI", page_icon="💼", layout="centered")

# --- 2. CSS (MİNİMALİST CHATGPT STİLİ) ---
st.markdown("""
    <style>
    /* Ana Konteyner Genişliği */
    .stMainBlockContainer {
        max-width: 740px !important;
    }

    /* CHAT INPUT BARINI SOLA KAYDIR (Ataç için yer aç) */
    div[data-testid="stChatInput"] textarea {
        padding-left: 45px !important;
    }

    /* ATAÇ BUTONU (POPOVER) KONUMLANDIRMA */
    div[data-testid="stPopover"] {
        position: fixed;
        bottom: 53px; /* Chat barının tam ortası ile dikey hiza */
        left: 50%;
        /* Barın 740px genişliğinde olduğunu varsayarak sol kenara hizalar */
        transform: translateX(-355px); 
        z-index: 1000001;
        width: 30px !important;
    }

    /* Butonun Görünüşü (Küçük ve Şeffaf) */
    div[data-testid="stPopover"] > button {
        background-color: transparent !important;
        border: none !important;
        color: #8e8ea0 !important; /* ChatGPT gri tonu */
        padding: 0px !important;
        width: 28px !important;
        height: 28px !important;
        min-width: 28px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: color 0.2s ease;
    }

    /* İkon Boyutu */
    div[data-testid="stPopover"] > button p {
        font-size: 18px !important; /* Ataç ikonunu küçült */
        margin: 0px !important;
    }

    /* Popover içindeki OK (Aşağı ok) işaretini gizle */
    div[data-testid="stPopover"] svg[data-testid="stIcon"] {
        display: none !important;
    }

    /* Üzerine gelince belirginleş */
    div[data-testid="stPopover"] > button:hover {
        color: #ffffff !important;
    }

    /* Input alanını engelleyen gereksiz boşlukları kaldır */
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stPopover"]) {
        height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
        pointer-events: none;
    }
    div[data-testid="stPopover"] {
        pointer-events: auto;
    }

    /* Mobil Ekranlar İçin Düzeltme */
    @media (max-width: 740px) {
        div[data-testid="stPopover"] {
            left: 15px;
            transform: none;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

if "mcp_client" not in st.session_state:
    st.session_state.mcp_client = MCPToolClient(MCP_SERVER_URL)


# --- 4. YARDIMCI FONKSİYONLAR ---
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
    st.session_state.messages.append({"role": "user", "content": user_input})
    tools_schema = await get_tools_from_server()

    with st.spinner("İşleniyor..."):
        response_msg = chat_with_llm(st.session_state.messages, tools_schema)

    if response_msg.get("tool_calls"):
        st.session_state.messages.append(response_msg)
        for tool_call in response_msg["tool_calls"]:
            t_name, t_args = tool_call["function"]["name"], tool_call["function"]["arguments"]
            with st.status(f"🛠️ {t_name}...", expanded=False):
                result = await st.session_state.mcp_client.run_tool(t_name, t_args)
            st.session_state.messages.append({"role": "tool", "content": result, "name": t_name})

    def gen():
        for chunk in chat_with_llm_stream(st.session_state.messages):
            yield chunk.get('message', {}).get('content', '')

    return gen()


# --- 5. ARAYÜZ (CHAT) ---
st.title("💼 Sanal Müşavir Asistanı")
st.caption("Vergi, Banka ve Belge Analizi")

# Geçmiş Mesajlar
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"] and "content" in msg:
        clean_content = msg["content"].split("\n\n[SİSTEM NOTU:")[0]
        with st.chat_message(msg["role"]):
            st.markdown(clean_content)

# --- 6. GİRİŞ ALANI (ATAÇ VE BAR) ---
file_info_hidden = ""
uploaded_file_name = None

# Küçük Ataç Butonu
with st.popover("📎"):
    u_file = st.file_uploader("Belge Yükle", type=["pdf", "docx", "doc", "txt"], label_visibility="collapsed")
    if u_file:
        file_path = os.path.join(temp_dir, u_file.name)
        with open(file_path, "wb") as f:
            f.write(u_file.getbuffer())
        uploaded_file_name = u_file.name
        file_info_hidden = f"\n\n[SİSTEM NOTU: Dosya yolu: '{file_path}'. read_file aracını kullan.]"
        st.toast(f"📎 {u_file.name} eklendi.", icon="✅")

# Chat Input
if prompt := st.chat_input("Mesajınızı yazın..."):
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file_name:
            st.caption(f"📎 {uploaded_file_name} analiz edilecek.")

    actual_input = prompt + file_info_hidden
    with st.chat_message("assistant"):
        response_generator = asyncio.run(process_interaction(actual_input))
        final_text = st.write_stream(response_generator)
        st.session_state.messages.append({"role": "assistant", "content": final_text})