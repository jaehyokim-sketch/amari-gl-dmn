"""구조적 연결 근사행렬(SC)과 문헌 합성 기능적 연결행렬(EMPR_FC).

⚠ 출처 등급 (2026-09-21 정정)
----------------------------
아래 두 행렬은 **어느 것도 실측 데이터에서 계산한 값이 아니다.**
둘 다 선행연구의 보고값을 참고해 연구진이 손으로 입력한 상수다.
이전 판본이 이를 "실측 dMRI 연결행렬"로 표기했던 것은 오기이며 정정하였다
(`docs/재검증_계획.md` §0.3).

  * SC       — 등급 C: 문헌 근사. 개별 엣지값이 특정 논문의 특정 표에서
               직접 인용된 것이 아니라, 아래 문헌들의 보고 경향을 참고한 추정치다.
  * EMPR_FC  — 등급 C: 서로 다른 전처리(atlas·정합·평활화·nuisance·GSR 여부)를
               거친 5개 연구의 최종값을 수작업 합성한 행렬.

따라서 `analysis.fc_correlation` 이 내는 r 은 "실측 FC 재현도"가 아니라
**"문헌 보고 패턴과의 유사도"** 로만 해석해야 한다. 또한 EMPR_FC 는 사실상
네트워크 소속으로 값이 거의 결정되는 블록 행렬이므로, r 은 블록 구조만으로도
상당 부분 달성된다 — 귀무모형 대비는 `src/nulls.py` 참조.

SC
--
모든 성분이 **비음수**다. DMN-TPN 사이에도 음의 결합을 일절 입력하지 않는다 —
반상관은 전역 억압항 β·⟨φ⟩ 를 통해 동역학의 *결과*로 나타나야 한다
(v1의 순환론적 설계 제거).

참고 문헌: Honey et al. 2009 PNAS; Hagmann et al. 2008 PLoS Biol;
      van den Heuvel & Sporns 2011 J Neurosci;
      Krimmel et al. 2019 / Berman et al. 2020 / Crick & Koch 2005 (Claustrum)

EMPR_FC
-------
GSR 적용 문헌 rsFC 값. Fox 2005 PNAS; Power 2011 Neuron; Smith 2013 NeuroImage;
Ji 2019 NeuroImage (CAB-NP, HCP S1200 N=337); Buckner 2008 Ann NY Acad.

V7 변경점: CLA-ACC 를 0.35 → **0.30** 으로 하향.
  근거: macaque BALSA Area14→ACC FC = 0.05–0.23 (Autio 2020 + Yokoyama 2021).
        기존 0.35 는 과대추정으로 판단, 보수적 상한 0.30 적용.
        CLA-AI = 0.45 는 유지 (macaque Area14→INSULA = 0.43 으로 검증됨).

⚠ CLA 2노드는 **탐색적(Tier B)** 으로 강등되었다 (2026-09-21).
  전장은 표준 파셀레이션에 없고 두께가 1–2 mm 라 부분용적·신호누출을 통제할 수
  없다. 특히 L_CLA↔L_AI 는 19.4 mm 거리로, 평활화만으로도 CLA-AI≈0.45 가
  재현될 수 있다. 정량 주장에 사용하지 않는다.
"""

from __future__ import annotations

import numpy as np

from .nodes import NN, gidx

__all__ = ["build_sc", "SC", "EMPR_FC", "EMPR_PAIRS", "sc_degree"]


# ─── 구조적 연결 (SC) ────────────────────────────────────────────────────────

