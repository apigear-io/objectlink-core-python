"""Safety tests for ObjectLink protocol implementation.

Tests for malformed messages, registry edge cases, phantom entry prevention,
message size limits, and other safety-critical behaviors.
"""

import json

import pytest

from olink.client.node import ClientNode
from olink.client.registry import ClientRegistry
from olink.core.protocol import Protocol
from olink.core.types import MessageConverter, MessageFormat, MsgType, Name
from olink.mocks import MockSink, MockSource
from olink.remote.node import RemoteNode
from olink.remote.registry import RemoteRegistry

# --- Malformed message handling (H1) ---


class TestMalformedMessages:
    def setup_method(self):
        self.log_messages = []
        self.client = ClientNode()
        self.client.on_log(lambda level, msg: self.log_messages.append((level, msg)))

    def test_empty_message(self):
        """Empty JSON array should be silently dropped."""
        self.client.handle_message("[]")
        assert any("invalid message" in msg for _, msg in self.log_messages)

    def test_non_list_message(self):
        """Non-list JSON should be silently dropped."""
        self.client.handle_message('"hello"')
        assert any("invalid message" in msg for _, msg in self.log_messages)

    def test_unknown_message_type(self):
        """Unknown message type should be logged and ignored."""
        self.client.handle_message(json.dumps([999, "test"]))
        assert any("not supported message type" in msg for _, msg in self.log_messages)

    def test_link_message_too_short(self):
        """LINK message with only type field should be dropped."""
        self.client.handle_message(json.dumps([MsgType.LINK]))
        assert any("malformed message" in msg for _, msg in self.log_messages)

    def test_invoke_message_too_short(self):
        """INVOKE message with fewer than 4 elements should be dropped."""
        self.client.handle_message(json.dumps([MsgType.INVOKE, 1]))
        assert any("malformed message" in msg for _, msg in self.log_messages)

    def test_invoke_message_with_3_elements(self):
        """INVOKE needs at least 4 elements."""
        self.client.handle_message(json.dumps([MsgType.INVOKE, 1, "demo.Calc/add"]))
        assert any("malformed message" in msg for _, msg in self.log_messages)

    def test_set_property_too_short(self):
        """SET_PROPERTY needs at least 3 elements."""
        self.client.handle_message(json.dumps([MsgType.SET_PROPERTY]))
        assert any("malformed message" in msg for _, msg in self.log_messages)

    def test_error_message_too_short(self):
        """ERROR needs at least 4 elements."""
        self.client.handle_message(json.dumps([MsgType.ERROR, 10]))
        assert any("malformed message" in msg for _, msg in self.log_messages)

    def test_valid_link_message_still_works(self):
        """Valid messages should still be processed after validation is added."""
        name = "demo.SafetyTest"
        sink = MockSink(name)
        remote = RemoteNode()
        source = MockSource(name)

        # Wire up client and remote directly
        client = ClientNode()
        client.on_write(lambda msg: remote.handle_message(msg))
        remote.on_write(lambda msg: client.handle_message(msg))

        # Register through the global registries
        ClientNode.register_sink(sink)
        RemoteNode.register_source(source)

        client.link_remote(name)
        assert any(e.get("type") == "linked" for e in source.events)

        # Cleanup
        ClientNode.unregister_sink(sink)
        RemoteNode.unregister_source(source)

    def test_message_with_extra_fields_accepted(self):
        """Messages with extra trailing fields should be accepted (forward-compat)."""

        class FakeListener:
            def handle_link(self, name):
                self.last_name = name

        listener = FakeListener()
        p = Protocol(listener)
        # LINK normally has 2 elements, but 3 should also work (future extension)
        result = p.handle_message([MsgType.LINK, "demo.Test", "extra_field"])
        assert result is True
        assert listener.last_name == "demo.Test"

    def test_invalid_json(self):
        """Invalid JSON should be caught and logged."""
        self.client.handle_message("not valid json{{{")
        assert any("handle_message error" in msg for _, msg in self.log_messages)


# --- Registry KeyError prevention (M1, M2) ---


