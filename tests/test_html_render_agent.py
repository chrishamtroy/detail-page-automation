import pytest
import src.agents.html_render_agent as renderer
from src.agents.html_render_agent import (
    _comma,
    _inject_local_assets,
    _fix_font_stack,
)

_CDN_HTML = (
    "<html><head>"
    '<script src="https://cdn.tailwindcss.com"></script>'
    "</head><body></body></html>"
)


@pytest.fixture(autouse=True)
def reset_asset_cache():
    """각 테스트 전후 모듈 레벨 캐시를 초기화한다."""
    renderer._TAILWIND_JS = None
    renderer._NOTO_CSS = None
    yield
    renderer._TAILWIND_JS = None
    renderer._NOTO_CSS = None


# ── _comma ────────────────────────────────────────────────────────────────────

def test_comma_integer():
    assert _comma(1000000) == "1,000,000"


def test_comma_string_number():
    assert _comma("50000") == "50,000"


def test_comma_zero():
    assert _comma(0) == "0"


def test_comma_invalid_returns_original():
    assert _comma("N/A") == "N/A"


def test_comma_negative():
    assert _comma(-1000) == "-1,000"


# ── _inject_local_assets ──────────────────────────────────────────────────────

def test_inject_replaces_cdn_when_assets_present(monkeypatch):
    monkeypatch.setattr(renderer, "_TAILWIND_JS", "var tw=1;")
    monkeypatch.setattr(renderer, "_NOTO_CSS", "@font-face{}")
    result = _inject_local_assets(_CDN_HTML)
    assert 'src="https://cdn.tailwindcss.com"' not in result
    assert "var tw=1;" in result


def test_inject_appends_font_css_before_head_close(monkeypatch):
    monkeypatch.setattr(renderer, "_TAILWIND_JS", "")
    monkeypatch.setattr(renderer, "_NOTO_CSS", "@font-face{font-family:test}")
    result = _inject_local_assets(_CDN_HTML)
    assert "@font-face{font-family:test}" in result
    assert result.index("@font-face") < result.index("</head>")


def test_inject_no_change_when_no_assets(monkeypatch):
    monkeypatch.setattr(renderer, "_TAILWIND_JS", "")
    monkeypatch.setattr(renderer, "_NOTO_CSS", "")
    html = "<html><head></head><body></body></html>"
    assert _inject_local_assets(html) == html


# ── _fix_font_stack ───────────────────────────────────────────────────────────

def test_fix_font_adds_malgun():
    html = "font-family: 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif"
    result = _fix_font_stack(html)
    assert "'Malgun Gothic'" in result
    assert "'Apple SD Gothic Neo'" in result


def test_fix_font_no_match_unchanged():
    html = "font-family: Arial, sans-serif"
    assert _fix_font_stack(html) == html


def test_fix_font_preserves_surrounding_text():
    html = "body { font-family: 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif; color: red; }"
    result = _fix_font_stack(html)
    assert "color: red" in result
