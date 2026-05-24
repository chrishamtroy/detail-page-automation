import asyncio
import json
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import get_gemini_key, GEMINI_TEXT_MODEL

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=get_gemini_key())
    return _client


STYLE_GUIDE = """
Photorealistic commercial product photography style.
Clean, high-end, Korean e-commerce aesthetic.
Warm natural lighting, soft shadows.
Width 1200px, height 600-800px landscape orientation.
No text overlay, no watermarks.
"""

SECTION_STYLE_HINTS: dict[str, str] = {
    "hero": "Aspirational lifestyle photo. Product prominently featured. Bright, energetic background.",
    "pain": "Empathetic scene. Person looking tired/frustrated but relatable. Soft muted tones.",
    "problem": "Before/problem visualization. Dark-to-light gradient. Conceptual imagery.",
    "story": "Split or dual imagery showing transformation. Left=before, right=after. Warm hopeful tones.",
    "solution_intro": "Product hero shot. White or gradient background. Premium minimal style.",
    "how_it_works": "Step-by-step flat lay or process visualization. Clean, organized. Soft background.",
    "social_proof": "Happy satisfied customers lifestyle photo. Natural candid feel. Warm tones.",
    "authority": "Professional expert portrait or laboratory/clinic setting. Trust-building aesthetic.",
    "benefits_bonus": "Product with bonus items arranged artistically. Gift/value presentation style.",
    "risk_removal": "Shield, lock, or guarantee symbol imagery. Safe, trustworthy blue tones.",
    "final_choice": "Crossroads or decision moment. Bright vs dark contrast. Motivational.",
    "target_filter": "Specific target demographic lifestyle photo. Relatable daily life scene.",
    "final_cta": "Urgency and excitement. Countdown, limited stock visual. High energy colors.",
}


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
)
def _call_gemini_text(prompt: str) -> str:
    client = _get_client()
    response = client.models.generate_content(
        model=GEMINI_TEXT_MODEL,
        contents=prompt,
    )
    return response.text.strip()


async def generate_image_prompt(
    section_id: str, copy_data: dict, product_data: dict
) -> str:
    brand = product_data.get("brand", {})
    product = product_data.get("product", {})

    color_primary = brand.get("color_primary", "#FF6B35")
    color_secondary = brand.get("color_secondary", "#1A1A2E")
    product_name = product.get("name", "product")
    category = product.get("category", "")

    prompt = f"""Create an optimized English image generation prompt for this e-commerce section background.

Section: {section_id}
Product: {product_name} ({category})
Brand colors: primary={color_primary}, secondary={color_secondary}
Section copy summary: {json.dumps(copy_data, ensure_ascii=False)[:500]}
Style hint: {SECTION_STYLE_HINTS.get(section_id, "")}

Global style guide:
{STYLE_GUIDE}

Output ONLY the image generation prompt in English. No explanation, no labels.
Keep it under 150 words. Be specific and vivid."""

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _call_gemini_text, prompt)