#: (노드 A, 노드 B, 연결강도) — 대칭 행렬로 전개된다.
SC_EDGES: list[tuple[str, str, float]] = [
    # DMN 내부 (Honey 2009, Hagmann 2008)
    ("mPFC", "PCC", 0.18), ("mPFC", "L_AG", 0.12), ("mPFC", "R_AG", 0.12),
    ("mPFC", "L_MTG", 0.10), ("mPFC", "R_MTG", 0.10),
    ("PCC", "L_AG", 0.38), ("PCC", "R_AG", 0.35),
    ("PCC", "L_MTG", 0.22), ("PCC", "R_MTG", 0.20),
    ("L_AG", "L_MTG", 0.25), ("R_AG", "R_MTG", 0.24),
    ("L_AG", "R_AG", 0.15), ("L_MTG", "R_MTG", 0.08),

    # TPN 내부 (van den Heuvel & Sporns 2011)
    ("L_dlPFC", "R_dlPFC", 0.18), ("L_dlPFC", "L_FEF", 0.28), ("L_dlPFC", "R_FEF", 0.08),
    ("L_dlPFC", "L_IPS", 0.22), ("L_dlPFC", "R_IPS", 0.06),
    ("R_dlPFC", "L_FEF", 0.08), ("R_dlPFC", "R_FEF", 0.28),
    ("R_dlPFC", "L_IPS", 0.06), ("R_dlPFC", "R_IPS", 0.22),
    ("L_FEF", "R_FEF", 0.15), ("L_FEF", "L_IPS", 0.30), ("L_FEF", "R_IPS", 0.08),
    ("R_FEF", "L_IPS", 0.08), ("R_FEF", "R_IPS", 0.30), ("L_IPS", "R_IPS", 0.20),

    # SAL 내부
    ("ACC", "L_AI", 0.30), ("ACC", "R_AI", 0.30), ("L_AI", "R_AI", 0.18),

    # DMN–SAL
    ("mPFC", "ACC", 0.15), ("mPFC", "L_AI", 0.08), ("mPFC", "R_AI", 0.08),
    ("PCC", "ACC", 0.06), ("L_AG", "L_AI", 0.07), ("R_AG", "R_AI", 0.07),

    # TPN–SAL
    ("L_dlPFC", "ACC", 0.12), ("R_dlPFC", "ACC", 0.12),
    ("L_dlPFC", "L_AI", 0.10), ("R_dlPFC", "R_AI", 0.10),
    ("L_IPS", "L_AI", 0.10), ("R_IPS", "R_AI", 0.10),
    ("L_FEF", "ACC", 0.08), ("R_FEF", "ACC", 0.08),

    # Claustrum (Berman 2020; Krimmel 2019; Crick & Koch 2005)
    ("L_CLA", "R_CLA", 0.22),      # 양측 claustrum (Berman 2020)
    ("L_CLA", "L_AI", 0.38),       # 최강 연결: insular–CLA (Krimmel 2019)
    ("R_CLA", "R_AI", 0.38),
    ("L_CLA", "ACC", 0.20),        # ACC–CLA (Krimmel 2019)
    ("R_CLA", "ACC", 0.20),
    ("L_CLA", "mPFC", 0.18),       # pars orbitalis (Berman 2020)
    ("R_CLA", "mPFC", 0.18),
    ("L_CLA", "L_MTG", 0.15),      # transverse temporal (Berman 2020)
    ("R_CLA", "R_MTG", 0.15),
    ("L_CLA", "L_dlPFC", 0.10),    # Crick & Koch 2005
    ("R_CLA", "R_dlPFC", 0.10),
    ("L_CLA", "PCC", 0.08),        # 후방 DMN (Krimmel 2019)
    ("R_CLA", "PCC", 0.08),
    ("L_CLA", "L_AG", 0.06), ("R_CLA", "R_AG", 0.06),
    ("L_CLA", "L_FEF", 0.06), ("R_CLA", "R_FEF", 0.06),
    ("L_CLA", "L_IPS", 0.04), ("R_CLA", "R_IPS", 0.04),

    # DMN–TPN: 전부 양수 (음의 결합 입력 없음!)
    ("mPFC", "L_dlPFC", 0.04), ("mPFC", "R_dlPFC", 0.04),
    ("mPFC", "L_FEF", 0.02), ("mPFC", "R_FEF", 0.02),
    ("mPFC", "L_IPS", 0.03), ("mPFC", "R_IPS", 0.03),
    ("PCC", "L_dlPFC", 0.03), ("PCC", "R_dlPFC", 0.03),
    ("PCC", "L_FEF", 0.02), ("PCC", "R_FEF", 0.02),
    ("PCC", "L_IPS", 0.05), ("PCC", "R_IPS", 0.05),
    ("L_AG", "L_dlPFC", 0.03), ("R_AG", "R_dlPFC", 0.03),
    ("L_AG", "L_IPS", 0.06), ("R_AG", "R_IPS", 0.06),
    ("L_MTG", "L_dlPFC", 0.02), ("R_MTG", "R_dlPFC", 0.02),
    ("L_MTG", "L_IPS", 0.03), ("R_MTG", "R_IPS", 0.03),
]


def build_sc() -> np.ndarray:
    """대칭 (NN, NN) 구조적 연결행렬을 만든다. 대각은 0."""
    C = np.zeros((NN, NN), dtype=np.float64)
    for a, b, v in SC_EDGES:
        ia, ib = gidx(a), gidx(b)
        if ia < 0 or ib < 0:
            continue
        C[ia, ib] = v
        C[ib, ia] = v
    return C


SC: np.ndarray = build_sc()


def sc_degree(C: np.ndarray | None = None) -> np.ndarray:
    """노드별 구조적 연결 차수(가중합)."""
    return (SC if C is None else C).sum(axis=1)


# ─── 실측 기능적 연결 (EMPR_FC) ──────────────────────────────────────────────

