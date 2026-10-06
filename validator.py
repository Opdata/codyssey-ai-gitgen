"""AI 응답을 파싱하고 출력 형식 규칙을 검증·후처리하는 모듈 (미션 4-5).

방식: 후처리 (재요청 없이 고쳐서 출력 → 1회 실행 = API 1회 호출 유지, 미션 7장 권장)
"""

import re

COMMIT_TITLE_RECOMMENDED = 50  # 미션 4-5: 커밋 제목 50자 이내 권장
COMMIT_TITLE_MAX = 72  # 미션 4-5: 최대 72자
PR_TITLE_MAX = 80  # 미션 4-5: PR 제목 최대 80자
PR_SECTIONS = ["Why", "What", "How to Test"]  # 미션 4-4: 필수 섹션 헤더


def parse(text: str) -> tuple[str, str]:
    """AI 응답에서 (제목, 본문) 을 꺼낸다.

    기대 형식:
        TITLE: <제목>
        BODY:
        <본문 여러 줄>
    TITLE: 이 없으면(AI가 형식을 어긴 경우) 첫 줄을 제목, 나머지를 본문으로 본다.
    """

    title_m = re.search(r"^TITLE:\s*(.+)$", text, re.MULTILINE)
    body_m = re.search(r"^BODY:\s*\n?(.*)", text, re.MULTILINE | re.DOTALL)
    if title_m:
        title = title_m.group(1).strip()
        body = body_m.group(1).strip() if body_m else ""
        return title, body
    lines = [l for l in text.splitlines() if l.strip()]
    return (lines[0].strip() if lines else ""), "\n".join(lines[1:]).strip()


def _truncate(title: str, max_len: int) -> tuple[str, bool]:
    """제목이 max_len 을 넘으면 잘라서 끝에 '…' 를 붙인다. (결과 제목, 잘랐는지) 반환."""

    if len(title) <= max_len:
        return title, False
    return title[: max_len - 1].rstrip() + "…", True


def validate_commit(title: str, body: str) -> tuple[str, str, list[str]]:
    """커밋 제목/본문을 검증·후처리한다. (제목, 본문, 경고 목록) 반환.

    - 제목 없음      → ValueError (미션 4-3: 제목 1줄 필수)
    - 72자 초과      → 잘라내고 경고
    - 50자 초과      → 경고만 (권장 기준)
    - 본문에 불릿 없음 → 경고 (미션 4-3: 본문을 포함한다면 불릿/파일 언급)
    """

    warnings = []
    if not title:
        raise ValueError("AI 응답에서 커밋 제목을 찾지 못했습니다.")
    title, cut = _truncate(title, COMMIT_TITLE_MAX)
    if cut:
        warnings.append(f"커밋 제목이 {COMMIT_TITLE_MAX}자를 초과해 잘랐습니다.")
    elif len(title) > COMMIT_TITLE_RECOMMENDED:
        warnings.append(
            f"커밋 제목이 권장 {COMMIT_TITLE_RECOMMENDED}자를 초과합니다({len(title)}자)."
        )
    if body and not re.search(r"^\s*[-*]\s+\S", body, re.MULTILINE):
        warnings.append("커밋 본문에 불릿(- )이 없습니다.")
    return title, body, warnings


def _split_sections(body: str) -> dict[str, list[str]]:
    """PR 본문을 섹션별 불릿 목록으로 나눈다.

    예) "## Why\\n- a\\n\\n## What(핵심)\\n* b"  →  {"Why": ["- a"], "What": ["- b"]}
    - 헤더는 #~###### 아무거나, 뒤에 (설명)이 붙어도 이름이 그걸로 시작하면 인정
    - 불릿은 '- ' 또는 '* ' 모두 인정하고 '- ' 로 통일
    - 빈 줄, 섹션 밖의 줄, 불릿이 아닌 줄은 무시
    """

    sections = {}
    current = None
    for line in body.splitlines():
        header = re.match(r"^#{1,6}\s*(.+?)\s*$", line)
        if header:
            name = header.group(1).lower()
            current = next((s for s in PR_SECTIONS if name.startswith(s.lower())), None)
            continue
        bullet = re.match(r"^\s*[-*]\s+(\S.*)$", line)
        if current and bullet:
            sections.setdefault(current, []).append("- " + bullet.group(1).strip())
    return sections


def validate_pr(title: str, body: str) -> tuple[str, str, list[str]]:
    """PR 제목/본문을 검증·후처리한다. (제목, 정리된 본문, 경고 목록) 반환.

    - 제목 없음 → ValueError
    - 80자 초과 → 잘라내고 경고
    - 본문은 Why/What/How to Test 순서로 다시 조립
      섹션이 없거나 불릿이 없으면 '- (작성 필요)' 를 넣고 경고 (미션 4-4: 각 섹션 최소 1개 불릿)
    """

    warnings = []
    if not title:
        raise ValueError("AI 응답에서 PR 제목을 찾지 못했습니다.")
    title, cut = _truncate(title, PR_TITLE_MAX)
    if cut:
        warnings.append(f"PR 제목이 {PR_TITLE_MAX}자를 초과해 잘랐습니다.")
    sections = _split_sections(body)
    blocks = []
    for name in PR_SECTIONS:
        bullets = sections.get(name)
        if not bullets:
            warnings.append(
                f"'{name}' 섹션이 없거나 불릿이 없어 기본 불릿을 추가했습니다."
            )
            bullets = ["- (작성 필요)"]
        blocks.append(f"## {name}\n" + "\n".join(bullets))
    return title, "\n\n".join(blocks), warnings
