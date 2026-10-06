"""AI에게 보낼 프롬프트(시스템/사용자)를 구성하는 모듈 (미션 4-3, 4-4).

- 시스템 프롬프트: 역할 + 규칙(형식/길이/추측 금지) + 출력 형식 고정
- 사용자 프롬프트: 이번 실행의 컨텍스트(브랜치, 변경 파일 목록, diff)
"""

COMMIT_SYSTEM = """당신은 Git 커밋 메시지 작성 도우미입니다.
규칙:
- 제목은 '<type>: <요약>' 형식이며, type은 feat/fix/docs/refactor/test/chore 중 하나
- 제목은 50자 이내(최대 72자), 마침표 없음, 한국어
- 본문은 '- '로 시작하는 불릿 1~3개, 변경된 파일/모듈명을 1~3개 언급
- diff에 없는 내용은 추측하지 않는다
출력 형식(이 형식 외 다른 텍스트 금지):
TITLE: <제목>
BODY:
- <불릿>"""

PR_SYSTEM = """당신은 Pull Request 설명 작성 도우미입니다.
규칙:
- 제목은 80자 이내 1줄, 한국어
- 본문은 아래 3개 섹션 헤더를 반드시 포함, 각 섹션에 '- ' 불릿 1개 이상
- diff에 없는 내용은 추측하지 않는다
출력 형식(이 형식 외 다른 텍스트 금지):
TITLE: <제목>
BODY:
## Why
- <변경 배경>
## What
- <핵심 변경 사항>
## How to Test
- <테스트 방법>
"""


def build_user_prompt(
    files: list[str],
    diff: str,
    branch: str | None = None,
) -> str:
    """git 수집 결과를 AI가 읽기 좋은 구획 형태의 텍스트로 만든다.

    반환 예 (branch="feature/x", files=["M  main.py"], diff="+print(1)"):
        [현재 브랜치]
        feature/x

        [변경 파일 목록 (git status)]
        M  main.py

        [변경 내용 (git diff)]
        +print(1)
    """

    parts = []
    if branch:
        parts.append(f"[현재 브랜치]\n{branch}")
    parts.append("[변경 파일 목록 (git status)]\n" + "\n".join(files))
    parts.append(f"[변경 내용 (git diff)]\n{diff}")
    return "\n\n".join(parts)
