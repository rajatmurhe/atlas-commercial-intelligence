"""Gemini structured planner; never forwards database rows or credentials."""

import json
import re
import httpx


def generate_plan(cfg, instructions, question, context, schema):
    if not cfg.gemini_api_key:
        raise RuntimeError("Gemini requires GEMINI_API_KEY.")
    if not re.fullmatch(r"gemini-[a-zA-Z0-9.\-]+", cfg.gemini_model):
        raise RuntimeError("Invalid GEMINI_MODEL.")
    try:
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{cfg.gemini_model}:generateContent",
            headers={"x-goog-api-key": cfg.gemini_api_key},
            json={
                "systemInstruction": {"parts": [{"text": instructions}]},
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": json.dumps(
                                    {"question": question, "context": context}
                                )
                            }
                        ],
                    }
                ],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseJsonSchema": schema,
                    "temperature": 0,
                    "maxOutputTokens": 4096,
                },
            },
            timeout=30,
        )
    except httpx.RequestError:
        raise RuntimeError("Gemini connection failed; retry later.") from None
    if response.status_code != 200:
        # Do not include provider response bodies, headers, or secrets in logs.
        raise RuntimeError(
            f"Gemini request failed (HTTP {response.status_code}); check free-tier quota and API configuration."
        )
    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates or candidates[0].get("finishReason") != "STOP":
        raise RuntimeError("Gemini did not return a complete plan.")
    payload = "".join(
        p.get("text", "")
        for p in candidates[0].get("content", {}).get("parts", [])
        if not p.get("thought")
    )
    usage = data.get("usageMetadata", {})
    return payload, {
        "input_tokens": usage.get("promptTokenCount", 0),
        "output_tokens": usage.get("candidatesTokenCount", 0)
        + usage.get("thoughtsTokenCount", 0),
    }
