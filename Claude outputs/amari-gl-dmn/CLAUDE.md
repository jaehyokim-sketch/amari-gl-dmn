# CLAUDE.md — 확장 Amari-GL DMN+Claustrum 시뮬레이션

이 파일은 Claude Code 가 이 저장소에서 작업할 때 자동으로 읽는 프로젝트 맥락이다.
Cowork 클라우드 세션(2026-09-18 ~ 09-21, 세션 1–4)에서 진행한 연구를 VS Code 로
이관한 것이다.

## 연구자

교수 (medicdog@wku.ac.kr) · 원광대학교 한의과대학 (Wonkwang KMED Acu)
응답은 한국어로. 학술 문맥이므로 용어는 한글 + 영문 병기를 유지할 것.

## 무엇을 하는 프로젝트인가

프리고진(Prigogine)의 비평형 열역학적 **산일구조(dissipative structure)** 이론으로
Default Mode Network 의 발현을 설명한다. 확장 Amari–Ginzburg–Landau 방정식으로
17개 뇌 영역의 신경 동역학을 시뮬레이션하고, Balloon–Windkessel 혈역학 모델을 거쳐
얻은 BOLD rsFC 를 문헌 FC 및 OpenNeuro 실측과 정량 비교한다.

핵심 주장은 **DMN–TPN 반상관이 가정이 아니라 창발**이라는 것이다. 구조적 연결(SC)에는
양의 값만 넣고, 전역 억압항 −β⟨φ⟩ 만으로 반상관이 나오는지를 검증한다.
따라서 **SC 행렬에 음수를 넣는 수정은 이 연구의 전제를 무너뜨린다 — 절대 하지 말 것.**

## 지배 방정식

    τ dφᵢ/dt = (σ−1)φᵢ − φᵢ³ + Σⱼ Cᵢⱼ(φⱼ−φᵢ) − β·⟨φ⟩ + ηᵢ(t)

* `(σ−1)φ − φ³` — Ginzburg–Landau 포텐셜, 피치포크 분기
* `Σⱼ Cᵢⱼ(φⱼ−φᵢ)` — dMRI 기반 확산 결합 (전부 ≥ 0)
* `−β·⟨φ⟩` — 전역 억압. **반상관 창발의 유일한 기전**
* `ηᵢ(t)` — 가우시안 백색잡음

BOLD 는 Balloon–Windkessel 순방향 모델(Friston 2000)로 변환한다.

## 확정 파라미터 (v3 / Artifact V7)

| 구분 | 값 |
|---|---|
| Amari-GL | σ=0.985, β=0.45, noise=0.09, τ=1.0 |
| 적분 | DT=0.08s, warmup=60s, 실효 TR=0.56s |
| Balloon-Windkessel | κ=0.65, γ=0.41, τ_h=0.98s, α=0.32, E₀=0.4, V₀=0.04, k1=2.8, k2=2.0, k3=0.6 |
| 노드 | DMN 6 + TPN 6 + SAL 3 + CLA 2 = 17 |

**⚠️ σ·β 는 재검토 대상이다.** `docs/PORTING_NOTES.md` §3 참조 — 네트워크 임계점이
σ=1 이 아니라 **σ\* = 1.3809** 이며, σ=1.25/β=0.80 이 7/7 검증을 통과하고
r=0.93 을 낸다. 현재 값(0.985/0.45)은 5/7, r=0.90 이다.

## EMPR_FC 주요값 (V7 확정)

DMN 내부 +0.443 · TPN 내부 +0.425 · SAL 내부 +0.580 · DMN-TPN −0.199 · DMN-SAL +0.120
CLA-AI **+0.45** · CLA-ACC **+0.30** · CLA-mPFC +0.30 · L↔R CLA +0.55

CLA-ACC 는 V7 에서 0.35 → 0.30 으로 하향했다. 근거는 macaque BALSA
Area14→ACC FC = 0.05–0.23 (Autio 2020 + Yokoyama 2021). CLA-AI=0.45 는
macaque Area14→INSULA = 0.43 으로 검증되어 유지. **이 값을 되돌리지 말 것**
(`tests/test_port.py::test_v7_cla_values` 가 고정하고 있다).

## 저장소 구조

```
src/            시뮬레이션 코어 — 원본 JS 에서 포팅, 수식·상수 1:1 대응
  nodes.py         17-노드 MNI 파셀레이션
  connectivity.py  SC 행렬 + EMPR_FC 문헌 행렬
  amari_gl.py      Amari-GL 적분기 (Euler–Maruyama)
  balloon.py       Balloon–Windkessel 혈역학
  simulate.py      통합 러너 (JS simFrame 루프 재현)
  analysis.py      rsFC 상관·네트워크 블록·검증표 7항목
  plotting.py      한글 폰트 탐색 + 영문 폴백
scripts/        run_simulation.py · param_sweep.py · plot_results.py
tests/          test_port.py — 포팅 무결성 22항목
artifact/       amari_gl_v7.html — 게시된 논문 원본 (V7)
docs/           PORTING_NOTES.md · 세션_연속성_기록.md · 선행연구_비교정리.md
results/        생성물 (git 추적 안 함)
```

## 자주 쓰는 명령

```bash
python scripts/run_simulation.py                        # 기본 실행 + 검증표
python scripts/run_simulation.py --ensemble 30          # 유한표본 잡음 제거
python scripts/run_simulation.py --sigma 1.25 --beta 0.80 --ensemble 10
python scripts/param_sweep.py --sigma 0.95 1.45 11 --beta 0.3 1.3 11
python scripts/plot_results.py --ensemble 10
python -m pytest tests/ -q
```

