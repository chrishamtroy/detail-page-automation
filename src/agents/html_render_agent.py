import asyncio
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright, Browser, Playwright
from src.config import TEMPLATE_DIR, SECTION_WIDTH


def _comma(value: object) -> str:
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)


def _make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,  # 신뢰된 내부 템플릿 파일 — 이스케이프 불필요
    )
    env.filters["comma"] = _comma
    return env


class BrowserPool:
    """Playwright 브라우저 생명주기를 안전하게 관리하는 풀."""

    def __init__(self, max_pages: int = 4) -> None:
        self._max_pages = max_pages
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._semaphore: asyncio.Semaphore | None = None

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch()
        self._semaphore = asyncio.Semaphore(self._max_pages)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def render(
        self,
        html_content: str,
        output_path: Path,
    ) -> Path:
        assert self._browser is not None, "BrowserPool.start()를 먼저 호출하세요."
        assert self._semaphore is not None

        async with self._semaphore:
            page = await self._browser.new_page(
                viewport={"width": SECTION_WIDTH, "height": 800}
            )
            try:
                await page.set_content(html_content, wait_until="networkidle")
                wrapper = await page.query_selector(".section-wrapper")
                if wrapper:
                    await wrapper.screenshot(path=str(output_path))
                else:
                    await page.screenshot(path=str(output_path), full_page=True)
            finally:
                await page.close()

        return output_path


async def render_section(
    section_id: str,
    copy_data: dict,
    background_data_uri: str,
    product_data: dict,
    output_path: Path,
    browser_pool: BrowserPool,
) -> Path:
    env = _make_env()
    template = env.get_template(f"sections/{section_id}.html")

    brand = product_data.get("brand", {})
    html_content = template.render(
        copy=copy_data,
        background=background_data_uri,
        product=product_data.get("product", {}),
        brand=brand,
        offer=product_data.get("offer", {}),
        social_proof=product_data.get("social_proof", {}),
        authority=product_data.get("authority", {}),
        color_primary=brand.get("color_primary", "#FF6B35"),
        color_secondary=brand.get("color_secondary", "#1A1A2E"),
    )

    return await browser_pool.render(html_content, output_path)
