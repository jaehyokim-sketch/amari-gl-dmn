"""확장 Amari–Ginzburg–Landau (Amari-GL) 신경장 동역학.

    τ dφᵢ/dt = (σ−1)φᵢ − φᵢ³ + Σⱼ Cᵢⱼ(φⱼ−φᵢ) − β·⟨φ⟩ + ηᵢ(t)

항별 의미
  (σ−1)φ − φ³ : Ginzburg–Landau 포텐셜. σ=1 에서 pitchfork 분기.
                 σ<1 이면 단일 안정점(φ=0), σ>1 이면 이중우물.
  Σ Cᵢⱼ(φⱼ−φᵢ) : 확산형 구조적 결합 (SC, 전부 비음수).
  −β·⟨φ⟩        : **전역 억압**. DMN-TPN 반상관을 창발시키는 유일한 기전.
  ηᵢ(t)         : 가우시안 백색잡음, Euler–Maruyama 로 √DT 스케일.

적분은 원본 JS Artifact(`glStep`)와 수치적으로 동일하게 맞춘다:
Euler–Maruyama, 고정 DT, 매 스텝 φ 를 [-4, 4] 로 클리핑.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["GLParams", "gl_step", "DT_DEFAULT"]

#: 기본 적분 스텝 (초). JS Artifact 와 동일.
DT_DEFAULT: float = 0.08

#: φ 클리핑 범위 (발산 방지). JS `Math.max(-4, Math.min(4, ...))` 와 동일.
PHI_CLIP: float = 4.0


@dataclass
class GLParams:
    """Amari-GL 제어 파라미터.

    기본값은 v3 확정값이며 OpenNeuro ds000030 검증에서 r=0.922 를 낸 설정이다.
    """

    sigma: float = 0.985   # 분기 파라미터 (임계 직하, subcritical)
    beta: float = 0.45     # 전역 억압 강도
    noise: float = 0.09    # 잡음 진폭
    tau: float = 1.0       # 시간상수 (현재 구현은 τ=1 을 가정)

    def as_dict(self) -> dict:
        return {"sigma": self.sigma, "beta": self.beta,
                "noise": self.noise, "tau": self.tau}


def gl_step(
    phi: np.ndarray,
    sc: np.ndarray,
    p: GLParams,
    dt: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Amari-GL 한 스텝 적분 (Euler–Maruyama).

    Args:
        phi: (N,) 현재 상태.
        sc:  (N, N) 비음수 대칭 구조적 연결행렬, 대각 0.
        p:   제어 파라미터.
        dt:  적분 스텝.
        rng: 난수 생성기 (재현성을 위해 외부에서 주입).

    Returns:
        (N,) 다음 스텝 상태.
    """
    a = p.sigma - 1.0
    mean_phi = phi.mean()

    # 국소 포텐셜 항
    dphi = (a * phi - phi ** 3) * dt

    # 확산형 결합: Σⱼ Cᵢⱼ(φⱼ − φᵢ) = (C @ φ) − φ·rowsum(C)
    dphi += (sc @ phi - phi * sc.sum(axis=1)) * dt

    # 전역 억압
    dphi -= p.beta * mean_phi * dt

    # 확률 항 (Euler–Maruyama: √dt 스케일)
    dphi += p.noise * np.sqrt(dt) * rng.standard_normal(phi.shape[0])

    return np.clip(phi + dphi, -PHI_CLIP, PHI_CLIP)
