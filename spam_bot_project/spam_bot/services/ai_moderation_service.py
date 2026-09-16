import json

import aiohttp
from loguru import logger

_ENDPOINT_TMPL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

_SYSTEM_PROMPT = (
    "You are a content moderation classifier for a Telegram study-community group chat. "
    "Given a single message, decide whether it is (a) explicit sexual/adult content, or "
    "(b) an unsolicited flirt-spam-bot lure (e.g. 'lonely, message me privately', fake dating "
    "account bait). Ordinary conversation, advertisements for products/courses, and off-topic "
    "chatter are NOT violations. Respond with strict JSON only: "
    '{"violation": true|false, "category": "adult"|"flirt_spam"|"none"}.'
)


class AIModerationResult:
    def __init__(self, is_violation: bool, category: str, input_tokens: int, output_tokens: int) -> None:
        self.is_violation = is_violation
        self.category = category
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class AIModerationService:
    def __init__(self, model: str) -> None:
        self._model = model

    async def classify(self, text: str, api_key: str) -> AIModerationResult | None:
        url = _ENDPOINT_TMPL.format(model=self._model)
        payload = {
            "systemInstruction": {"parts": [{"text": _SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": text[:2000]}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    params={"key": api_key},
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    data = await resp.json()
                    if resp.status != 200:
                        logger.warning(f"Gemini API xatosi ({resp.status}): {data}")
                        return None
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.warning(f"Gemini API so'rovi muvaffaqiyatsiz: {exc}")
            return None

        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)

        try:
            candidate_text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(candidate_text)
            is_violation = bool(parsed.get("violation", False))
            category = str(parsed.get("category", "none"))
        except (KeyError, IndexError, ValueError, json.JSONDecodeError):
            logger.warning(f"Gemini javobini o'qib bo'lmadi: {data}")
            is_violation, category = False, "none"

        return AIModerationResult(is_violation, category, input_tokens, output_tokens)
