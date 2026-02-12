from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

class MCPToolClient:
    def __init__(self, server_url: str):
        # URL'nin sonunda /sse olduğundan emin oluyoruz
        self.server_url = server_url if server_url.endswith("/sse") else f"{server_url}/sse"

    async def run_tool(self, tool_name: str, args: dict):
        async with sse_client(self.server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, args)
                return result.content[0].text

    async def list_tools(self):
        async with sse_client(self.server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return result.tools # .tools listesini döndürür