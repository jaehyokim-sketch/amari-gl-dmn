"""SessionEnd hook — 세션 종료 시 대화 기록을 프로젝트 폴더에 자동 보관한다.

Claude Code 가 세션을 끝낼 때(창/폴더 닫기 포함) stdin 으로 넘겨주는 JSON 을 읽어
트랜스크립트(JSONL)를 `Claude outputs/session-logs/` 로 복사하고, 사람이 읽을 수 있는
질문 목록 인덱스를 함께 갱신한다.

한계: 훅은 셸 명령이라 요약을 "작성"할 수는 없다. 이 스크립트가 남기는 것은
**원본 백업과 기계적 인덱스**이며, 큐레이션된 세션 요약
(`Claude outputs/세션_작업기록_*.md`)은 Claude 에게 직접 요청해서 만들어야 한다.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "Claude outputs" / "session-logs"

MAX_PROMPT_CHARS = 300
SKIP_PREFIXES = ("<system-reminder>", "<command-name>", "<local-command-")


def emit(message: str) -> None:
    """훅 결과를 Claude Code UI 에 한 줄로 알린다."""
    print(json.dumps({"systemMessage": message}, ensure_ascii=False))


def user_prompts(transcript: Path) -> list[tuple[str, str]]:
    """트랜스크립트에서 (시각, 사용자 발화) 목록을 뽑는다."""
    out: list[tuple[str, str]] = []
    with transcript.open(encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") != "user":
                continue

            content = (rec.get("message") or {}).get("content")
            if isinstance(content, list):
                texts = [b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text"]
                text = "\n".join(t for t in texts if t)
            elif isinstance(content, str):
                text = content
            else:
                continue

            text = text.strip()
            if not text or text.startswith(SKIP_PREFIXES):
                continue

            stamp = (rec.get("timestamp") or "")[:19].replace("T", " ")
            if len(text) > MAX_PROMPT_CHARS:
                text = text[:MAX_PROMPT_CHARS] + " …"
            out.append((stamp, text.replace("\n", " ")))
    return out


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    raw_path = payload.get("transcript_path")
    if not raw_path:
        emit("세션 기록 보관 건너뜀: transcript_path 없음")
        return

    transcript = Path(raw_path)
    if not transcript.is_file():
        emit(f"세션 기록 보관 실패: 트랜스크립트를 찾을 수 없음 ({transcript.name})")
        return

    session_id = str(payload.get("session_id") or transcript.stem)
    today = datetime.now().strftime("%Y-%m-%d")
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    dest = LOG_DIR / f"{today}_{session_id[:8]}.jsonl"
    shutil.copy2(transcript, dest)

    prompts = user_prompts(transcript)
    index = LOG_DIR / f"{today}_{session_id[:8]}_질문목록.md"
    lines = [
        f"# 세션 질문 목록 — {today}",
        "",
        f"> 세션 ID: `{session_id}`",
        f"> 원본 트랜스크립트: `{dest.name}`",
        f"> 보관 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "이 파일은 SessionEnd 훅이 자동 생성한 **기계적 인덱스**다.",
        "내용을 해석한 요약은 `Claude outputs/세션_작업기록_*.md` 를 참조할 것.",
        "",
        "---",
        "",
    ]
    if prompts:
        for i, (stamp, text) in enumerate(prompts, 1):
            lines.append(f"{i}. `{stamp}` — {text}")
    else:
        lines.append("_사용자 발화를 찾지 못했다._")
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")

    size_mb = dest.stat().st_size / 1_048_576
    emit(f"세션 기록 보관 완료 → Claude outputs/session-logs/{dest.name} "
         f"({size_mb:.1f} MB, 질문 {len(prompts)}건)")


if __name__ == "__main__":
    main()
