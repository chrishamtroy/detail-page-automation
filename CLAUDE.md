# detail-page-automation CLAUDE.md

## 절대 규칙
- `.env` 파일 절대 커밋 금지
- `output/` 폴더 내 PNG/HTML 커밋 금지
- API 키 하드코딩 금지

## 아키텍처
```
input/product_data.json
    → orchestrator.py (3배치 병렬)
        → section_coordinator.py (섹션당 4단계)
            → content_agent.py (Claude 카피)
            → image_prompt_agent.py (Gemini 프롬프트)
            → image_gen_agent.py (Gemini 이미지)
            → html_render_agent.py (Playwright PNG)
    → Pillow 합산 → final_output.png
```

## 기술 스택
- Python 3.13+
- anthropic (Claude sonnet-4-6)
- google-genai (Gemini 2.0 Flash)
- Playwright + Jinja2 (HTML→PNG)
- Pillow (이미지 합산)

## 빌드/테스트
- 개발 실행: `python generate.py`
- 단일 섹션: `python generate.py --section hero`
- 드라이런: `python generate.py --dry-run`
- 프리뷰: `python preview.py output/<run_id>/`

## 코딩 컨벤션
- 비동기: asyncio + asyncio.gather
- 동시성 제한: asyncio.Semaphore
- 에러: 폴백 우선 (CSS 그라디언트), 전체 실패 금지
- 타입힌트 필수
