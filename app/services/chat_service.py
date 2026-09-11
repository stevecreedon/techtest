from app.mcp.server import mcp_server
from app.schemas.chat import ChatEvent
from app.services.export_service import ExportService
from app.services.llm_client import EventEmitter, LLMClient, ToolSpec


def _tabular_rows(tool_name: str, result: object) -> list[dict] | None:
    """Pull exportable rows out of a tool result, if it has any."""
    if tool_name == "query_people" and isinstance(result, list):
        return result
    if tool_name == "bucket_counts" and isinstance(result, dict):
        buckets = result.get("buckets")
        if isinstance(buckets, list):
            return buckets
    return None


class ChatService:
    def __init__(self, llm_client: LLMClient, export_service: ExportService) -> None:
        self._llm_client = llm_client
        self._export_service = export_service

    async def handle_message(self, message: str, emit: EventEmitter) -> None:
        tools = await self._list_tool_specs()
        last_rows: list[dict] | None = None

        async def call_tool(name: str, arguments: dict) -> object:
            nonlocal last_rows
            _content, structured = await mcp_server.call_tool(name, arguments)
            result = (
                structured.get("result", structured) if isinstance(structured, dict) else structured
            )
            rows = _tabular_rows(name, result)
            if rows:
                last_rows = rows
            return result

        await self._llm_client.run(message, tools, call_tool, emit)

        if last_rows and len(last_rows) > 1:
            export_id = self._export_service.create_export(last_rows, filename="result.csv")
            await emit(ChatEvent(type="download", download_url=f"/downloads/{export_id}"))

    @staticmethod
    async def _list_tool_specs() -> list[ToolSpec]:
        mcp_tools = await mcp_server.list_tools()
        return [
            ToolSpec(name=t.name, description=t.description or "", input_schema=t.inputSchema)
            for t in mcp_tools
        ]
