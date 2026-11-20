"""Balloon–Windkessel 혈역학 순방향 모델.

신경 활동 φ(t) → BOLD 신호. Friston et al. (2000) NeuroImage 12:466-477,
Buxton et al. (1998) Magn Reson Med 39:855-864.

상태변수 4개 (노드별):
    s : 혈관확장 신호 (vasodilatory signal)
    f : 뇌혈류 (cerebral blood flow), 정상상태 1
    v : 혈액량 (blood volume), 정상상태 1
    q : 탈산소혈색소 함량 (deoxyhemoglobin), 정상상태 1

    ds/dt = x − κ·s − γ·(f−1)
    df/dt = s
    dv/dt = (f − v^(1/α)) / τ_h
    dq/dt = (f·E(f)/E₀ − v^(1/α−1)·q) / τ_h
    E(f)  = 1 − (1−E₀)^(1/f)

    BOLD  = V₀·[ k₁(1−q) + k₂(1−q/v) + k₃(1−v) ]

원본 JS Artifact(`bwStep`, `boldVal`)와 동일한 Euler 적분 및 동일한 하한
클리핑(f≥0.1, v≥0.05, q≥0.01)을 사용한다.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["BWParams", "BWState", "bw_step", "bold_signal"]


@dataclass(frozen=True)
class BWParams:
    """Balloon–Windkessel 매개변수 (v3 확정값)."""

    kappa: float = 0.65   # 신호 감쇠율 (s⁻¹)
    gamma: float = 0.41   # 자가조절 피드백 (s⁻¹)
    tau: float = 0.98     # 혈액 통과시간 τ_h (s)
    alpha: float = 0.32   # Grubb 지수
    E0: float = 0.40      # 안정상태 산소추출률
    V0: float = 0.04      # 안정상태 혈액량 분율
    k1: float = 2.8
    k2: float = 2.0
    k3: float = 0.6


#: 노드별 BW 상태. shape (N,) 배열 4개를 묶어 벡터화 적분한다.
@dataclass
class BWState:
    s: np.ndarray
    f: np.ndarray
    v: np.ndarray
    q: np.ndarray

    @classmethod
    def initial(cls, n: int) -> "BWState":
        """정상상태 초기값 (s=0, f=v=q=1)."""
        return cls(
            s=np.zeros(n, dtype=np.float64),
            f=np.ones(n, dtype=np.float64),
            v=np.ones(n, dtype=np.float64),
            q=np.ones(n, dtype=np.float64),
        )


# JS 구현과 동일한 하한값 (수치 발산 방지)
_F_MIN, _V_MIN, _Q_MIN = 0.1, 0.05, 0.01


def bw_step(x: np.ndarray, st: BWState, p: BWParams, dt: float) -> BWState:
    """BW 상태를 한 스텝 전진시킨다.

    Args:
        x:  (N,) 신경 입력 (φ 로부터 변환된 값).
        st: 현재 BW 상태.
        p:  BW 매개변수.
        dt: 적분 스텝.
    """
    sf = np.maximum(_F_MIN, st.f)
    sv = np.maximum(_V_MIN, st.v)
    sq = np.maximum(_Q_MIN, st.q)

    # 산소추출률 E(f) / E₀
    Ef = (1.0 - np.power(1.0 - p.E0, 1.0 / sf)) / p.E0

    return BWState(
        s=st.s + (x - p.kappa * st.s - p.gamma * (sf - 1.0)) * dt,
        f=np.maximum(_F_MIN, st.f + st.s * dt),
        v=np.maximum(_V_MIN, st.v + (sf - np.power(sv, 1.0 / p.alpha)) / p.tau * dt),
        q=np.maximum(
            _Q_MIN,
            st.q + (sf * Ef - np.power(sv, 1.0 / p.alpha - 1.0) * sq) / p.tau * dt,
        ),
    )


def bold_signal(st: BWState, p: BWParams) -> np.ndarray:
    """BW 상태 → BOLD 백분율 변화 (N,)."""
    sv = np.maximum(_V_MIN, st.v)
    sq = np.maximum(_Q_MIN, st.q)
    return p.V0 * (
        p.k1 * (1.0 - sq)
        + p.k2 * (1.0 - sq / sv)
        + p.k3 * (1.0 - sv)
    )
