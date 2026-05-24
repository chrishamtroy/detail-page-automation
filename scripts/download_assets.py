#!/usr/bin/env python3
"""
정적 자산 1회 다운로드 스크립트.

실행: python scripts/download_assets.py

다운로드 항목:
  - Tailwind CSS 3.4.x 전체 빌드 → static/tailwind.min.css
  - Noto Sans KR 폰트 (Regular/Bold/Black) → static/fonts/
"""

import re
import sys
from pathlib import Path

import httpx

STATIC_DIR = Path(__file__).parent.parent / "static"
FONTS_DIR = STATIC_DIR / "fonts"

TAILWIND_URL = "https://cdn.tailwindcss.com"  # Tailwind Play CDN (JS)
GOOGLE_FONTS_CSS_URL = (
    "https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap"
)
GOOGLE_FONTS_HEADERS = {
    # woff2 포맷을 요청하기 위한 모던 브라우저 UA
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _download(url: str, dest: Path, headers: dict | None = None) -> int:
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        r = client.get(url, headers=headers or {})
        r.raise_for_status()
        dest.write_bytes(r.content)
    return len(r.content)


def download_tailwind() -> None:
    dest = STATIC_DIR / "tailwind.js"
    print("Tailwind Play CDN (JS) 다운로드 중...", end=" ", flush=True)
    size = _download(TAILWIND_URL, dest)
    print(f"완료 ({size:,} bytes) → {dest.name}")


def download_noto_sans_kr() -> None:
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    print("Noto Sans KR CSS 요청 중...", end=" ", flush=True)

    with httpx.Client(follow_redirects=True, timeout=30) as client:
        r = client.get(GOOGLE_FONTS_CSS_URL, headers=GOOGLE_FONTS_HEADERS)
        r.raise_for_status()
        fonts_css = r.text

    # CSS에서 woff2 URL 추출 (중복 제거, 순서 유지)
    font_urls = list(dict.fromkeys(
        re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)", fonts_css)
    ))
    print(f"완료 (폰트 {len(font_urls)}개 발견)")

    local_css = fonts_css
    for i, url in enumerate(font_urls):
        filename = f"noto-kr-{i:02d}.woff2"
        dest = FONTS_DIR / filename
        print(f"  폰트 {i+1}/{len(font_urls)} 다운로드...", end=" ", flush=True)
        size = _download(url, dest, headers=GOOGLE_FONTS_HEADERS)
        # CSS의 원격 URL을 로컬 경로로 교체
        local_css = local_css.replace(url, f"fonts/{filename}")
        print(f"완료 ({size:,} bytes)")

    (STATIC_DIR / "noto-sans-kr.css").write_text(local_css, encoding="utf-8")
    print(f"로컬 폰트 CSS → static/noto-sans-kr.css")


def main() -> None:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 50)
    print("  정적 자산 다운로드")
    print("=" * 50)

    errors: list[str] = []

    try:
        download_tailwind()
    except Exception as e:
        errors.append(f"Tailwind: {e}")
        print(f"실패: {e}")

    try:
        download_noto_sans_kr()
    except Exception as e:
        errors.append(f"Noto Sans KR: {e}")
        print(f"실패: {e}")

    print("=" * 50)
    if errors:
        print(f"오류 {len(errors)}건. 인터넷 연결을 확인하세요.")
        sys.exit(1)
    else:
        print("모든 자산 다운로드 완료.")
        print("이제 오프라인에서도 렌더링이 가능합니다.")


if __name__ == "__main__":
    main()
