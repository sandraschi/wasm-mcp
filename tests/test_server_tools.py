"""Test wasm_mcp server tools (inspect, call) with fixture."""

from pathlib import Path

import pytest

from wasm_mcp.server import _call_export, _inspect_module

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ADD_WAT = FIXTURES / "add.wat"


@pytest.mark.skipif(not ADD_WAT.exists(), reason="fixture add.wat missing")
def test_inspect_add_wat():
    r = _inspect_module(str(ADD_WAT))
    assert r["ok"] is True
    assert "exports" in r
    names = [e["name"] for e in r["exports"]]
    assert "add" in names
    assert "mul" in names


@pytest.mark.skipif(not ADD_WAT.exists(), reason="fixture add.wat missing")
def test_call_add():
    r = _call_export(str(ADD_WAT), "add", "[1, 2]")
    assert r["ok"] is True
    assert r["result"] == 3


@pytest.mark.skipif(not ADD_WAT.exists(), reason="fixture add.wat missing")
def test_call_mul():
    r = _call_export(str(ADD_WAT), "mul", "[4, 5]")
    assert r["ok"] is True
    assert r["result"] == 20
