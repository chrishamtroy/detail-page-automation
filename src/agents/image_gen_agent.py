import asyncio
import base64
import io
from PIL import Image, ImageDraw
from google import genai
from google.genai import types
from src.config import get_gemini_key, GEMINI_IMAGE_MODEL, SECTION_WIDTH

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


def _call_gemini_image_api(image_prompt: str) -> bytes | None:
    try:
        client = _get_client()
        response = client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,
            contents=image_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                return base64.b64decode(part.inline_data.data)
    except Exception:
        pass
    return None


def _resize_to_bytes(image_bytes: bytes, width: int, height: int) -> bytes:
    img = Image.open(io.BytesIO(image_bytes))
    img = img.resize((width, height), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def generate_background(
    section_id: str, image_prompt: str, product_data: dict
) -> str:
    height = SECTION_HEIGHTS.get(section_id, 600)
    semaphore = _get_semaphore()

    async with semaphore:
        loop = asyncio.get_event_loop()
        image_bytes = await loop.run_in_executor(
            None, _call_gemini_image_api, image_prompt
        )

    if image_bytes:
        resized = _resize_to_bytes(image_bytes, SECTION_WIDTH, height)
        return "data:image/png;base64," + base64.b64encode(resized).decode()

    fallback = _gradient_fallback(section_id, SECTION_WIDTH, height)
    return "data:image/png;base64," + base64.b64encode(fallback).decode()
