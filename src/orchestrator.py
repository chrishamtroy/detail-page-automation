import asyncio
import io
from pathlib import Path
from PIL import Image
from loguru import logger
from src.config import SECTIONS
from src.agents.section_coordinator import run_section
from src.agents.html_render_agent import BrowserPool


async def run(
    product_data: dict,
    output_dir: Path,
    dry_run: bool = False,
    only_section: str | None = None,
) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)

    browser_pool = BrowserPool(max_pages=4)
    if not dry_run:
        await browser_pool.start()

    try:
        results = await _run_sections(
            product_data=product_data,
            output_dir=output_dir,
            browser_pool=browser_pool,
            dry_run=dry_run,
            only_section=only_section,
        )
    finally:
        if not dry_run:
            await browser_pool.stop()

    if not dry_run and not only_section:
        _merge_images(results, output_dir)

    return results


async def _run_sections(
    product_data: dict,
    output_dir: Path,
    browser_pool: BrowserPool,
    dry_run: bool,
    only_section: str | None,
) -> list[dict]:
    if only_section:
        return [
            await run_section(only_section, product_data, output_dir, browser_pool, dry_run)
        ]

    async def _task(s: str) -> dict:
        return await run_section(s, product_data, output_dir, browser_pool, dry_run)

    logger.info("[Batch A] 섹션 01~05 병렬 생성")
    results_a = await asyncio.gather(*[_task(s) for s in SECTIONS[0:5]])

    logger.info("[Batch B] 섹션 06~10 병렬 생성")
    results_b = await asyncio.gather(*[_task(s) for s in SECTIONS[5:10]])

    logger.info("[Batch C] 섹션 11~13 병렬 생성")
    results_c = await asyncio.gather(*[_task(s) for s in SECTIONS[10:]])

    return list(results_a) + list(results_b) + list(results_c)


def _merge_images(results: list[dict], output_dir: Path) -> None:
    png_paths = [
        Path(r["output_path"])
        for r in results
        if r.get("status") == "done" and r.get("output_path")
    ]
    if not png_paths:
        return

    images = [Image.open(p) for p in png_paths]
    total_height = sum(img.height for img in images)
    max_width = max(img.width for img in images)

    merged = Image.new("RGB", (max_width, total_height), color=(255, 255, 255))
    y_offset = 0
    for img in images:
        merged.paste(img, (0, y_offset))
        y_offset += img.height

    out = output_dir / "final_output.png"
    merged.save(out, "PNG", optimize=True)
    logger.success(f"최종 합본 저장: {out}")
