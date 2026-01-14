"""Tests for MessageConverter to ensure proper handling of special float values."""
import json
import pytest
from olink.core.types import MessageConverter, MessageFormat, MsgType


def test_message_converter_normal_values():
    """Test that normal values are serialized correctly."""
    converter = MessageConverter(MessageFormat.JSON)

    data = [MsgType.PROPERTY_CHANGE, "test.Object/prop", {"value": 42.5}]
    result = converter.to_string(data)
    parsed = json.loads(result)

    assert parsed == [MsgType.PROPERTY_CHANGE, "test.Object/prop", {"value": 42.5}]


def test_message_converter_rejects_infinity():
    """Test that infinity values raise ValueError."""
    converter = MessageConverter(MessageFormat.JSON)

    data = [MsgType.PROPERTY_CHANGE, "test.Object/prop", {"value": float('inf')}]
    with pytest.raises(ValueError):
        converter.to_string(data)


def test_message_converter_rejects_negative_infinity():
    """Test that negative infinity values raise ValueError."""
    converter = MessageConverter(MessageFormat.JSON)

    data = [MsgType.PROPERTY_CHANGE, "test.Object/prop", {"value": float('-inf')}]
    with pytest.raises(ValueError):
        converter.to_string(data)


def test_message_converter_rejects_nan():
    """Test that NaN values raise ValueError."""
    converter = MessageConverter(MessageFormat.JSON)

    data = [MsgType.PROPERTY_CHANGE, "test.Object/prop", {"value": float('nan')}]
    with pytest.raises(ValueError):
        converter.to_string(data)


def test_message_converter_round_trip():
    """Test that data can be serialized and deserialized correctly."""
    converter = MessageConverter(MessageFormat.JSON)

    original = [MsgType.INVOKE, 42, "test.Object/method", [1, 2, 3]]
    serialized = converter.to_string(original)
    deserialized = converter.from_string(serialized)
    assert deserialized == original
