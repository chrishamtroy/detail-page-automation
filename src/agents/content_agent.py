import json
import anthropic
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import get_anthropic_key, CLAUDE_MODEL
from src.cost_tracker import get_tracker

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=get_anthropic_key())
    return _client


SYSTEM_PROMPT = """당신은 대한민국 최고의 이커머스 세일즈 카피라이터입니다.
한국어 구어체로, 자연스럽고 설득력 있게 상세페이지 카피를 작성합니다.

원칙:
- 결론 먼저, 이유 나중
- 감정 → 논리 순서
- 구체적 숫자 사용 ("많은" 대신 "143명", "빠르게" 대신 "3일 만에")
- 2인칭 "당신/여러분" 적절히 사용
- 짧은 문장 (한 문장 20자 이내)
- 번역체 금지, 한국어 자연스러운 구어체

항상 JSON 형식으로만 응답하세요. 마크다운 코드블록 없이 순수 JSON만.
"""

SECTION_PROMPTS: dict[str, str] = {
    "hero": """Hero 섹션 카피를 작성하세요.
목표: 3초 내 관심 캡처 + 긴급성 유발

출력 JSON:
{
  "headline_options": ["옵션1", "옵션2", "옵션3"],
  "subheadline": "타겟 명시 + 방법 힌트",
  "urgency_badge": "한정 수량/기간 문구",
  "cta_text": "행동 유도 버튼 텍스트"
}""",

    "pain": """Pain 섹션 카피를 작성하세요.
목표: "이거 내 얘기다" 공감 유발

출력 JSON:
{
  "intro": "공감 질문 (1문장)",
  "pain_points": ["고통1", "고통2", "고통3", "고통4"],
  "emotional_hook": "혼자가 아님을 알려주는 마무리 문장"
}""",

    "problem": """Problem 섹션 카피를 작성하세요.
목표: 실패 원인 이해 → 해결책 기대 유도

출력 JSON:
{
  "hook": "반전 발견 문구",
  "reasons": ["진짜 원인1", "진짜 원인2", "진짜 원인3"],
  "reframe": "관점 전환 문장"
}""",

    "story": """Story 섹션 카피를 작성하세요.
목표: 변화 전/후 드라마로 가능성 확신

출력 JSON:
{
  "before": "과거 고통 상황 묘사",
  "turning_point": "전환점 문장",
  "after": "변화 후 새로운 일상",
  "proof": "증거/결과 수치"
}""",

    "solution_intro": """Solution Intro 섹션 카피를 작성하세요.
목표: 제품 정체성 명확화

출력 JSON:
{
  "intro": "소개 문구",
  "product_name": "제품명",
  "one_liner": "핵심 정의 (한 문장)",
  "target_fit": "이 제품이 맞는 사람"
}""",

    "how_it_works": """How It Works 섹션 카피를 작성하세요.
목표: 쉬워 보이게 + 신뢰 형성

출력 JSON:
{
  "headline": "섹션 제목",
  "steps": [
    {"number": "01", "title": "단계명", "description": "설명", "result": "결과"},
    {"number": "02", "title": "단계명", "description": "설명", "result": "결과"},
    {"number": "03", "title": "단계명", "description": "설명", "result": "결과"}
  ]
}""",

    "social_proof": """Social Proof 섹션 카피를 작성하세요.
목표: 실사용자 신뢰로 구매 저항 낮추기

출력 JSON:
{
  "headline": "섹션 제목 (숫자 포함)",
  "stats": [
    {"number": "수치", "label": "설명"},
    {"number": "수치", "label": "설명"},
    {"number": "수치", "label": "설명"}
  ],
  "featured_review": {
    "quote": "대표 후기",
    "name": "이름",
    "result": "결과"
  }
}""",

    "authority": """Authority 섹션 카피를 작성하세요.
목표: 전문가/브랜드 권위로 신뢰 구축

출력 JSON:
{
  "intro": "전문가 소개 문구",
  "credential_highlight": "가장 인상적인 자격 1가지",
  "personal_message": "전문가 직접 메시지 (3~4문장)",
  "cta": "전문가 권장 문구"
}""",

    "benefits_bonus": """Benefits & Bonus 섹션 카피를 작성하세요.
목표: 가치 극대화로 가격 저항 낮추기

출력 JSON:
{
  "headline": "섹션 제목",
  "main_benefits": [
    {"icon": "이모지", "title": "혜택명", "description": "설명"}
  ],
  "bonus_headline": "보너스 소개 문구",
  "total_value_text": "총 가치 강조 문구"
}""",

    "risk_removal": """Risk Removal 섹션 카피를 작성하세요.
목표: 구매 장벽 완전 제거

출력 JSON:
{
  "guarantee_headline": "보장 제목",
  "guarantee_body": "보장 내용 상세 (2~3문장)",
  "faqs": [
    {"question": "질문", "answer": "답변"},
    {"question": "질문", "answer": "답변"},
    {"question": "질문", "answer": "답변"}
  ]
}""",

    "final_choice": """Final Choice 섹션 카피를 작성하세요.
목표: 최종 선택 압박 (현재 vs 미래)

출력 JSON:
{
  "headline": "선택의 순간 문구",
  "without": ["이 제품 없이 계속되는 상황1", "상황2", "상황3"],
  "with": ["이 제품과 함께하는 미래1", "미래2", "미래3"],
  "question": "최종 선택 질문"
}""",

    "target_filter": """Target Filter 섹션 카피를 작성하세요.
목표: 적합 고객만 남기고 불필요한 환불 방지

출력 JSON:
{
  "headline": "섹션 제목",
  "recommended": {
    "title": "이런 분께 딱입니다",
    "items": ["적합 대상1", "적합 대상2", "적합 대상3"]
  },
  "not_recommended": {
    "title": "이런 분께는 맞지 않아요",
    "items": ["비적합 대상1", "비적합 대상2"]
  }
}""",

    "final_cta": """Final CTA 섹션 카피를 작성하세요.
목표: 마지막 행동 유도 + 긴급성 최고조

출력 JSON:
{
  "headline": "마지막 헤드라인 (강렬하게)",
  "urgency_text": "긴급성 문구 (재고/기간)",
  "price_display": "가격 표시 문구",
  "cta_button": "CTA 버튼 텍스트",
  "closing": "마무리 안심 문구"
}""",
}


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # 첫 줄(```json 또는 ```) 과 마지막 줄(```) 제거
        inner = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        text = inner.strip()
    return json.loads(text)


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
)
async def generate_copy(section_id: str, product_data: dict) -> dict:
    prompt = f"""다음 상품 정보를 바탕으로 {section_id} 섹션 카피를 작성하세요.

상품 정보:
{json.dumps(product_data, ensure_ascii=False, indent=2)}

{SECTION_PROMPTS[section_id]}"""

    client = _get_client()
    response = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    usage = response.usage
    get_tracker().add_claude(section_id, usage.input_tokens, usage.output_tokens)
    logger.debug(
        f"[{section_id}] Claude tokens: in={usage.input_tokens} out={usage.output_tokens}"
    )

    return _parse_json(response.content[0].text)
