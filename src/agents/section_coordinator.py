from pathlib import Path
from src.agents.content_agent import generate_copy
from src.agents.image_prompt_agent import generate_image_prompt
from src.agents.image_gen_agent import generate_background
from src.agents.html_render_agent import render_section, BrowserPool


async def run_section(
    section_id: str,
    product_data: dict,
    output_dir: Path,
    browser_pool: BrowserPool,
    dry_run: bool = False,
) -> dict:
    result: dict = {"section_id": section_id, "status": "pending"}

    try:
        print(f"  [{section_id}] 카피 생성 중...")
        copy_data = await generate_copy(section_id, product_data)
        result["copy"] = copy_data

        if dry_run:
            result["status"] = "dry_run"
            print(f"  [{section_id}] dry-run 완료 (이미지/렌더링 스킵)")
            return result

        print(f"  [{section_id}] 이미지 프롬프트 생성 중...")
        image_prompt = await generate_image_prompt(section_id, copy_data, product_data)
        result["image_prompt"] = image_prompt

        print(f"  [{section_id}] 배경 이미지 생성 중...")
        background_uri = await generate_background(
            section_id, image_prompt, product_data
        )

        print(f"  [{section_id}] PNG 렌더링 중...")
        output_path = output_dir / f"section_{section_id}.png"
        await render_section(
            section_id, copy_data, background_uri, product_data, output_path, browser_pool
        )

        result["output_path"] = str(output_path)
        result["status"] = "done"
        print(f"  [{section_id}] 완료 → {output_path.name}")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"  [{section_id}] 오류: {e}")

    return result
