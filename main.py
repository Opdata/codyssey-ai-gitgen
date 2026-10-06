"""AI 기반 Git 커밋/PR 초안 생성기 — CLI 진입점.

사용법:
    python3 main.py commit [--model M] [--temperature T] [--max-tokens N] [--safe-mode]
    python3 main.py pr     [--model M] [--temperature T] [--max-tokens N] [--safe-mode]
"""

import argparse
import sys

from ai_client import DEFAULT_MODEL, AIError, call_ai, get_api_key
from git_collector import GitError, collect_diff, collect_status, ensure_repo_root
from masker import mask
from prompt_builder import COMMIT_SYSTEM, PR_SYSTEM, build_user_prompt
from validator import parse, validate_commit, validate_pr

LINE = "-" * 40  # 출력 구획 구분선 (미션 4-5)


def build_parser() -> argparse.ArgumentParser:
    """commit / pr 서브커맨드와 공통 옵션을 정의한다. (정형 코드 — 그대로 사용)"""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"모델명 (기본: {DEFAULT_MODEL})"
    )
    common.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="0.0~2.0, 낮을수록 일관됨 (기본: 0.2)",
    )
    common.add_argument(
        "--max-tokens", type=int, default=500, help="최대 출력 토큰 수 (기본: 500)"
    )
    common.add_argument(
        "--safe-mode",
        action="store_true",
        help="diff 의 API Key/이메일 등을 마스킹 후 전송",
    )

    parser = argparse.ArgumentParser(description="AI 기반 Git 커밋/PR 초안 생성기")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("commit", parents=[common], help="커밋 메시지 생성")
    sub.add_parser("pr", parents=[common], help="PR 제목/본문 생성")
    return parser


def print_commit(title: str, body: str) -> None:
    """커밋 메시지를 구획을 나눠 출력한다. (미션 8장 출력 예시 형태)"""

    print("[DONE] 커밋 메시지 생성 완료\n")
    print("--- Commit Message ---")
    print(title)
    if body:
        print(f"\n{body}")
    print(LINE)


def print_pr(title: str, body: str) -> None:
    """PR 제목/본문을 구획을 나눠 출력한다. (미션 8장 출력 예시 형태)"""

    print("[DONE] PR 초안 생성 완료\n")
    print("--- PR Title ---")
    print(title)
    print("\n--- PR Body ---")
    print(body)
    print(LINE)


def run(args: argparse.Namespace) -> int:
    """수집 → (마스킹) → 프롬프트 → AI 호출 → 검증 → 출력. 종료 코드(0 성공, 1 실패) 반환.

    오류는 여기서 잡지 않고 main() 으로 올려보낸다.
    """

    # 옵션 검사
    if args.temperature < 0.0 or args.temperature > 2.0:
        print("[ERROR] --temperature는 0.0~2.0 범위여야 합니다.")
        return 1
    if args.max_tokens < 1:
        print("[ERROR] --max-tokens는 1 이상이어야 합니다.")
        return 1

    # Git 변경 사항 수집
    ensure_repo_root()
    branch, files = collect_status()
    print(f"[INFO] Git status 수집 완료: {len(files)}개 파일 변경 감지")
    if not files:
        print("[INFO] 변경 사항이 없습니다. 생성하지 않고 종료합니다.")
        return 0
    diff = collect_diff()
    print(f"[INFO] Git diff 수집 완료: {len(diff.splitlines())}줄")
    if not diff:
        print(
            "[WARN] diff가 비어 있습니다. 새 파일은 git add 후 실행하면 내용이 반영됩니다."
        )

    # safe-mode 마스킹
    if args.safe_mode:
        diff, masked = mask(diff)
        files = [mask(f)[0] for f in files]
        print(f"[INFO] safe-mode: 민감정보 {masked}건 마스킹")

    # 프롬프트 구성
    get_api_key()
    if args.command == "commit":
        system, user = COMMIT_SYSTEM, build_user_prompt(files, diff)
    else:
        print(f"[INFO] 현재 브랜치: {branch}")
        system, user = PR_SYSTEM, build_user_prompt(files, diff, branch)

    # AI 호출
    print(
        f"[INFO] AI API 요청 중... (model={args.model}, temperature={args.temperature}, max_tokens={args.max_tokens})"
    )
    text, finish = call_ai(system, user, args.model, args.temperature, args.max_tokens)
    print("[INFO] API 호출 횟수: 1")

    if finish == "MAX_TOKENS":
        print(
            "[WARN] max_tokens에 도달해 응답이 잘렸을 수 있습니다. --max-tokens를 늘려보세요."
        )

    # 검증 후처리 후 출력
    title, body = parse(text)
    if args.command == "commit":
        title, body, warnings = validate_commit(title, body)
        print_commit(title, body)
    else:
        title, body, warnings = validate_pr(title, body)
        print_pr(title, body)
    for w in warnings:
        print(f"[WARN] {w}")
    return 0


def main() -> int:
    """인자를 해석하고 run() 을 실행한다. 예상된 오류는 [ERROR] 한 줄로 출력하고 1 반환."""

    args = build_parser().parse_args()
    try:
        return run(args)
    except (GitError, AIError, ValueError) as e:
        print(f"[ERROR] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
