"""safe-mode: diff 의 민감정보 마스킹 (미션 7장 보안/민감정보).

미션 7장: 아래 중 1개 이상을 --safe-mode 옵션으로 제공
  (A) 특정 패턴(API Key 형태, 이메일 등) 마스킹 후 전송  → mask()  ← 채택
  (B) diff 일부만 전송                                    → 미채택 (선택 항목)
"""

import re

# (정규식, 바꿀 문자열) 쌍의 목록. 위에서부터 순서대로 적용한다.
PATTERNS = [
    # key=value 형태: API_KEY="abc", password: abc, token = 'abc' → 값만 [MASKED]
    (
        re.compile(
            r"(?i)((?:api[_-]?key|secret|token|password)\s*[:=]\s*)(['\"]?)[^\s'\"]+\2"
        ),
        r"\1\2[MASKED]\2",
    ),
    # Google API Key (AIza + 35자)
    (re.compile(r"AIza[0-9A-Za-z_\-]{35}"), "[MASKED_API_KEY]"),
    # OpenAI/Anthropic 계열 키 (sk- 로 시작)
    (re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "[MASKED_API_KEY]"),
    # AWS Access Key
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[MASKED_AWS_KEY]"),
    # 이메일
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[MASKED_EMAIL]"),
]


def mask(text: str) -> tuple[str, int]:
    """PATTERNS 를 순서대로 적용해 민감정보를 가린다. (가린 텍스트, 가린 개수) 반환."""

    total = 0
    for pattern, repl in PATTERNS:
        text, n = pattern.subn(repl, text)
        total += n
    return text, total
