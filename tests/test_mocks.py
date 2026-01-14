"""Tests for mock implementations."""

from olink.mocks import MockSink, MockSource


def test_mock_sink_instance_isolation():
    """Two MockSink instances should have independent state"""
    sink1 = MockSink("test.Object1")
    sink2 = MockSink("test.Object2")

    sink1.events.append({"type": "test"})
    sink1.properties["x"] = 42

    assert len(sink2.events) == 0, "sink2 should not see sink1's events"
    assert "x" not in sink2.properties, "sink2 should not see sink1's properties"
