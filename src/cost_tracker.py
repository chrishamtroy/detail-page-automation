"""API 사용량 및 예상 비용 추적 (싱글턴)."""
from __future__ import annotations
import threading
from dataclasses import dataclass, field

# 가격 기준 (2025년 기준 추정치, 변동 가능)
_CLAUDE_IN_PER_MTK = 3.0    # $3 / 1M input tokens
_CLAUDE_OUT_PER_MTK = 15.0  # $15 / 1M output tokens
_GEMINI_TEXT_PER_MTK = 0.10  # $0.10 / 1M tokens (gemini-2.0-flash)
_GEMINI_IMAGE_EACH = 0.04    # ~$0.04 / 이미지 생성 (추정)


@dataclass
class _SectionUsage:
    section_id: str
    claude_in: int = 0
    claude_out: int = 0
    gemini_text: int = 0
    gemini_images: int = 0


class CostTracker:
    def __init__(self) -> None:
        self._records: list[_SectionUsage] = []
        self._lock = threading.Lock()

    def add_claude(self, section_id: str, input_tokens: int, output_tokens: int) -> None:
        with self._lock:
            rec = self._get_or_create(section_id)
            rec.claude_in += input_tokens
            rec.claude_out += output_tokens

    def add_gemini_text(self, section_id: str, tokens: int) -> None:
        with self._lock:
            self._get_or_create(section_id).gemini_text += tokens

    def add_gemini_image(self, section_id: str) -> None:
        with self._lock:
            self._get_or_create(section_id).gemini_images += 1

    def _get_or_create(self, section_id: str) -> _SectionUsage:
        for rec in self._records:
            if rec.section_id == section_id:
                return rec
        rec = _SectionUsage(section_id=section_id)
        self._records.append(rec)
        return rec

    def report(self) -> dict:
        total_in = sum(r.claude_in for r in self._records)
        total_out = sum(r.claude_out for r in self._records)
        total_gt = sum(r.gemini_text for r in self._records)
        total_gi = sum(r.gemini_images for r in self._records)

        claude_cost = (total_in * _CLAUDE_IN_PER_MTK + total_out * _CLAUDE_OUT_PER_MTK) / 1_000_000
        gemini_cost = total_gt * _GEMINI_TEXT_PER_MTK / 1_000_000 + total_gi * _GEMINI_IMAGE_EACH

        return {
            "claude_input_tokens": total_in,
            "claude_output_tokens": total_out,
            "gemini_text_tokens": total_gt,
            "gemini_images": total_gi,
            "claude_cost_usd": round(claude_cost, 4),
            "gemini_cost_usd": round(gemini_cost, 4),
            "total_cost_usd": round(claude_cost + gemini_cost, 4),
        }


_tracker = CostTracker()


def get_tracker() -> CostTracker:
    return _tracker
