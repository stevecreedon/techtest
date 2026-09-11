import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

from app.schemas.chat import ChatEvent

ToolCaller = Callable[[str, dict], Awaitable[Any]]
EventEmitter = Callable[[ChatEvent], Awaitable[None]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict


class LLMClient(Protocol):
    """Runs one chat turn: reasons, optionally calls tools, emits streamed events."""

    async def run(
        self,
        user_message: str,
        tools: list[ToolSpec],
        call_tool: ToolCaller,
        emit: EventEmitter,
    ) -> None: ...


class AnthropicLLMClient:
    """Streams a Claude tool-use turn, forwarding extended-thinking deltas as they arrive."""

    def __init__(self, api_key: str, model: str) -> None:
        import anthropic

        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def run(
        self,
        user_message: str,
        tools: list[ToolSpec],
        call_tool: ToolCaller,
        emit: EventEmitter,
    ) -> None:
        anthropic_tools = [
            {"name": t.name, "description": t.description, "input_schema": t.input_schema}
            for t in tools
        ]
        messages: list[dict] = [{"role": "user", "content": user_message}]
        final_text = ""

        while True:
            async with self._client.messages.stream(
                model=self._model,
                max_tokens=1536,
                thinking={"type": "enabled", "budget_tokens": 2000},
                tools=anthropic_tools,  # type: ignore[arg-type]
                messages=messages,  # type: ignore[arg-type]
            ) as stream:
                async for event in stream:
                    if event.type != "content_block_delta":
                        continue
                    delta = event.delta
                    if delta.type == "thinking_delta":
                        await emit(ChatEvent(type="thinking", text=delta.thinking))
                    elif delta.type == "text_delta":
                        final_text += delta.text

                response = await stream.get_final_message()

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                break

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                await emit(
                    ChatEvent(type="tool_call", tool_name=block.name, tool_input=block.input)
                )
                result = await call_tool(block.name, block.input)
                await emit(ChatEvent(type="tool_result", tool_name=block.name, text=str(result)))
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": str(result)}
                )
            messages.append({"role": "user", "content": tool_results})
            final_text = ""

        await emit(ChatEvent(type="answer", text=final_text.strip()))


class FakeLLMClient:
    """Deterministic, network-free stand-in for AnthropicLLMClient.

    Pattern-matches the three example questions from docs/requirements/chat.md
    and drives the real MCP tools, so the full pipeline (filters, region
    resolution, aggregation, PII-safety) is exercised without an API key.
    Used automatically when ANTHROPIC_API_KEY is not configured.
    """

    async def run(
        self,
        user_message: str,
        tools: list[ToolSpec],
        call_tool: ToolCaller,
        emit: EventEmitter,
    ) -> None:
        lowered = user_message.lower()

        await emit(ChatEvent(type="thinking", text="Reading the question for filters..."))

        if "average" in lowered and "age" in lowered:
            await self._answer_average_age(lowered, call_tool, emit)
        elif "percentile" in lowered and ("below" in lowered or "range" in lowered):
            await self._answer_percentile(lowered, call_tool, emit)
        elif "quartile" in lowered or ("percentile" in lowered and "aggregate" in lowered):
            await self._answer_bucket_counts(lowered, call_tool, emit)
        else:
            await self._answer_fallback(call_tool, emit)

    async def _answer_average_age(
        self, lowered: str, call_tool: ToolCaller, emit: EventEmitter
    ) -> None:
        gender = _extract_gender(lowered)
        region = _extract_region(lowered)
        await emit(
            ChatEvent(
                type="thinking",
                text=(
                    f"Averaging age filtered by gender={gender or 'any'}, region={region or 'any'}."
                ),
            )
        )
        args = {k: v for k, v in {"gender": gender, "region": region}.items() if v}
        await emit(ChatEvent(type="tool_call", tool_name="average_age", tool_input=args))
        result = await call_tool("average_age", args)
        await emit(ChatEvent(type="tool_result", tool_name="average_age", text=str(result)))

        who = f"{gender or 'people'}" + (f" in {region}" if region else "")
        if result["value"] is None:
            await emit(ChatEvent(type="answer", text=f"No matching records found for {who}."))
            return
        await emit(
            ChatEvent(
                type="answer",
                text=(
                    f"The average age of {who} is {result['value']:.1f} years "
                    f"(sample size: {result['sample_size']})."
                ),
            )
        )

    async def _answer_percentile(
        self, lowered: str, call_tool: ToolCaller, emit: EventEmitter
    ) -> None:
        match = re.search(r"(\d+)(?:st|nd|rd|th)?\s+percentile", lowered)
        percentile = float(match.group(1)) if match else 90.0
        await emit(
            ChatEvent(type="thinking", text=f"Computing the {percentile:g}th percentile of age.")
        )
        args = {"percentile": percentile}
        await emit(ChatEvent(type="tool_call", tool_name="age_percentile", tool_input=args))
        result = await call_tool("age_percentile", args)
        await emit(ChatEvent(type="tool_result", tool_name="age_percentile", text=str(result)))
        await emit(
            ChatEvent(
                type="answer",
                text=(
                    f"Ages below the {percentile:g}th percentile range from "
                    f"{result['min_age']} to {result['age_at_percentile']:.1f} years "
                    f"(sample size: {result['sample_size']})."
                ),
            )
        )

    async def _answer_bucket_counts(
        self, lowered: str, call_tool: ToolCaller, emit: EventEmitter
    ) -> None:
        gender = _extract_gender(lowered)
        await emit(
            ChatEvent(
                type="thinking", text=f"Bucketing ages into quartiles for gender={gender or 'any'}."
            )
        )
        args: dict = {"percentile_edges": [25, 50, 75, 100]}
        if gender:
            args["gender"] = gender
        await emit(ChatEvent(type="tool_call", tool_name="bucket_counts", tool_input=args))
        result = await call_tool("bucket_counts", args)
        await emit(ChatEvent(type="tool_result", tool_name="bucket_counts", text=str(result)))

        summary = ", ".join(f"{b['label']}: {b['count']}" for b in result["buckets"])
        who = gender or "people"
        await emit(ChatEvent(type="answer", text=f"Counts of {who} by age quartile — {summary}."))

    async def _answer_fallback(self, call_tool: ToolCaller, emit: EventEmitter) -> None:
        await emit(ChatEvent(type="tool_call", tool_name="list_countries", tool_input={}))
        countries = await call_tool("list_countries", {})
        await emit(ChatEvent(type="tool_result", tool_name="list_countries", text=str(countries)))
        await emit(
            ChatEvent(
                type="answer",
                text=(
                    f"I can answer questions about {len(countries)} countries. "
                    "Try asking things like 'What is the average age of men in "
                    "South America?', 'What age range is below the 90th percentile "
                    "by age?', or 'Aggregate the number of women by quartile.'"
                ),
            )
        )


def _extract_gender(lowered: str) -> str | None:
    if "women" in lowered or "female" in lowered:
        return "female"
    if "men" in lowered or "male" in lowered:
        return "male"
    return None


def _extract_region(lowered: str) -> str | None:
    for region in ["south america", "north america", "europe", "asia", "africa", "oceania"]:
        if region in lowered:
            return region.title()
    return None
