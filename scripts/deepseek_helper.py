"""DeepSeek API 헬퍼 CLI.

DeepSeek는 OpenAI 호환 REST API(https://api.deepseek.com)를 제공하므로
별도 SDK 없이 requests만으로 호출한다.

사용 전 준비:
    1. 프로젝트 루트에 .env 파일을 만들고 다음을 채운다.
         DEEPSEEK_API_KEY=발급받은_키
         DEEPSEEK_MODEL=deepseek-flash   # DeepSeek Flash 모델(V4.1 Flash)의 API 모델 ID
    2. python scripts/deepseek_helper.py <서브커맨드> ...

서브커맨드:
    chat                          대화형 REPL (대화 맥락 유지, /exit 로 종료)
    ask "질문"                    한 번만 질의
    summarize <파일> [--lang ko|en]   PDF/MD/TXT/HTML 문서를 요약
    translate <파일> --to en|ko [--out 경로]  문서를 번역
    analyze <파일> [--question "질문"]        코드/데이터 파일 분석 보조
"""

import argparse
import html
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

API_URL = "https://api.deepseek.com/chat/completions"
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")

CHUNK_CHARS = 40_000
MAX_TOKENS = 4096


def call_deepseek(messages: list[dict], max_tokens: int = MAX_TOKENS) -> str:
    if not API_KEY:
        sys.exit(
            "DEEPSEEK_API_KEY가 설정되어 있지 않습니다. "
            "프로젝트 루트의 .env 파일에 DEEPSEEK_API_KEY=... 를 추가하세요."
        )
    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": False,
        },
        timeout=120,
    )
    if resp.status_code != 200:
        sys.exit(f"DeepSeek API 오류 ({resp.status_code}): {resp.text}")
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix in (".html", ".htm"):
        raw = path.read_text(encoding="utf-8", errors="ignore")
        text = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        return html.unescape(text)
    return path.read_text(encoding="utf-8", errors="ignore")


def chunk_text(text: str, size: int = CHUNK_CHARS) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


def cmd_chat(_args):
    print(f"DeepSeek 대화형 모드 (model={MODEL}). 종료하려면 /exit 입력.\n")
    history = []
    while True:
        try:
            user_input = input("나: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input in ("/exit", "/quit"):
            break
        if not user_input:
            continue
        history.append({"role": "user", "content": user_input})
        reply = call_deepseek(history)
        history.append({"role": "assistant", "content": reply})
        print(f"\nDeepSeek: {reply}\n")


def cmd_ask(args):
    reply = call_deepseek([{"role": "user", "content": args.prompt}])
    print(reply)


def cmd_summarize(args):
    path = Path(args.file)
    text = extract_text(path)
    lang_label = "한국어" if args.lang == "ko" else "English"
    chunks = chunk_text(text)

    if len(chunks) == 1:
        prompt = f"다음 문서를 {lang_label}로 핵심만 간결하게 요약해줘:\n\n{chunks[0]}"
        print(call_deepseek([{"role": "user", "content": prompt}]))
        return

    partial_summaries = []
    for i, chunk in enumerate(chunks, 1):
        print(f"[{i}/{len(chunks)}] 부분 요약 중...", file=sys.stderr)
        prompt = f"다음은 긴 문서의 {i}번째 조각이다. 핵심 내용을 간결히 정리해줘:\n\n{chunk}"
        partial_summaries.append(call_deepseek([{"role": "user", "content": prompt}]))

    combine_prompt = (
        f"아래는 하나의 문서를 조각내어 각각 요약한 결과들이다. "
        f"이를 종합하여 {lang_label}로 하나의 일관된 최종 요약을 작성해줘:\n\n"
        + "\n\n---\n\n".join(partial_summaries)
    )
    print(call_deepseek([{"role": "user", "content": combine_prompt}]))


def cmd_translate(args):
    path = Path(args.file)
    text = extract_text(path)
    target = "영어" if args.to == "en" else "한국어"
    chunks = chunk_text(text)

    translated_parts = []
    for i, chunk in enumerate(chunks, 1):
        print(f"[{i}/{len(chunks)}] 번역 중...", file=sys.stderr)
        prompt = f"다음 텍스트를 {target}로 자연스럽게 번역해줘. 원문 구조(문단, 목록 등)를 유지해줘:\n\n{chunk}"
        translated_parts.append(call_deepseek([{"role": "user", "content": prompt}]))

    result = "\n\n".join(translated_parts)
    if args.out:
        Path(args.out).write_text(result, encoding="utf-8")
        print(f"번역 결과를 {args.out} 에 저장했습니다.", file=sys.stderr)
    else:
        print(result)


def cmd_analyze(args):
    path = Path(args.file)
    content = extract_text(path)
    question = args.question or "이 파일의 내용을 분석하고 주요 특징, 잠재적 문제, 개선점을 알려줘."
    chunks = chunk_text(content)
    if len(chunks) > 1:
        print(
            f"경고: 파일이 커서 첫 {CHUNK_CHARS}자만 분석에 사용합니다.",
            file=sys.stderr,
        )
    prompt = f"다음 파일 내용을 보고 질문에 답해줘.\n\n[질문]\n{question}\n\n[파일 내용]\n{chunks[0]}"
    print(call_deepseek([{"role": "user", "content": prompt}]))


def main():
    parser = argparse.ArgumentParser(description="DeepSeek API 헬퍼 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("chat").set_defaults(func=cmd_chat)

    p_ask = sub.add_parser("ask")
    p_ask.add_argument("prompt")
    p_ask.set_defaults(func=cmd_ask)

    p_sum = sub.add_parser("summarize")
    p_sum.add_argument("file")
    p_sum.add_argument("--lang", choices=["ko", "en"], default="ko")
    p_sum.set_defaults(func=cmd_summarize)

    p_tr = sub.add_parser("translate")
    p_tr.add_argument("file")
    p_tr.add_argument("--to", choices=["ko", "en"], required=True)
    p_tr.add_argument("--out")
    p_tr.set_defaults(func=cmd_translate)

    p_an = sub.add_parser("analyze")
    p_an.add_argument("file")
    p_an.add_argument("--question")
    p_an.set_defaults(func=cmd_analyze)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