class TestRegistryKeyErrors:
    def test_client_unregister_nonexistent_sink(self):
        """Unregistering a sink that was never registered should not crash."""
        registry = ClientRegistry()
        sink = MockSink("nonexistent.Object")
        # Should not raise KeyError
        registry.unregister_sink(sink)

    def test_remote_remove_node_from_source_twice(self):
        """Double-removing a node from source should not crash."""
        registry = RemoteRegistry()
        source = MockSource("demo.Test")
        registry.add_source(source)
        node = RemoteNode()
        registry.add_node_to_source("demo.Test", node)
        registry.remove_node_from_source("demo.Test", node)
        # Second removal should not crash (uses discard)
        registry.remove_node_from_source("demo.Test", node)

    def test_remote_remove_nonexistent_node(self):
        """Removing a node that's not in any source should not crash."""
        registry = RemoteRegistry()
        node = RemoteNode()
        # Should not crash
        registry.remove_node(node)


# --- Phantom entry prevention (M3) ---


class TestPhantomEntryPrevention:
    def test_get_source_nonexistent_no_phantom(self):
        """Looking up a nonexistent source should not create a registry entry."""
        registry = RemoteRegistry()
        result = registry.get_source("nonexistent.Object")
        assert result is None
        assert len(registry.entries) == 0

    def test_get_nodes_nonexistent_no_phantom(self):
        """Looking up nodes for a nonexistent source should not create an entry."""
        registry = RemoteRegistry()
        result = registry.get_nodes("nonexistent.Object")
        assert len(result) == 0
        assert len(registry.entries) == 0

    def test_get_sink_nonexistent_no_phantom(self):
        """Looking up a nonexistent sink should not create a registry entry."""
        registry = ClientRegistry()
        result = registry.get_sink("nonexistent.Object")
        assert result is None
        assert len(registry.entries) == 0

    def test_get_node_nonexistent_no_phantom(self):
        """Looking up a node for a nonexistent sink should not create an entry."""
        registry = ClientRegistry()
        result = registry.get_node("nonexistent.Object")
        assert result is None
        assert len(registry.entries) == 0

    def test_add_source_still_creates_entry(self):
        """Mutation operations should still create entries as needed."""
        registry = RemoteRegistry()
        source = MockSource("demo.Test")
        registry.add_source(source)
        assert len(registry.entries) == 1
        assert registry.get_source("demo.Test") is source


# --- Message size limit (M5) ---


class TestMessageSizeLimit:
    def test_oversized_message_rejected(self):
        """Messages exceeding max size should raise ValueError."""
        converter = MessageConverter(MessageFormat.JSON, max_message_size=100)
        large_msg = json.dumps([MsgType.LINK, "a" * 200])
        with pytest.raises(ValueError, match="message size"):
            converter.from_string(large_msg)

    def test_normal_message_accepted(self):
        """Normal-sized messages should work fine."""
        converter = MessageConverter(MessageFormat.JSON, max_message_size=1024)
        msg = json.dumps([MsgType.LINK, "demo.Counter"])
        result = converter.from_string(msg)
        assert result[0] == MsgType.LINK

    def test_default_limit_is_1mb(self):
        """Default max message size should be 1MB."""
        converter = MessageConverter(MessageFormat.JSON)
        assert converter.max_message_size == 1024 * 1024


# --- Exception handling (H6) ---


class TestExceptionHandling:
    def test_json_decode_error_caught(self):
        """Invalid JSON should be caught as JSONDecodeError."""
        log_messages = []
        node = ClientNode()
        node.on_log(lambda level, msg: log_messages.append((level, msg)))
        node.handle_message("{invalid")
        assert any("handle_message error" in msg for _, msg in log_messages)

    def test_value_error_from_oversized_message(self):
        """ValueError from message size limit should be caught."""
        log_messages = []
        converter_size = 50
        node = ClientNode()
        node.converter.max_message_size = converter_size
        node.on_log(lambda level, msg: log_messages.append((level, msg)))
        large_msg = json.dumps([MsgType.LINK, "a" * 100])
        node.handle_message(large_msg)
        assert any("handle_message error" in msg for _, msg in log_messages)


# --- Name utility edge cases (M4) ---


class TestNameUtility:
    def test_resource_from_name_no_slash(self):
        """Name without slash returns the full string as resource."""
        assert Name.resource_from_name("demo.Counter") == "demo.Counter"

    def test_path_from_name_no_slash(self):
        """Name without slash returns the full string as path."""
        assert Name.path_from_name("demo.Counter") == "demo.Counter"

    def test_has_path_with_slash(self):
        assert Name.has_path("demo.Counter/count") is True

    def test_has_path_without_slash(self):
        assert Name.has_path("demo.Counter") is False

    def test_empty_string(self):
        """Empty string edge case."""
        assert Name.resource_from_name("") == ""
        assert Name.path_from_name("") == ""

    def test_create_name(self):
        assert Name.create_name("demo.Counter", "count") == "demo.Counter/count"
