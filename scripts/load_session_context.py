"""SessionStart hook — 새 세션 시작 시 직전 세션 기록을 컨텍스트로 불러온다.

`Claude outputs/` 의 가장 최근 `세션_작업기록_*.md` 를 찾아 그 경로와 앞부분을
Claude 의 컨텍스트에 주입한다. 그래서 프로그램을 다시 열면 이전 작업 맥락을
따로 말해주지 않아도 이어받을 수 있다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "Claude outputs"

HEAD_CHARS = 1500


def emit(context: str | None) -> None:
    out: dict = {"hookSpecificOutput": {"hookEventName": "SessionStart"}}
    if context:
        out["hookSpecificOutput"]["additionalContext"] = context
    print(json.dumps(out, ensure_ascii=False))


def main() -> None:
    # stdin 은 읽고 버린다 (훅 규약상 JSON 이 들어온다).
    try:
        sys.stdin.read()
    except Exception:
        pass

    if not OUTPUT_DIR.is_dir():
        emit(None)
        return

    records = sorted(
        OUTPUT_DIR.glob("세션_작업기록_*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not records:
        emit(None)
        return

    latest = records[0]
    rel = latest.relative_to(PROJECT_ROOT).as_posix()
    head = latest.read_text(encoding="utf-8", errors="ignore")[:HEAD_CHARS]

    others = "\n".join(
        f"  - {p.relative_to(PROJECT_ROOT).as_posix()}" for p in records[1:6]
    )

    context = (
        "이 프로젝트에는 이전 세션 기록이 보관되어 있다. "
        "사용자가 이전 작업의 연속을 요청하면 아래 파일을 먼저 읽을 것.\n\n"
        f"가장 최근 기록: `{rel}`\n\n"
        f"--- 앞부분 미리보기 ---\n{head}\n--- (이하 생략, 전체는 파일을 읽을 것) ---\n"
    )
    if others:
        context += f"\n이전 기록들:\n{others}\n"

    emit(context)


if __name__ == "__main__":
    main()
