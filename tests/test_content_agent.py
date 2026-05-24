import pytest
from src.agents.content_agent import _parse_json


def test_parse_plain_json():
    assert _parse_json('{"key": "value"}') == {"key": "value"}


def test_parse_json_codeblock_with_lang():
    text = '```json\n{"key": "value"}\n```'
    assert _parse_json(text) == {"key": "value"}


def test_parse_json_codeblock_no_lang():
    text = '```\n{"key": "value"}\n```'
    assert _parse_json(text) == {"key": "value"}


def test_parse_json_with_whitespace():
    assert _parse_json('  \n{"a": 1}  \n') == {"a": 1}


def test_parse_json_nested():
    text = '{"steps": [{"number": "01", "title": "시작"}]}'
    result = _parse_json(text)
    assert result["steps"][0]["number"] == "01"


def test_parse_invalid_json_raises():
    with pytest.raises(Exception):
        _parse_json("not json at all")


def test_parse_empty_codeblock_raises():
    with pytest.raises(Exception):
        _parse_json("```\n\n```")
