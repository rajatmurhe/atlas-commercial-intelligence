import json
from types import SimpleNamespace
import httpx
import pytest
from ciq.gemini import generate_plan
from ciq.agent import classify
from ciq.config import settings


def test_gemini_plan_preserves_context_and_validates(monkeypatch):
    cfg = settings()
    monkeypatch.setattr(cfg, "agent_mode", "live")
    monkeypatch.setattr(cfg, "llm_provider", "gemini")
    monkeypatch.setattr(cfg, "gemini_api_key", "test-secret")

    def post(url, **kwargs):
        body = kwargs["json"]
        assert "test-secret" not in url
        assert (
            json.loads(body["contents"][0]["parts"][0]["text"])["context"]["intent"]
            == "products"
        )
        assert body["generationConfig"]["responseJsonSchema"]["properties"]["intent"][
            "enum"
        ]
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {
                            "parts": [
                                {
                                    "text": json.dumps(
                                        {
                                            "intent": "products",
                                            "country": "Qatar",
                                            "period": "Q3 2026",
                                            "message": "",
                                        }
                                    )
                                }
                            ]
                        },
                    }
                ],
                "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 30},
            },
        )

    monkeypatch.setattr("ciq.gemini.httpx.post", post)
    result = classify(
        {
            "question": "What about Qatar?",
            "context": {"intent": "products", "period": "Q3 2026"},
        }
    )
    assert result["plan"]["country"] == "Qatar"
    assert result["usage"] == {"input_tokens": 100, "output_tokens": 30}


@pytest.mark.parametrize("status", [400, 403, 429, 500])
def test_provider_errors_are_sanitized(monkeypatch, status):
    monkeypatch.setattr(
        "ciq.gemini.httpx.post",
        lambda *a, **k: httpx.Response(status, text="secret-provider-details"),
    )
    cfg = SimpleNamespace(gemini_api_key="test-secret", gemini_model="gemini-2.5-flash")
    with pytest.raises(RuntimeError) as exc:
        generate_plan(cfg, "", "", {}, {})
    assert str(status) in str(exc.value)
    assert "secret" not in str(exc.value)


def test_incomplete_plan_is_rejected(monkeypatch):
    monkeypatch.setattr(
        "ciq.gemini.httpx.post",
        lambda *a, **k: httpx.Response(
            200, json={"candidates": [{"finishReason": "MAX_TOKENS"}]}
        ),
    )
    cfg = SimpleNamespace(gemini_api_key="test-secret", gemini_model="gemini-2.5-flash")
    with pytest.raises(RuntimeError, match="complete plan"):
        generate_plan(cfg, "", "", {}, {})


def test_langfuse_callback_dependency_available():
    from langfuse.langchain import CallbackHandler

    assert CallbackHandler is not None
