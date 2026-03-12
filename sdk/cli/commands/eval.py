"""Eval command - test agents with inference and trace."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, Optional

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from ..config import load_config

console = Console()


def eval_agent(
    agent_id: str,
    query: str,
    timeout: int = 180,
    show_trace: bool = True,
    json_output: bool = False,
    session_id: Optional[str] = None,
) -> None:
    """Send a query to an agent and display response with trace.

    Args:
        agent_id: The agent ID to test
        query: The query/message to send
        timeout: Request timeout in seconds
        show_trace: Whether to fetch and display trace data
        json_output: Output result as JSON
        session_id: Optional session ID for multi-turn conversations
    """
    config = load_config()
    base_url = "https://agent-prod.studio.lyzr.ai"
    is_new_session = session_id is None
    session_id = session_id or str(uuid.uuid4())

    # Prepare request
    payload = {
        "agent_id": agent_id,
        "session_id": session_id,
        "user_id": "bp-sdk-eval",
        "message": query,
    }
    headers = {
        "X-API-Key": config.agent_api_key,
        "Content-Type": "application/json",
    }

    if not json_output:
        console.print(f"\n[bold blue]Agent ID:[/] {agent_id}")
        if is_new_session:
            console.print(f"[bold blue]Session ID:[/] {session_id} [dim](new)[/]")
        else:
            console.print(f"[bold blue]Session ID:[/] {session_id} [dim](continuing)[/]")
        console.print(f"\n[bold]Query:[/]\n{query}\n")

    # Stream response
    response_text = []
    trace_id = None

    status_ctx = console.status("[bold green]Waiting for response...") if not json_output else nullcontext()
    with status_ctx:
        try:
            with httpx.Client(timeout=float(timeout)) as client:
                with client.stream(
                    "POST",
                    f"{base_url}/v3/inference/stream/",
                    json=payload,
                    headers=headers,
                ) as response:
                    response.raise_for_status()

                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            content = line[6:]  # Remove "data: " prefix
                            if content == "[DONE]":
                                break
                            if content.startswith("{"):
                                try:
                                    data = json.loads(content)
                                    if "trace_id" in data:
                                        trace_id = data["trace_id"]
                                except json.JSONDecodeError:
                                    response_text.append(content)
                            else:
                                response_text.append(content)
        except httpx.HTTPStatusError as e:
            if json_output:
                print(json.dumps({"error": f"HTTP {e.response.status_code}", "detail": e.response.text}))
            else:
                console.print(f"[bold red]Error:[/] HTTP {e.response.status_code}")
                console.print(e.response.text)
            return
        except httpx.RequestError as e:
            if json_output:
                print(json.dumps({"error": str(e)}))
            else:
                console.print(f"[bold red]Error:[/] {e}")
            return

    full_response = "".join(response_text)

    if json_output:
        # Build JSON result
        result: dict[str, Any] = {
            "agent_id": agent_id,
            "session_id": session_id,
            "query": query,
            "response": full_response,
        }

        if show_trace:
            trace_data = _fetch_trace(config.agent_api_key, base_url, agent_id)
            if trace_data:
                result["trace"] = trace_data

        print(json.dumps(result, indent=2))
    else:
        # Display response with Rich formatting
        console.print(Panel(
            Markdown(full_response) if "```" in full_response or "#" in full_response else full_response,
            title="[bold green]Response",
            border_style="green",
        ))

        # Fetch and display trace
        if show_trace:
            _display_trace(config.agent_api_key, base_url, agent_id, session_id)

        # Show continuation tip
        console.print(f"\n[dim]To continue this conversation:[/]")
        console.print(f"[dim]  bp eval {agent_id} \"your next message\" --session {session_id}[/]\n")


def _fetch_trace(api_key: str, base_url: str, agent_id: str) -> dict[str, Any] | None:
    """Fetch trace data and return as dictionary."""
    headers = {"x-api-key": api_key}

    # Wait for trace to be available
    time.sleep(1)

    try:
        with httpx.Client(timeout=30.0) as client:
            traces_response = client.get(
                f"{base_url}/v3/ops/traces",
                params={"agent_id": agent_id, "limit": 5, "count": True},
                headers=headers,
            )

            if traces_response.status_code != 200:
                return None

            traces_data = traces_response.json()
            traces = traces_data.get("traces", [])

            if not traces:
                return None

            trace_id = traces[0].get("trace_id")
            if not trace_id:
                return None

            trace_detail = client.get(
                f"{base_url}/v3/ops/trace/{trace_id}",
                headers=headers,
            )

            if trace_detail.status_code != 200:
                return None

            runs = trace_detail.json()

            # Build structured trace data
            total_latency = sum(r.get("latency_ms", 0) for r in runs)
            total_input_tokens = sum(r.get("num_input_tokens", 0) for r in runs)
            total_output_tokens = sum(r.get("num_output_tokens", 0) for r in runs)

            return {
                "trace_id": trace_id,
                "total_runs": len(runs),
                "total_latency_ms": total_latency,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "agents_involved": list(set(r.get("agent_name") for r in runs if r.get("agent_name"))),
                "runs": [
                    {
                        "step": i + 1,
                        "agent_name": r.get("agent_name"),
                        "agent_id": r.get("agent_id"),
                        "model": r.get("language_model"),
                        "latency_ms": r.get("latency_ms", 0),
                        "input_tokens": r.get("num_input_tokens", 0),
                        "output_tokens": r.get("num_output_tokens", 0),
                    }
                    for i, r in enumerate(runs)
                ],
            }

    except httpx.RequestError:
        return None


def _display_trace(api_key: str, base_url: str, agent_id: str, session_id: str) -> None:
    """Fetch and display trace data with Rich formatting."""
    headers = {"x-api-key": api_key}

    with console.status("[bold blue]Fetching trace..."):
        time.sleep(1)

        try:
            with httpx.Client(timeout=30.0) as client:
                traces_response = client.get(
                    f"{base_url}/v3/ops/traces",
                    params={"agent_id": agent_id, "limit": 5, "count": True},
                    headers=headers,
                )

                if traces_response.status_code != 200:
                    console.print(f"[yellow]Could not fetch traces: {traces_response.status_code}[/]")
                    return

                traces_data = traces_response.json()
                traces = traces_data.get("traces", [])

                if not traces:
                    console.print("[yellow]No traces found[/]")
                    return

                trace_id = traces[0].get("trace_id")
                if not trace_id:
                    console.print("[yellow]No trace_id in response[/]")
                    return

                trace_detail = client.get(
                    f"{base_url}/v3/ops/trace/{trace_id}",
                    headers=headers,
                )

                if trace_detail.status_code != 200:
                    console.print(f"[yellow]Could not fetch trace details: {trace_detail.status_code}[/]")
                    return

                runs = trace_detail.json()

        except httpx.RequestError as e:
            console.print(f"[yellow]Error fetching trace: {e}[/]")
            return

    if not runs:
        console.print("[yellow]Empty trace[/]")
        return

    console.print(f"\n[bold blue]Trace ID:[/] {trace_id}")
    console.print(f"[bold blue]Total Runs:[/] {len(runs)}")

    table = Table(
        title="Delegation Sequence",
        show_header=True,
        header_style="bold cyan",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Agent", style="bold")
    table.add_column("Model", style="dim")
    table.add_column("Latency", justify="right")
    table.add_column("Tokens (in/out)", justify="right")

    total_latency = 0
    total_input_tokens = 0
    total_output_tokens = 0

    for i, run in enumerate(runs, 1):
        agent_name = run.get("agent_name", "Unknown")
        model = run.get("language_model", "N/A")
        latency = run.get("latency_ms", 0)
        input_tokens = run.get("num_input_tokens", 0)
        output_tokens = run.get("num_output_tokens", 0)

        total_latency += latency
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens

        table.add_row(
            str(i),
            agent_name,
            model,
            f"{latency:,.0f}ms",
            f"{input_tokens:,} / {output_tokens:,}",
        )

    console.print(table)

    console.print(f"\n[bold]Summary:[/]")
    console.print(f"  Total Latency: {total_latency:,.0f}ms ({total_latency/1000:.1f}s)")
    console.print(f"  Total Tokens: {total_input_tokens:,} input, {total_output_tokens:,} output")
    console.print(f"  Agents Involved: {len(set(r.get('agent_name') for r in runs))}")


# Context manager for no-op
class nullcontext:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
