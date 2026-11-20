# DeepSeek API 위임 규칙

이 프로젝트에는 DeepSeek API를 호출하는 헬퍼 스크립트가 있다: [scripts/deepseek_helper.py](scripts/deepseek_helper.py)
(API 키는 `.env`에 있고 `.gitignore`로 보호됨. 사용 모델: `deepseek-flash`)

사용자가 대화 중 "DeepSeek한테 ~시켜줘", "딥시크로 ~해줘"처럼 DeepSeek을 지목해서 요청하면,
Claude(Sonnet)가 직접 답하지 말고 Bash 툴로 이 스크립트를 실행해 DeepSeek의 응답을 받아온 뒤
그 결과를 사용자에게 보여준다. 아래는 요청 유형별 매핑이다.

| 사용자 요청 유형 | 실행 명령 |
|---|---|
| 자유 질의/대화 | `python scripts/deepseek_helper.py ask "질문"` |
| 문서/PDF 요약 | `python scripts/deepseek_helper.py summarize "파일경로" --lang ko` |
| 번역 | `python scripts/deepseek_helper.py translate "파일경로" --to en` (또는 `ko`) |
| 코드/데이터 분석 보조 | `python scripts/deepseek_helper.py analyze "파일경로" --question "질문"` |

규칙:
- 파일 경로에 공백이나 한글이 포함되면 반드시 따옴표로 감싼다.
- 스크립트가 `DeepSeek API 오류`로 실패하면 `.env`의 `DEEPSEEK_API_KEY`/`DEEPSEEK_MODEL` 설정을 먼저 확인하고,
  임의로 코드를 수정하기 전에 오류 메시지를 그대로 사용자에게 보고한다.
- 이 호출은 Claude Code 자체의 모델을 바꾸는 것이 아니라, 별도 프로세스로 DeepSeek API를 한 번 호출하는 것이다.
  Claude(Sonnet)는 계속 대화의 주 진행자 역할을 유지하며, DeepSeek의 응답은 참고 자료로 통합해 전달한다.
- 대화형 `chat` 서브커맨드는 REPL이라 자동화된 단발성 호출에는 적합하지 않으므로,
  Claude가 사용자를 대신해 실행할 때는 `ask`/`summarize`/`translate`/`analyze`만 사용한다.