#: 노드 순서는 nodes.IDS 와 동일하다.
_EMPR_FC_ROWS = [
    # mPFC   PCC   L_AG  R_AG  L_MTG R_MTG L_dlP R_dlP L_FEF R_FEF L_IPS R_IPS  ACC  L_AI  R_AI  L_CLA R_CLA
    [ 1.00, 0.58, 0.47, 0.45, 0.34, 0.32,-0.22,-0.20,-0.18,-0.17,-0.20,-0.19, 0.16, 0.16, 0.16, 0.30, 0.30],  # mPFC
    [ 0.58, 1.00, 0.62, 0.60, 0.44, 0.42,-0.28,-0.27,-0.25,-0.24,-0.32,-0.30, 0.16, 0.16, 0.16, 0.18, 0.18],  # PCC
    [ 0.47, 0.62, 1.00, 0.54, 0.46, 0.30,-0.20,-0.22,-0.18,-0.18,-0.18,-0.18, 0.10, 0.10, 0.10, 0.12, 0.10],  # L_AG
    [ 0.45, 0.60, 0.54, 1.00, 0.28, 0.45,-0.22,-0.20,-0.18,-0.18,-0.18,-0.18, 0.10, 0.10, 0.10, 0.10, 0.12],  # R_AG
    [ 0.34, 0.44, 0.46, 0.28, 1.00, 0.37,-0.18,-0.18,-0.16,-0.16,-0.18,-0.18, 0.10, 0.10, 0.10, 0.20, 0.10],  # L_MTG
    [ 0.32, 0.42, 0.30, 0.45, 0.37, 1.00,-0.18,-0.18,-0.16,-0.16,-0.18,-0.18, 0.10, 0.10, 0.10, 0.10, 0.20],  # R_MTG
    [-0.22,-0.28,-0.20,-0.22,-0.18,-0.18, 1.00, 0.52, 0.46, 0.29, 0.50, 0.32, 0.13, 0.09, 0.09, 0.15, 0.08],  # L_dlPFC
    [-0.20,-0.27,-0.22,-0.20,-0.18,-0.18, 0.52, 1.00, 0.28, 0.48, 0.32, 0.52, 0.13, 0.09, 0.09, 0.08, 0.15],  # R_dlPFC
    [-0.18,-0.25,-0.18,-0.18,-0.16,-0.16, 0.46, 0.28, 1.00, 0.47, 0.53, 0.29, 0.13, 0.09, 0.09, 0.08, 0.05],  # L_FEF
    [-0.17,-0.24,-0.18,-0.18,-0.16,-0.16, 0.29, 0.48, 0.47, 1.00, 0.28, 0.54, 0.13, 0.09, 0.09, 0.05, 0.08],  # R_FEF
    [-0.20,-0.32,-0.18,-0.18,-0.18,-0.18, 0.50, 0.32, 0.53, 0.28, 1.00, 0.58, 0.13, 0.09, 0.09, 0.05, 0.04],  # L_IPS
    [-0.19,-0.30,-0.18,-0.18,-0.18,-0.18, 0.32, 0.52, 0.29, 0.54, 0.58, 1.00, 0.13, 0.09, 0.09, 0.04, 0.05],  # R_IPS
    [ 0.16, 0.16, 0.10, 0.10, 0.10, 0.10, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13, 1.00, 0.57, 0.54, 0.30, 0.30],  # ACC   ← V7: CLA 0.35→0.30
    [ 0.16, 0.16, 0.10, 0.10, 0.10, 0.10, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.57, 1.00, 0.63, 0.45, 0.20],  # L_AI
    [ 0.16, 0.16, 0.10, 0.10, 0.10, 0.10, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.54, 0.63, 1.00, 0.20, 0.45],  # R_AI
    [ 0.30, 0.18, 0.12, 0.10, 0.20, 0.10, 0.15, 0.08, 0.08, 0.05, 0.05, 0.04, 0.30, 0.45, 0.20, 1.00, 0.55],  # L_CLA ← V7
    [ 0.30, 0.18, 0.10, 0.12, 0.10, 0.20, 0.08, 0.15, 0.05, 0.08, 0.04, 0.05, 0.30, 0.20, 0.45, 0.55, 1.00],  # R_CLA ← V7
]

EMPR_FC: np.ndarray = np.array(_EMPR_FC_ROWS, dtype=np.float64)

#: 논문 본문 검증표에 쓰이는 대표 노드쌍 실측값.
EMPR_PAIRS: dict[str, float] = {
    "mPFC_PCC": +0.58,
    "PCC_LAG": +0.62,
    "LAG_RAG": +0.54,
    "TPN_DLIPS": +0.50,
    "FEF_IPS": +0.53,
    "SAL_ACC_AI": +0.57,
    "DMN_TPN_ANTI": -0.199,
    "DMN_SAL": +0.120,
}


# 무결성 체크 — import 시점에 형상/대칭성을 보장한다.
assert EMPR_FC.shape == (NN, NN), f"EMPR_FC shape {EMPR_FC.shape} != ({NN},{NN})"
assert np.allclose(EMPR_FC, EMPR_FC.T), "EMPR_FC 가 대칭이 아님"
assert np.allclose(np.diag(EMPR_FC), 1.0), "EMPR_FC 대각이 1이 아님"
assert np.all(SC >= 0), "SC 에 음수 성분이 있음 — 반상관 창발 설계 위반"
assert np.allclose(SC, SC.T), "SC 가 대칭이 아님"