## 작업 규칙

* **SC 에 음수를 넣지 않는다.** 반상관은 창발해야 한다.
* 파라미터를 바꾸면 `docs/PORTING_NOTES.md` 에 근거와 재현 명령을 남긴다.
* `EMPR_FC` 문헌값을 수정할 때는 반드시 출처(저자·연도·저널)를 주석으로 남긴다.
* 검증 지표는 두 가지다: ① 검증표 7항목 통과 수, ② 상삼각 136쌍 Pearson r.
  단일 실행 r 은 시드마다 ±0.02 흔들리므로 **파라미터 비교는 반드시 앙상블로** 한다.
* 그림 라벨은 `src/plotting.py` 의 `L("한글", "English")` 를 쓴다 — 한글 폰트가
  없는 환경에서 네모로 깨지지 않게 하기 위함이다.

## 게시된 논문 (Artifact)

https://claude.ai/artifact/5x7jEdNb7Sw7yA1VZzc28S — Version 7 (2026-09-19)

섹션: #abstract #intro #theory #method #result #hcp #dissipative #priorwork
#discussion #conclusion #refs

**Artifact 는 claude.ai 에 게시된 페이지이고 VS Code 에서 직접 갱신할 수 없다.**
`artifact/amari_gl_v7.html` 을 편집한 뒤, claude.ai 나 Cowork 세션에서 같은
URL 로 재게시해야 반영된다.

## 검증 이력

* ~~OpenNeuro ds000030 UCLA CNP, N=13~~ — **철회됨** (좌표계 오류, 위 ⚠ 절 참조)
* 시뮬 vs 문헌 합성행렬 r = 0.922 보고 — Python 재현값은 0.88–0.90
  (`docs/PORTING_NOTES.md` §2.1). **단 이 지표는 변별력이 없다** (N0 = 0.966).
* **실측 개인 데이터에 대한 검증은 아직 통과한 바 없다.** Phase 2 에서 수행 예정.

## ⚠ 현재 상태 — 외부 평가 반영 재검증 진행 중 (2026-09-21, Session 5)

외부 평가에서 **실증 검증의 정합성 문제**가 제기되었고, 코드 대조 결과 모두 사실로
확인되었다. 전체 경위·계획·결과는 **`docs/재검증_계획.md`** 를 먼저 읽을 것.

### 확정된 사실 (되돌리지 말 것)

* **SC 와 EMPR_FC 는 실측값이 아니다.** 둘 다 손으로 입력한 문헌 근사행렬이다.
  이전 판본이 "실측 dMRI"로 표기한 것은 오기이며 Phase 0 에서 정정했다.
  **다시 "실측"으로 되돌리지 말 것.**
* **OpenNeuro ds000030 검증(N=13)은 철회되었다.** N=13 은 `sform_code=1`
  (= 스캐너 공간, MNI 아님) 인 피험자만 남긴 표본이므로 MNI 좌표 적용이 무효다.
  r = 0.188 및 "SAL 신뢰성 있음" 판정을 **인용하지 말 것.**
* **Claustrum 2노드는 탐색적(Tier B)으로 강등되었다** (연구자 결정).
  정량 주장에 사용하지 않는다. CLA–AI≈0.45 는 19.4 mm 거리에서 평활화 누출만으로도
  재현 가능한 값이다.
* **연구자 결정**: 재분석으로 r 이 하락하는 상황을 수용한다. 결과를 유리하게
  재해석하지 말 것.

### Phase 1 결과 — 귀무모형 사다리 (`src/nulls.py`)

| 결론 | 근거 |
|---|---|
| **r = 0.922 는 모형 변별력이 없는 지표** | N0(블록 평균만) = 0.966 > 전체 모델 |
| **−φ³ 비선형항은 FC 에 기여하지 않음** | N4b(3차항만 제거) Δ = −0.002 / −0.003 |
| **SC 배선 패턴은 실제로 기여함** | N3(가중치 치환) 0.75 → 0.23 급락 |

→ **임계성·분기 논증을 rsFC 만으로 뒷받침할 수 없다.** 유지하려면 준안정성·눈사태
분포·엔트로피 생성률 등 선형/비선형이 갈라지는 관측량이 필요하다
(`docs/재검증_계획.md` §8.2).

## 다음 작업 후보

1. **Phase 2** — 동일 파이프라인 공개 커넥톰 확보 (ENIGMA Toolbox / Domhof 2022).
   `docs/재검증_계획.md` §4 경로 1. **EBRAINS 계정과 pip 설치 승인 필요.**
2. **Phase 3** — 전처리 대칭 비교 + β 절제 2×2 설계 (§3.3)
3. **Phase 4** — split-half 로 σ·β 재적합, Tier A 15노드 최종 검증
4. 참고문헌 [1]–[30] 확충 (#priorwork 출처 반영)
5. 영문 논문 초고 (선택) — 단 §8.4 의 재정의된 기여 범위에 맞춰 작성할 것

## 보안

* OpenNeuro JWT 토큰이 과거 대화에 노출됨 → **재발급 필요** (jaehyo.kim@gmail.com)
* 자격증명을 코드·커밋·웹폼에 넣지 않는다. 필요 시 환경변수만 사용.
