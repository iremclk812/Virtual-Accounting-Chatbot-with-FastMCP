import streamlit as st
import asyncio
import time
from client.mcp_client import MCPToolClient
from client.ollama import chat_with_llm, chat_with_llm_stream, SYSTEM_PROMPT

# --- KONFİGÜRASYON ---
MCP_SERVER_URL = "http://127.0.0.1:8000/sse"

st.set_page_config(
    page_title="Sanal Müşavir AI",
    page_icon="💼",
    layout="centered"
)

st.title("💼 Sanal Müşavir Asistanı")
st.caption("Vergi, Banka ve Ödeme Takibi | Resmi Dilekçe Oluşturucu")

# --- SESSION STATE BAŞLATMA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

if "mcp_client" not in st.session_state:
    # MCP Client'ı bir kez oluşturuyoruz
    st.session_state.mcp_client = MCPToolClient(MCP_SERVER_URL)


# --- ASYNC YARDIMCI FONKSİYONLAR ---
async def get_tools_from_server():
    """Sunucudan tool listesini çeker ve Ollama formatına çevirir."""
    try:
        mcp = st.session_state.mcp_client
        tools = await mcp.list_tools()

        # MCP Tool objelerini Ollama JSON Schema formatına dönüştür
        formatted_tools = []
        for t in tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema  # SDK 1.0+ için inputSchema kullanılır
                }
            })
        return formatted_tools
    except Exception as e:
        st.error(f"MCP Sunucusuna bağlanılamadı: {e}")
        return []


async def execute_tool(name, args):
    """Belirlenen tool'u MCP üzerinden çalıştırır."""
    mcp = st.session_state.mcp_client
    return await mcp.run_tool(name, args)


# --- ANA İŞLEMCİ (DÖNGÜ) ---
async def process_interaction(user_input):
    # 1. Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 2. Toolları hazırla
    tools_schema = await get_tools_from_server()

    # 3. LLM'e sor (Karar aşaması - stream=False)
    # AI bir tool mu çağıracak yoksa direkt mi konuşacak?
    with st.spinner("Düşünüyor..."):
        response_msg = chat_with_llm(st.session_state.messages, tools_schema)

    # 4. Tool Çağrısı Var mı?
    if response_msg.get("tool_calls"):
        # AI bir veya birden fazla tool çağırmak istiyor
        st.session_state.messages.append(response_msg)

        for tool_call in response_msg["tool_calls"]:
            t_name = tool_call["function"]["name"]
            t_args = tool_call["function"]["arguments"]

            with st.status(f"🛠️ {t_name} sorgulanıyor...", expanded=False) as status:
                result = await execute_tool(t_name, t_args)
                status.update(label=f"✅ {t_name} verisi alındı.", state="complete", expanded=False)

            # Tool sonucunu geçmişe ekle
            st.session_state.messages.append({
                "role": "tool",
                "content": result,
                "name": t_name
            })

        # Tool verileriyle beraber son cevabı stream ederek oluştur
        return stream_output()

    else:
        # Tool yok, direkt cevabı stream et
        return stream_output()


def stream_output():
    """Ollama'dan gelen yanıtı harf harf Streamlit'e aktaran jeneratör."""

    def generator():
        full_text = ""
        # chat_with_llm_stream fonksiyonu stream=True ile çalışır
        for chunk in chat_with_llm_stream(st.session_state.messages):
            content = chunk.get('message', {}).get('content', '')
            full_text += content
            yield content

    return generator()


# --- ARAYÜZ ÇİZİMİ ---
# Geçmiş mesajları ekrana bas (Sistem mesajı ve Tool mesajları hariç)
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"] and "content" in msg:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Kullanıcı girişi
if prompt := st.chat_input("Örn: Aydınlık firmasının vergi borcu nedir?"):
    # Kullanıcı mesajını ekranda göster
    with st.chat_message("user"):
        st.markdown(prompt)

    # Asistan cevabını stream ederek göster
    with st.chat_message("assistant"):
        # Async döngüyü çalıştır ve jeneratörü al
        response_generator = asyncio.run(process_interaction(prompt))

        # Streamlit'in daktilo efekti
        full_response = st.write_stream(response_generator)

        # Final cevabı geçmişe kaydet
        st.session_state.messages.append({"role": "assistant", "content": full_response})