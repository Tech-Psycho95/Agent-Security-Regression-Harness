"""Tests for trace validation."""

from __future__ import annotations

import pytest

from agent_harness.trace import Trace, TraceValidationError


def test_trace_from_dict_accepts_object_items():
    trace = Trace.from_dict(
        {
            "messages": [{"role": "assistant", "content": "ok"}],
            "tool_calls": [{"name": "search", "arguments": {"q": "owasp"}}],
            "events": [{"type": "goal", "id": "summarize_document"}],
        }
    )

    assert trace.messages == [{"role": "assistant", "content": "ok"}]
    assert trace.tool_calls == [{"name": "search", "arguments": {"q": "owasp"}}]
    assert trace.events == [{"type": "goal", "id": "summarize_document"}]


@pytest.mark.parametrize(
    ("field_name", "bad_item"),
    [
        ("messages", "not an object"),
        ("tool_calls", ["not", "an", "object"]),
        ("events", 123),
    ],
)
def test_trace_from_dict_rejects_non_object_items(field_name, bad_item):
    data = {
        "messages": [],
        "tool_calls": [],
        "events": [],
    }
    data[field_name] = [{}, bad_item]

    with pytest.raises(TraceValidationError, match=rf"{field_name}\[1\] must be an object"):
        Trace.from_dict(data)
