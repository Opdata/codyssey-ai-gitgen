import os
import subprocess


class GitError(Exception):
    """git 실행 실패, 저장소 루트 아님 등 Git 관련 오류."""


def run_git(args: list[str]) -> str:
    """git 명령을 실행하고 표준출력(stdout)을 문자열로 반환한다.

    예) run_git(["status", "--porcelain", "-b"])  ->  "## main\\n?? a.txt\\n"
    실패하면 GitError 를 raise 한다.
    """

    try:
        result = subprocess.run(
            ["git", "-c", "core.quotepath=false", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except FileNotFoundError:
        raise GitError("git 명령을 찾을 수 없습니다. Git 설치 여부를 확인하세요.")

    if result.returncode != 0:
        raise GitError(result.stderr.strip() or f"git {' '.join(args)} 실행 실패")

    return result.stdout


def ensure_repo_root() -> None:
    """현재 작업 디렉토리가 Git 프로젝트 루트인지 확인한다 (미션 4-1).

    루트가 아니면 GitError 를 raise 한다.
    """

    if not os.path.exists(".git"):
        raise GitError("Git 프로젝트 루트 디렉토리에서 실행하세요. (.git 없음)")


def collect_status() -> tuple[str, list[str]]:
    """git status 를 실행해 (브랜치명, 변경 파일 목록) 을 반환한다.

    `git status --porcelain -b` 출력 예:
        ## main...origin/main      <- 첫 줄: 브랜치 정보
        M  main.py                 <- 이후: 변경 파일 한 줄씩
        ?? new.txt
    반환 예: ("main", ["M  main.py", "?? new.txt"])
    """

    output = run_git(["status", "--porcelain", "-b"])
    lines = output.splitlines()
    branch = ""
    if lines and lines[0].startswith("## "):
        header = lines.pop(0)[3:]
        header = header.replace("No commits yet on ", "")
        branch = header.split("...")[0].strip()
    files = [line for line in lines if line.strip()]
    return branch, files


def collect_diff() -> str:
    """staged(git add 된) + unstaged 변경 diff 를 합쳐서 반환한다.

    주의: 한 번도 add 안 한 새 파일(??)은 git diff 에 나오지 않는다.
    """

    staged = run_git(["diff", "--cached"])
    unstaged = run_git(["diff"])
    return staged + unstaged
