"""시뮬레이션 rsFC 의 정량 분석 및 문헌값 검증.

핵심 지표
---------
* ``fc_correlation``  : 시뮬 FC 상삼각 vs 문헌 FC 상삼각의 Pearson r.
                        논문의 주요 검증 지표 (v3 보고값 r = 0.922).
* ``network_blocks``  : DMN/TPN/SAL/CLA 블록별 평균 FC.
* ``validate``        : 논문 본문 검증표(7개 지표)의 합격/근사 판정.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .connectivity import EMPR_FC
from .nodes import NET_MEMBERS, NETWORKS, NN, gidx

__all__ = [
    "fc_correlation",
    "network_blocks",
    "validate",
    "ValidationRow",
    "VALIDATION_TARGETS",
]


def _upper(mat: np.ndarray) -> np.ndarray:
    """대각을 제외한 상삼각 성분을 1차원으로 펼친다."""
    iu = np.triu_indices(mat.shape[0], k=1)
    return mat[iu]


def fc_correlation(sim_fc: np.ndarray,
                   ref_fc: np.ndarray | None = None) -> float:
    """시뮬 FC 와 참조 FC 의 Pearson r (대각 제외 상삼각 기준)."""
    ref = EMPR_FC if ref_fc is None else ref_fc
    a, b = _upper(sim_fc), _upper(ref)
    return float(np.corrcoef(a, b)[0, 1])


def network_blocks(fc: np.ndarray) -> dict[str, float]:
    """네트워크 블록별 평균 FC.

    같은 네트워크끼리는 대각(자기상관)을 제외한 평균,
    서로 다른 네트워크는 전체 쌍 평균.
    """
    out: dict[str, float] = {}
    for i, na in enumerate(NETWORKS):
        ia = [gidx(x) for x in NET_MEMBERS[na]]
        for nb in NETWORKS[i:]:
            ib = [gidx(x) for x in NET_MEMBERS[nb]]
            block = fc[np.ix_(ia, ib)]
            if na == nb:
                m = block.shape[0]
                if m < 2:
                    out[f"{na}-{nb}"] = float("nan")
                    continue
                vals = block[~np.eye(m, dtype=bool)]
            else:
                vals = block.ravel()
            out[f"{na}-{nb}"] = float(vals.mean())
    return out


# ─── 논문 본문 검증표 ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Target:
    """단일 검증 항목: 노드쌍(들)의 평균 FC 가 [lo, hi] 안에 드는지."""

    label: str
    pairs: tuple[tuple[str, str], ...]
    lo: float
    hi: float
    literature: float


#: JS Artifact `updateTable()` 의 7개 항목과 동일.
VALIDATION_TARGETS: tuple[Target, ...] = (
    Target("mPFC–PCC (DMN 핵심)", (("mPFC", "PCC"),), 0.35, 0.70, +0.58),
    Target("PCC–L_AG (DMN 후방)", (("PCC", "L_AG"),), 0.40, 0.75, +0.62),
    Target("dlPFC–IPS (TPN 내부)",
           (("L_dlPFC", "L_IPS"), ("R_dlPFC", "R_IPS")), 0.30, 0.65, +0.50),
    Target("DMN–TPN 반상관 (창발)",
           tuple((d, t)
                 for d in ("mPFC", "PCC", "L_AG", "R_AG")
                 for t in ("L_dlPFC", "R_dlPFC", "L_IPS", "R_IPS")),
           -0.45, -0.15, -0.199),
    Target("mPFC–AI (DMN–SAL)",
           (("mPFC", "L_AI"), ("mPFC", "R_AI")), 0.10, 0.40, +0.120),
    Target("CLA–AI (동측)",
           (("L_CLA", "L_AI"), ("R_CLA", "R_AI")), 0.35, 0.55, +0.45),
    Target("mPFC–CLA",
           (("mPFC", "L_CLA"), ("mPFC", "R_CLA")), 0.20, 0.40, +0.30),
)


@dataclass(frozen=True)
class ValidationRow:
    """검증 1건의 결과."""

    label: str
    simulated: float
    literature: float
    lo: float
    hi: float

    @property
    def passed(self) -> bool:
        return self.lo <= self.simulated <= self.hi

    @property
    def mark(self) -> str:
        return "✓ 일치" if self.passed else "△ 근사"


def validate(fc: np.ndarray) -> list[ValidationRow]:
    """검증표 7개 항목을 평가한다."""
    rows: list[ValidationRow] = []
    for t in VALIDATION_TARGETS:
        vals = [fc[gidx(a), gidx(b)] for a, b in t.pairs]
        rows.append(
            ValidationRow(
                label=t.label,
                simulated=float(np.mean(vals)),
                literature=t.literature,
                lo=t.lo,
                hi=t.hi,
            )
        )
    return rows


assert NN == EMPR_FC.shape[0]
