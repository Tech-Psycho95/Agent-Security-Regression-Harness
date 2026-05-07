"""Tests for live HTTP target"""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
from http.server import HTTPServer
from pathlib import Path

import pytest

from agent_harness.cli import main

SCENARIO_PATH = Path(__file__).resolve().parents[1] / "scenarios" / "prompt_injection" / "direct_instruction_override_001.yaml"

@pytest.fixture()
def live_http_server():
    """Spin up the example HTTP target in a background thread.

    Binds to an OS-assigned port to avoid conflicts with other tests or
    running demo agents. Yields the base URL, then shuts down cleanly.
    """
    target_path = Path(__file__).resolve().parents[1] / "examples" / "targets" / "http_agent.py"
    spec = importlib.util.spec_from_file_location("http_agent", target_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    server = HTTPServer(("127.0.0.1", 0), module.AgentRequestHandler)
    port = server.server_address[1]

    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield f"http://127.0.0.1:{port}"

    server.shutdown()
    thread.join(timeout=5)


def test_run_live_http_adapter_success_path(capsys, monkeypatch, live_http_server):
    """End-to-end live HTTP success path: scenario -> HTTP adapter ->
    test server -> trace -> assertion evaluation -> pass result.
    """
    monkeypatch.setattr(sys, "argv", [
        "agent-harness", "run", str(SCENARIO_PATH),
        "--live", "--target-url", f"{live_http_server}/run",
    ])

    exit_code = main()

    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert exit_code == 0
    assert result["scenario_id"] == "prompt_injection.direct_instruction_override_001"
    assert result["mode"] == "live"
    assert result["result"] == "pass"
    assert result["assertions"][0]["id"] == "no_denied_tool_call"
    assert result["assertions"][0]["result"] == "pass"
    assert result["trace"]["tool_calls"] == []