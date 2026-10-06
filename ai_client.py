"""Gemini API(generateContent)를 REST 방식으로 호출하는 모듈 (미션 4-2)."""

import json
import os
import urllib.error
import urllib.request

API_KEY_ENV = "AI_API_KEY"
API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
DEFAULT_MODEL = "gemini-3.1-flash-lite"

# HTTP 상태 코드 → 사용자에게 보여줄 원인 설명
# (Gemini는 잘못된 키에 401이 아니라 400 "API key not valid" 를 돌려준다 — 실측)
HTTP_REASONS = {
    400: "잘못된 요청 (API Key 또는 파라미터 확인)",
    401: "인증 실패 (API Key 확인)",
    403: "권한 없음 (키의 API 사용 권한 확인)",
    404: "모델을 찾을 수 없음 (--model 값 확인)",
    429: "요청 한도 초과 (잠시 후 재시도)",
    500: "AI 서버 내부 오류",
    503: "AI 서버 과부하 (잠시 후 재시도)",
}


class AIError(Exception):
    """API Key 미설정, 네트워크 오류, HTTP 오류, 응답 형식 오류 등 AI API 관련 오류."""


def get_api_key() -> str:
    """환경변수 AI_API_KEY 에서 키를 읽어 반환한다. 없으면 AIError."""

    key = os.environ.get(API_KEY_ENV)
    if not key:
        raise AIError(
            f'{API_KEY_ENV} 환경변수가 설정되지 않았습니다.\n예) export {API_KEY_ENV}="YOUR_KEY"'
        )
    return key


def build_body(system: str, user: str, temperature: float, max_tokens: int) -> dict:
    """Gemini generateContent 요청 본문(dict)을 만든다.

    완성 형태:
    {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    """

    return {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }


def extract_text(data: dict) -> tuple[str, str]:
    """응답 JSON(dict)에서 (생성된 텍스트, finishReason) 을 꺼낸다.

    응답 형태:
    {
        "candidates": [
            {"content": {"parts": [{"text": "..."}, ...]}, "finishReason": "STOP"}
        ],
        "usageMetadata": {...}
    }
    finishReason: "STOP"(정상 종료), "MAX_TOKENS"(max_tokens 도달로 잘림), "SAFETY"(차단) 등
    """

    try:
        candidate = data["candidates"][0]
    except (KeyError, IndexError):
        raise AIError(
            f"응답 형식이 예상과 다릅니다: {json.dumps(data, ensure_ascii=False)[:300]}"
        )
    parts = candidate.get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts)
    finish = candidate.get("finishReason", "")
    return text.strip(), finish


def call_ai(
    system: str,
    user: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 500,
    timeout: int = 60,
) -> tuple[str, str]:
    """Gemini API를 1회 호출하고 (생성된 텍스트, finishReason) 을 반환한다.

    흐름: 요청 구성 → 전송 → 응답 파싱 → 예외를 AIError 로 변환
    """

    req = urllib.request.Request(
        API_URL.format(model=model),
        data=json.dumps(build_body(system, user, temperature, max_tokens)).encode(
            "utf-8"
        ),
        headers={"x-goog-api-key": get_api_key(), "content-type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        reason = HTTP_REASONS.get(e.code, "알 수 없는 오류")
        raise AIError(f"HTTP {e.code} {reason}: {detail}")
    except urllib.error.URLError as e:
        raise AIError(f"네트워크 오류: {e.reason}")
    except TimeoutError:
        raise AIError(f"응답 시간 초과 ({timeout}초)")

    return extract_text(data)
