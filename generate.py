#!/usr/bin/env python3
"""상세페이지 자동 생성 진입점."""

import argparse
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from src.config import INPUT_DIR, OUTPUT_DIR, SECTIONS
from src.orchestrator import run


def load_product_data(input_path: Path) -> dict:
    if not input_path.exists():
        raise FileNotFoundError(f"입력 파일 없음: {input_path}")
    with open(input_path, encoding="utf-8") as f:
        return json.load(f)


def print_banner() -> None:
    print("\n" + "=" * 60)
    print("  상세페이지 자동화 시스템")
    print("  Claude × Gemini × Playwright")
    print("=" * 60 + "\n")


def print_summary(results: list[dict], elapsed: float, output_dir: Path) -> None:
    done = [r for r in results if r.get("status") == "done"]
    errors = [r for r in results if r.get("status") == "error"]

    print("\n" + "=" * 60)
    print("  완료 보고")
    print("=" * 60)
    print(f"  섹션: {len(done)}/{len(results)} 성공")
    print(f"  소요: {elapsed:.1f}초")
    print(f"  출력: {output_dir}")

    if errors:
        print(f"\n  오류 ({len(errors)}건):")
        for r in errors:
            print(f"    - {r['section_id']}: {r.get('error', '알 수 없는 오류')}")

    final = output_dir / "final_output.png"
    if final.exists():
        print(f"\n  최종 합본: {final}")

    print("=" * 60 + "\n")


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
    args = parser.parse_args()

    print_banner()

    product_data = load_product_data(args.input)
    product_name = product_data.get("product", {}).get("name", "unknown")
    print(f"상품: {product_name}")
    print(f"입력: {args.input}")

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output or OUTPUT_DIR / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"출력: {output_dir}\n")

    if args.dry_run:
        print("[DRY-RUN] 카피만 생성합니다 (이미지/렌더링 스킵)\n")

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
        print("프리뷰 보기: python preview.py " + str(output_dir))


if __name__ == "__main__":
    asyncio.run(main())
