"""Tests for demo_server implementations."""

import pytest

# Skip all tests if starlette is not available
pytest.importorskip("starlette")

from demo_server import CounterAdapter


def test_counter_adapter_set_property():
    """olink_set_property should set property on impl object"""
    class TestCounter:
        count = 0

    # Bypass __init__ to avoid registration side effects
    adapter = CounterAdapter.__new__(CounterAdapter)
    adapter.impl = TestCounter()

    adapter.olink_set_property("demo.Counter/count", 42)
    assert adapter.impl.count == 42, f"Expected 42, got {adapter.impl.count}"


def test_remote_endpoint_instance_isolation():
    """Two RemoteEndpoint instances should have independent node and queue"""
    from demo_server import RemoteEndpoint
    from unittest.mock import MagicMock

    scope1 = {"type": "websocket"}
    scope2 = {"type": "websocket"}

    endpoint1 = RemoteEndpoint(scope1, MagicMock(), MagicMock())
    endpoint2 = RemoteEndpoint(scope2, MagicMock(), MagicMock())

    assert endpoint1.node is not endpoint2.node, "Each endpoint should have its own RemoteNode"
    assert endpoint1.queue is not endpoint2.queue, "Each endpoint should have its own Queue"
