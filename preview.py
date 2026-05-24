#!/usr/bin/env python3
"""output/<run_id>/ 폴더의 PNG를 브라우저에서 볼 수 있는 HTML로 생성."""

import sys
import base64
import webbrowser
from pathlib import Path


def build_preview(output_dir: Path) -> Path:
    png_files = sorted(output_dir.glob("section_*.png"))
    final = output_dir / "final_output.png"

    items_html = ""
    for png in png_files:
        section_id = png.stem.replace("section_", "")
        data = base64.b64encode(png.read_bytes()).decode()
        items_html += f"""
        <div class="section-item">
          <div class="label">{section_id}</div>
          <img src="data:image/png;base64,{data}" alt="{section_id}">
        </div>
        """

    final_html = ""
    if final.exists():
        data = base64.b64encode(final.read_bytes()).decode()
        final_html = f"""
        <div class="final-section">
          <h2>최종 합본</h2>
          <img src="data:image/png;base64,{data}" alt="final output" style="max-width:100%;">
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>상세페이지 프리뷰 — {output_dir.name}</title>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #1a1a2e; color: #eee; margin: 0; padding: 20px; }}
  h1 {{ text-align: center; color: #FF6B35; margin-bottom: 30px; }}
  .sections {{ display: flex; flex-direction: column; align-items: center; gap: 4px; }}
  .section-item {{ width: 1200px; position: relative; }}
  .label {{ position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.7); color: #FF6B35;
            font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 4px; z-index: 10; }}
  .section-item img {{ width: 100%; display: block; }}
  .final-section {{ margin-top: 60px; text-align: center; }}
  .final-section h2 {{ color: #FF6B35; margin-bottom: 20px; }}
</style>
</head>
<body>
<h1>상세페이지 프리뷰 — {output_dir.name}</h1>
<div class="sections">
{items_html}
</div>
{final_html}
</body>
</html>"""

    preview_path = output_dir / "_preview.html"
    preview_path.write_text(html, encoding="utf-8")
    return preview_path


def main() -> None:
    if len(sys.argv) < 2:
        print("사용법: python preview.py output/<run_id>/")
        sys.exit(1)

    output_dir = Path(sys.argv[1])
    if not output_dir.exists():
        print(f"디렉터리 없음: {output_dir}")
        sys.exit(1)

    preview_path = build_preview(output_dir)
    print(f"프리뷰 생성: {preview_path}")
    webbrowser.open(str(preview_path))


if __name__ == "__main__":
    main()
