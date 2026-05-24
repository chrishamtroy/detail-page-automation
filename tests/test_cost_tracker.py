import pytest
from src.cost_tracker import CostTracker


def test_initial_report_zeros():
    t = CostTracker()
    r = t.report()
    assert r["total_cost_usd"] == 0.0
    assert r["claude_input_tokens"] == 0
    assert r["claude_output_tokens"] == 0
    assert r["gemini_images"] == 0


def test_claude_input_cost():
    t = CostTracker()
    t.add_claude("hero", 1_000_000, 0)
    r = t.report()
    assert r["claude_input_tokens"] == 1_000_000
    assert r["claude_cost_usd"] == pytest.approx(3.0)


def test_claude_output_cost():
    t = CostTracker()
    t.add_claude("hero", 0, 1_000_000)
    r = t.report()
    assert r["claude_cost_usd"] == pytest.approx(15.0)


def test_gemini_image_tracking():
    t = CostTracker()
    t.add_gemini_image("hero")
    t.add_gemini_image("pain")
    r = t.report()
    assert r["gemini_images"] == 2
    assert r["gemini_cost_usd"] == pytest.approx(0.08)


def test_multiple_sections_accumulate():
    t = CostTracker()
    t.add_claude("hero", 500, 200)
    t.add_claude("pain", 600, 300)
    r = t.report()
    assert r["claude_input_tokens"] == 1100
    assert r["claude_output_tokens"] == 500


def test_same_section_accumulates():
    t = CostTracker()
    t.add_claude("hero", 100, 0)
    t.add_claude("hero", 200, 0)
    r = t.report()
    assert r["claude_input_tokens"] == 300


def test_total_cost_is_sum():
    t = CostTracker()
    t.add_claude("hero", 1_000_000, 0)
    t.add_gemini_image("hero")
    r = t.report()
    assert r["total_cost_usd"] == pytest.approx(r["claude_cost_usd"] + r["gemini_cost_usd"])
