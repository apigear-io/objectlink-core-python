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


def test_mock_source_instance_isolation():
    """Two MockSource instances should have independent state"""
    source1 = MockSource("test.Object1")
    source2 = MockSource("test.Object2")

    source1.events.append({"type": "test"})
    source1.properties["x"] = 42

    assert len(source2.events) == 0, "source2 should not see source1's events"
    assert "x" not in source2.properties, "source2 should not see source1's properties"
