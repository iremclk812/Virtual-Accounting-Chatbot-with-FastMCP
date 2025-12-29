import asyncio

from client.mcp_client import MCPToolClient
from client.ollama import ask_llm


MCP_SERVER_URL = "http://127.0.0.1:8000"


async def main():
    mcp = MCPToolClient(MCP_SERVER_URL)

    # 1️⃣ MCP tools al
    tools = await mcp.list_tools()

    tools_schema = [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        k: {"type": "string"} for k in t.input_schema.get("properties", {})
                    }
                }
            }
        }
        for t in tools
    ]

    user_input = "Aydınlık tekstilin banka hesaplarını getir"

    # 2️⃣ LLM karar versin
    llm_response = ask_llm(user_input, tools_schema)

    # 3️⃣ Tool çağrısı var mı?
    tool_calls = llm_response.get("tool_calls")

    if not tool_calls:
        print("🤖 LLM:", llm_response["message"]["content"])
        return

    tool_call = tool_calls[0]
    tool_name = tool_call["name"]
    args = tool_call["arguments"]

    # 4️⃣ MCP tool çalıştır
    result = await mcp.run_tool(tool_name, args)

    print("\n📤 TOOL OUTPUT:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
