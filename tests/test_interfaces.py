"""Tests for interface definitions."""

import inspect
from olink.client.sink import IObjectSink
from olink.remote.source import IObjectSource


def test_sink_interface_olink_object_name_has_self():
    """olink_object_name first parameter should be 'self'"""
    sig = inspect.signature(IObjectSink.olink_object_name)
    params = list(sig.parameters.keys())
    assert len(params) > 0, "Method should have parameters"
    assert params[0] == 'self', f"First parameter should be 'self', got '{params[0] if params else 'none'}'"


def test_source_interface_olink_object_name_has_self():
    """olink_object_name first parameter should be 'self'"""
    sig = inspect.signature(IObjectSource.olink_object_name)
    params = list(sig.parameters.keys())
    assert len(params) > 0, "Method should have parameters"
    assert params[0] == 'self', f"First parameter should be 'self', got '{params[0] if params else 'none'}'"
