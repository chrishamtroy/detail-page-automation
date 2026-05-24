#!/usr/bin/env python3
"""상세페이지 자동 생성 진입점."""

import argparse
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from loguru import logger
from pydantic import ValidationError

from src.config import INPUT_DIR, OUTPUT_DIR, SECTIONS
from src.cost_tracker import get_tracker
from src.logging_setup import setup as setup_logging
from src.models import ProductData
from src.orchestrator import run


def load_product_data(input_path: Path) -> dict:
    if not input_path.exists():
        raise FileNotFoundError(f"입력 파일 없음: {input_path}")
    with open(input_path, encoding="utf-8") as f:
        raw = json.load(f)
    try:
        ProductData.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"product_data.json 스키마 오류:\n{exc}") from exc
    return raw


def print_banner() -> None:
    logger.info("=" * 50)
    logger.info("  상세페이지 자동화 시스템")
    logger.info("  Claude × Gemini × Playwright")
    logger.info("=" * 50)


def print_summary(results: list[dict], elapsed: float, output_dir: Path) -> None:
    done = [r for r in results if r.get("status") == "done"]
    errors = [r for r in results if r.get("status") == "error"]
    cost = get_tracker().report()

    logger.info("=" * 50)
    logger.info("완료 보고")
    logger.info("=" * 50)
    logger.info(f"섹션: {len(done)}/{len(results)} 성공  |  소요: {elapsed:.1f}초")
    logger.info(
        f"비용(추정): Claude ${cost['claude_cost_usd']:.4f}"
        f" + Gemini ${cost['gemini_cost_usd']:.4f}"
        f" = 합계 ${cost['total_cost_usd']:.4f} USD"
    )
    logger.debug(
        f"토큰: Claude in={cost['claude_input_tokens']:,}"
        f" out={cost['claude_output_tokens']:,}"
        f"  Gemini text={cost['gemini_text_tokens']:,}"
        f" images={cost['gemini_images']}"
    )

    for r in errors:
        logger.error(f"섹션 오류 — {r['section_id']}: {r.get('error', '알 수 없는 오류')}")

    final = output_dir / "final_output.png"
    if final.exists():
        logger.success(f"최종 합본: {final}")

    logger.info(f"출력 디렉터리: {output_dir}")
    logger.info("=" * 50)


async def main() -> None:
    parser = argparse.ArgumentParser(description="상세페이지 자동 생성")
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_DIR / "product_data.json",
        help="상품 데이터 JSON 경로",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="출력 디렉터리 (기본: output/<타임스탬프>)",
    )
    parser.add_argument(
        "--section",
        type=str,
        choices=SECTIONS,
        default=None,
        help="단일 섹션만 생성",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="API 호출 없이 카피만 생성 (이미지/렌더링 스킵)",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        metavar="RUN_ID",
        help="중단된 실행 재개 (예: --resume 20260524_123456)",
    )
    args = parser.parse_args()

    product_data = load_product_data(args.input)
    product_name = product_data.get("product", {}).get("name", "unknown")

    if args.resume:
        run_id = args.resume
        output_dir = OUTPUT_DIR / run_id
        if not output_dir.exists():
            raise FileNotFoundError(f"재개 대상 디렉터리 없음: {output_dir}")
    else:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = args.output or OUTPUT_DIR / run_id

    output_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(output_dir)

    print_banner()
    logger.info(f"상품: {product_name}")
    logger.info(f"입력: {args.input}")
    logger.info(f"출력: {output_dir}" + (" [재개 모드]" if args.resume else ""))

    if args.dry_run:
        logger.info("[DRY-RUN] 카피만 생성합니다 (이미지/렌더링 스킵)")

    start = time.time()
    results = await run(
        product_data=product_data,
        output_dir=output_dir,
        dry_run=args.dry_run,
        only_section=args.section,
    )
    elapsed = time.time() - start

    print_summary(results, elapsed, output_dir)

    if not args.dry_run:
        logger.info("프리뷰 보기: python preview.py " + str(output_dir))


if __name__ == "__main__":
    asyncio.run(main())
