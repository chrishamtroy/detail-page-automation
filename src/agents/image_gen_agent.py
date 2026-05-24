import asyncio
import base64
import io
from PIL import Image, ImageDraw
from google import genai
from google.genai import types
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import get_gemini_key, GEMINI_IMAGE_MODEL, SECTION_WIDTH
from src.cost_tracker import get_tracker

_client: genai.Client | None = None
_semaphore: asyncio.Semaphore | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=get_gemini_key())
    return _client


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(3)
    return _semaphore


SECTION_HEIGHTS: dict[str, int] = {
    "hero": 700,
    "pain": 600,
    "problem": 600,
    "story": 650,
    "solution_intro": 600,
    "how_it_works": 700,
    "social_proof": 650,
    "authority": 600,
    "benefits_bonus": 700,
    "risk_removal": 600,
    "final_choice": 600,
    "target_filter": 550,
    "final_cta": 600,
}

GRADIENT_PRESETS: dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]] = {
    "hero": ((255, 107, 53), (26, 26, 46)),
    "pain": ((107, 107, 140), (40, 40, 60)),
    "problem": ((60, 60, 90), (20, 20, 40)),
    "story": ((255, 140, 80), (100, 60, 120)),
    "solution_intro": ((255, 107, 53), (255, 200, 150)),
    "how_it_works": ((240, 248, 255), (200, 220, 240)),
    "social_proof": ((255, 250, 240), (255, 220, 180)),
    "authority": ((30, 50, 80), (10, 30, 60)),
    "benefits_bonus": ((255, 107, 53), (255, 180, 100)),
    "risk_removal": ((20, 60, 100), (10, 40, 70)),
    "final_choice": ((40, 20, 60), (20, 10, 40)),
    "target_filter": ((245, 245, 250), (220, 225, 240)),
    "final_cta": ((200, 30, 30), (100, 10, 10)),
}


def _gradient_fallback(section_id: str, width: int, height: int) -> bytes:
    top_color, bottom_color = GRADIENT_PRESETS.get(
        section_id, ((50, 50, 80), (20, 20, 40))
    )
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=3, max=15),
)
def _call_gemini_image_api(image_prompt: str) -> bytes | None:
    client = _get_client()
    response = client.models.generate_content(
        model=GEMINI_IMAGE_MODEL,
        contents=image_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )
    candidates = response.candidates or []
    if not candidates:
        return None
    content = candidates[0].content
    if content is None:
        return None
    for part in content.parts or []:
        inline = part.inline_data
        if inline and inline.mime_type and inline.mime_type.startswith("image/") and inline.data:
            return base64.b64decode(inline.data)
    return None


def _resize_to_bytes(image_bytes: bytes, width: int, height: int) -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def generate_background(
    section_id: str, image_prompt: str, product_data: dict  # noqa: ARG001
) -> str:
    height = SECTION_HEIGHTS.get(section_id, 600)
    semaphore = _get_semaphore()

    image_bytes: bytes | None = None
    async with semaphore:
        loop = asyncio.get_event_loop()
        try:
            image_bytes = await loop.run_in_executor(
                None, _call_gemini_image_api, image_prompt
            )
        except Exception:
            pass  # 재시도 소진 후 폴백으로 진행

    if image_bytes:
        get_tracker().add_gemini_image(section_id)
        logger.debug(f"[{section_id}] Gemini 이미지 생성 성공")
        resized = _resize_to_bytes(image_bytes, SECTION_WIDTH, height)
        return "data:image/png;base64," + base64.b64encode(resized).decode()

    logger.warning(f"[{section_id}] Gemini 이미지 실패 → 그라디언트 폴백")
    fallback = _gradient_fallback(section_id, SECTION_WIDTH, height)
    return "data:image/png;base64," + base64.b64encode(fallback).decode()
