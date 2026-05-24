# 상세페이지 자동화 시스템

Claude × Gemini Flash × Playwright로 13섹션 이커머스 상세페이지 PNG를 자동 생성합니다.

## 빠른 시작

```bash
# 1. 클론
git clone https://github.com/chrishamtroy/detail-page-automation
cd detail-page-automation

# 2. 의존성 설치
pip install -r requirements.txt
playwright install chromium

# 3. API 키 설정
cp .env.example .env
# .env 파일에 키 입력:
# ANTHROPIC_API_KEY=sk-ant-...
# GEMINI_API_KEY=AIza...

# 4. 상품 정보 수정
# input/product_data.json 편집

# 5. 실행
python generate.py
```

## 파이프라인 구조

```
input/product_data.json
    │
    ▼
orchestrator.py  (3배치 병렬)
    │
    ├── Batch A [01~05]  ──┐
    ├── Batch B [06~10]  ──┤  asyncio.gather
    └── Batch C [11~13]  ──┘
              │
              ▼  섹션별 4단계
       1. content_agent.py    → Claude 카피 JSON
       2. image_prompt_agent.py → Gemini 이미지 프롬프트
       3. image_gen_agent.py   → Gemini 배경 이미지
       4. html_render_agent.py → Playwright PNG
              │
              ▼
       Pillow 수직 합산 → final_output.png
```

## 13섹션 구조

| # | 섹션 | 목적 |
|---|------|------|
| 01 | hero | 3초 내 관심 캡처 |
| 02 | pain | 고통 공감 |
| 03 | problem | 실패 원인 분석 |
| 04 | story | 변화 전/후 |
| 05 | solution_intro | 제품 소개 |
| 06 | how_it_works | 사용법 |
| 07 | social_proof | 후기/통계 |
| 08 | authority | 전문가 권위 |
| 09 | benefits_bonus | 혜택 + 보너스 |
| 10 | risk_removal | 환불 보장 |
| 11 | final_choice | 선택 압박 |
| 12 | target_filter | 타겟 필터 |
| 13 | final_cta | 최종 행동 유도 |

## 옵션

```bash
# 단일 섹션만 생성
python generate.py --section hero

# 카피만 생성 (이미지/렌더링 스킵, API 비용 절약)
python generate.py --dry-run

# 커스텀 입력/출력
python generate.py --input my_product.json --output my_output/

# 프리뷰 열기
python preview.py output/<run_id>/
```

## 필요 API 키

| 서비스 | 용도 | 발급 |
|--------|------|------|
| Anthropic | Claude 카피 생성 | [console.anthropic.com](https://console.anthropic.com) |
| Google AI | Gemini 이미지 생성 | [aistudio.google.com](https://aistudio.google.com) |

## 출력물

```
output/
└── 20260524_143022/
    ├── section_hero.png
    ├── section_pain.png
    ├── ...
    ├── section_final_cta.png
    ├── final_output.png      ← 13섹션 합본
    └── _preview.html         ← 브라우저 갤러리
```

## 상품 정보 커스터마이징

`input/product_data.json`에서 다음 항목을 수정하세요:

- `brand.color_primary` / `color_secondary` — 브랜드 컬러
- `product.*` — 상품명, 가격, 혜택, 성분 등
- `social_proof.testimonials` — 실제 후기
- `offer.bonus_items` — 보너스 구성

## 기술 스택

- **카피**: Claude `claude-sonnet-4-6` (Anthropic)
- **이미지 프롬프트**: Gemini 2.0 Flash
- **배경 이미지**: Gemini 2.0 Flash Exp Image Generation
- **렌더링**: Playwright chromium + Jinja2
- **합산**: Pillow
