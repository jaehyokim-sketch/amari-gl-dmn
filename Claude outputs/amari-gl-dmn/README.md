# 확장 Amari-GL 방정식 · DMN + Claustrum 장거리 상관 시뮬레이션

비평형 열역학적 산일구조(Prigogine) 관점에서 Default Mode Network 의 발현을
확장 Amari–Ginzburg–Landau 방정식으로 모사하고, Balloon–Windkessel 혈역학
순방향 모델을 거친 BOLD rsFC 를 문헌 FC 및 OpenNeuro 실측과 비교한다.

게시된 논문: <https://claude.ai/artifact/5x7jEdNb7Sw7yA1VZzc28S> (Version 7)

---

## VS Code 에서 시작하기

### 1. 폴더 열기

Google Drive 데스크톱 동기화 폴더에서 `amari-gl-dmn` 을 VS Code 로 연다.
(`파일 → 폴더 열기…`, 또는 터미널에서 `code amari-gl-dmn`)

### 2. Python 환경

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

VS Code 에서 `Ctrl/Cmd + Shift + P` → `Python: Select Interpreter` →
`.venv` 를 선택하면 편집기가 `src` 를 인식한다.

### 3. 실행 확인

```bash
python scripts/run_simulation.py
python -m pytest tests/ -q
```

검증표 7개 항목과 문헌 FC 일치도 r 이 출력되면 정상이다.

### 4. Claude Code 연결 (선택)

VS Code 확장 마켓플레이스에서 **Claude Code** 를 설치하고 이 폴더에서 실행하면,
`CLAUDE.md` 를 자동으로 읽어 연구 맥락(모델식·파라미터·금지사항·다음 작업)을
이어받는다. 클라우드 세션의 세션 ID 자체는 이어지지 않지만, 작업 맥락은
`CLAUDE.md` 와 `docs/` 가 전달한다.

---

## 주요 명령

| 목적 | 명령 |
|---|---|
| 기본 실행 + 문헌 검증표 | `python scripts/run_simulation.py` |
| 유한표본 잡음 제거 | `python scripts/run_simulation.py --ensemble 30` |
| 파라미터 변경 | `python scripts/run_simulation.py --sigma 1.25 --beta 0.80 --ensemble 10` |
| σ×β 스윕 + 히트맵 | `python scripts/param_sweep.py --sigma 0.95 1.45 11 --beta 0.3 1.3 11` |
| 그림 4종 생성 | `python scripts/plot_results.py --ensemble 10` |
| 포팅 무결성 테스트 | `python -m pytest tests/ -q` |
| 결과 저장 | `python scripts/run_simulation.py --save results/run1` |

---

## 모델 개요

```
τ dφᵢ/dt = (σ−1)φᵢ − φᵢ³ + Σⱼ Cᵢⱼ(φⱼ−φᵢ) − β·⟨φ⟩ + ηᵢ(t)
```

17 노드 = DMN 6 (mPFC, PCC, L/R_AG, L/R_MTG) + TPN 6 (L/R_dlPFC, L/R_FEF, L/R_IPS)
+ SAL 3 (ACC, L/R_AI) + CLA 2 (L/R_CLA).

구조적 연결 `C` 는 **전 성분 비음수**다. DMN–TPN 반상관은 입력이 아니라
전역 억압 `−β⟨φ⟩` 를 통해 창발해야 하며, 이것이 이 연구의 핵심 주장이다.

기본 파라미터는 σ=0.985, β=0.45, noise=0.09, DT=0.08s 이다.
다만 **`docs/PORTING_NOTES.md` §3 에 σ·β 재검토 권고가 있다** — 네트워크 임계점이
σ=1 이 아니라 σ\*=1.3809 이며, σ=1.25 / β=0.80 이 검증 7/7 을 통과한다.

---

## 저장소 구조

```
CLAUDE.md          Claude Code 용 프로젝트 맥락 (작업 규칙 포함)
src/               시뮬레이션 코어 (원본 JS 에서 1:1 포팅)
scripts/           실행·스윕·시각화 스크립트
tests/             포팅 무결성 테스트 22항목
artifact/          amari_gl_v7.html — 게시된 논문 원본
docs/              PORTING_NOTES.md · 세션_연속성_기록.md · 선행연구_비교정리.md
results/           생성물 (git 추적 제외)
```

> Drive 사본에는 용량 문제로 `artifact/amari_gl_v7.html` 이 빠져 있다.
> 대화창에 첨부된 `amari-gl-dmn.zip` 안에 들어 있으며,
> 게시된 Artifact URL 에서도 확인할 수 있다.

## 논문 원본 편집

`artifact/amari_gl_v7.html` 는 게시된 Artifact 의 소스다. VS Code 에서 편집할 수는
있으나, claude.ai 의 페이지에 반영하려면 같은 URL 로 **재게시**해야 한다
(Cowork 세션 또는 claude.ai 에서 수행). 브라우저로 직접 열면 로컬에서
인터랙티브 시뮬레이션을 그대로 확인할 수 있다.

---

## 요구사항

Python 3.10 이상, numpy · scipy · matplotlib · pytest (`requirements.txt` 참조).
