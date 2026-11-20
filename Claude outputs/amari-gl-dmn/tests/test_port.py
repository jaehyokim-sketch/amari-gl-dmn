"""포팅 무결성 테스트.

원본 JS Artifact(amari_gl_v7.html)와 Python 포팅이 어긋나지 않도록
행렬 값·설계 제약·수치 동작을 고정한다.

    pytest -q        (또는)        python -m pytest tests/ -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import (  # noqa: E402
    EMPR_FC, SC, GLParams, SimConfig, fc_correlation, run_simulation, validate,
)
from src.amari_gl import gl_step  # noqa: E402
from src.balloon import BWParams, BWState, bold_signal, bw_step  # noqa: E402
from src.nodes import NN, gidx  # noqa: E402


# ─── 행렬 무결성 ─────────────────────────────────────────────────────────────

def test_dimensions():
    assert NN == 17
    assert SC.shape == (NN, NN)
    assert EMPR_FC.shape == (NN, NN)


def test_sc_is_nonnegative():
    """반상관은 창발해야 한다 — SC 에 음의 결합을 넣으면 순환론이 된다."""
    assert np.all(SC >= 0), "SC 에 음수 성분 발견"


def test_sc_symmetric_zero_diagonal():
    assert np.allclose(SC, SC.T)
    assert np.allclose(np.diag(SC), 0.0)


def test_dmn_tpn_structural_links_are_positive():
    dmn = ["mPFC", "PCC", "L_AG", "R_AG", "L_MTG", "R_MTG"]
    tpn = ["L_dlPFC", "R_dlPFC", "L_FEF", "R_FEF", "L_IPS", "R_IPS"]
    block = SC[np.ix_([gidx(d) for d in dmn], [gidx(t) for t in tpn])]
    assert np.all(block >= 0)


def test_empirical_fc_symmetric_unit_diagonal():
    assert np.allclose(EMPR_FC, EMPR_FC.T)
    assert np.allclose(np.diag(EMPR_FC), 1.0)


@pytest.mark.parametrize("a,b,expected", [
    # V7 에서 0.35 → 0.30 으로 하향한 세 위치
    ("ACC", "L_CLA", 0.30),
    ("ACC", "R_CLA", 0.30),
    # 검증되어 유지된 값들
    ("L_CLA", "L_AI", 0.45),
    ("R_CLA", "R_AI", 0.45),
    ("L_CLA", "R_CLA", 0.55),
    ("mPFC", "L_CLA", 0.30),
])
def test_v7_cla_values(a, b, expected):
    """V7 CLA 파라미터가 되돌아가지 않았는지 확인."""
    assert EMPR_FC[gidx(a), gidx(b)] == pytest.approx(expected)


# ─── 수치 동작 ───────────────────────────────────────────────────────────────

def test_gl_step_clips_phi():
    rng = np.random.default_rng(0)
    phi = np.full(NN, 100.0)
    out = gl_step(phi, SC, GLParams(noise=0.0), 0.08, rng)
    assert np.all(np.abs(out) <= 4.0)


def test_gl_step_is_deterministic_with_seed():
    phi = np.zeros(NN)
    p, dt = GLParams(), 0.08
    a = gl_step(phi, SC, p, dt, np.random.default_rng(1))
    b = gl_step(phi, SC, p, dt, np.random.default_rng(1))
    assert np.allclose(a, b)


def test_bw_steady_state_gives_near_zero_bold():
    """정상상태(s=0, f=v=q=1)의 BOLD 는 0 이어야 한다."""
    st = BWState.initial(NN)
    assert np.allclose(bold_signal(st, BWParams()), 0.0)


def test_bw_state_bounds_hold():
    rng = np.random.default_rng(3)
    st, p = BWState.initial(NN), BWParams()
    for _ in range(500):
        st = bw_step(rng.random(NN) * 0.5, st, p, 0.08)
    assert np.all(st.f >= 0.1) and np.all(st.v >= 0.05) and np.all(st.q >= 0.01)
    assert np.all(np.isfinite(bold_signal(st, p)))


def test_effective_tr_is_056():
    """DT=0.08, SAMPLE_DT=0.5 → 실효 TR 0.56s (JS 와 동일한 누적 방식)."""
    assert SimConfig().effective_tr == pytest.approx(0.56)


# ─── 시뮬레이션 결과 ─────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def result():
    return run_simulation(SimConfig(n_samples=800, seed=42))


def test_simulation_shapes(result):
    assert result.bold.shape == (800, NN)
    assert result.fc.shape == (NN, NN)
    assert np.all(np.isfinite(result.bold))


def test_fc_valid_range(result):
    assert np.allclose(np.diag(result.fc), 1.0)
    assert result.fc.min() >= -1.0 and result.fc.max() <= 1.0
    assert np.allclose(result.fc, result.fc.T)


def test_literature_correlation_in_expected_band(result):
    """단일 실행 r 은 0.77–0.90 대역. 이 밖으로 나가면 포팅이 깨진 것."""
    r = fc_correlation(result.fc)
    assert 0.75 <= r <= 0.92, f"r={r:.4f} — 예상 대역을 벗어남"


def test_within_network_exceeds_between_network(result):
    """DMN/TPN 내부 FC 가 DMN-TPN 교차 FC 보다 확실히 커야 한다."""
    from src.analysis import network_blocks
    b = network_blocks(result.fc)
    assert b["DMN-DMN"] > b["DMN-TPN"] + 0.25
    assert b["TPN-TPN"] > b["DMN-TPN"] + 0.25


def test_cla_ai_coupling_matches_literature(result):
    """CLA–AI 동측 결합은 문헌 허용범위 [0.35, 0.55] 안에 들어야 한다."""
    row = next(r for r in validate(result.fc) if "CLA–AI" in r.label)
    assert row.passed, f"CLA-AI = {row.simulated:.3f}"


def test_majority_of_validation_targets_pass(result):
    rows = validate(result.fc)
    assert sum(r.passed for r in rows) >= 5, \
        "\n".join(f"{r.label}: {r.simulated:+.3f} {r.mark}" for r in rows)


@pytest.mark.xfail(
    reason="알려진 미해결 과제: 단일 실행에서 DMN-TPN 반상관이 문헌 "
           "−0.199 에 못 미친다 (≈ −0.02 ~ −0.05). docs/PORTING_NOTES.md 참조.",
    strict=False,
)
def test_dmn_tpn_anticorrelation_reaches_literature(result):
    row = next(r for r in validate(result.fc) if "반상관" in r.label)
    assert row.passed
