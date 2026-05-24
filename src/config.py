import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
INPUT_DIR = BASE_DIR / "input"

CLAUDE_MODEL = "claude-sonnet-4-6"
GEMINI_TEXT_MODEL = "gemini-2.0-flash"
GEMINI_IMAGE_MODEL = "gemini-2.0-flash-exp-image-generation"
SECTION_WIDTH = 1200

SECTIONS = [
    "hero",
    "pain",
    "problem",
    "story",
    "solution_intro",
    "how_it_works",
    "social_proof",
    "authority",
    "benefits_bonus",
    "risk_removal",
    "final_choice",
    "target_filter",
    "final_cta",
]

SECTION_LABELS = {
    "hero": "01 Hero — 긴급성 헤더",
    "pain": "02 Pain — 공감",
    "problem": "03 Problem — 문제 정의",
    "story": "04 Story — 변화 스토리",
    "solution_intro": "05 Solution Intro — 솔루션 소개",
    "how_it_works": "06 How It Works — 사용법",
    "social_proof": "07 Social Proof — 소셜 증거",
    "authority": "08 Authority — 권위",
    "benefits_bonus": "09 Benefits & Bonus — 혜택",
    "risk_removal": "10 Risk Removal — 리스크 제거",
    "final_choice": "11 Final Choice — 최종 선택",
    "target_filter": "12 Target Filter — 타겟 필터",
    "final_cta": "13 Final CTA — 최종 행동 유도",
}


def get_anthropic_key() -> str:
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요."
        )
    return key


def get_gemini_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요."
        )
    return key
