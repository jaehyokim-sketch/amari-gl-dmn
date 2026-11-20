"""시뮬레이션 러너 — Amari-GL 신경 동역학 + BW 혈역학 + BOLD 샘플링.

원본 JS Artifact(`simFrame`)의 루프 구조를 그대로 재현한다:

    매 적분 스텝(DT=0.08s):
        1. gl_step  으로 φ 전진
        2. 신경 입력 x = max(0, φ·0.3) + 0.04 를 BW 에 주입
        3. simTime > WARMUP(60s) 이고 sampleTimer >= SAMPLE_DT(0.5s) 이면
           BOLD 를 1회 샘플링하고 sampleTimer 를 0 으로 리셋

sampleTimer 는 DT 단위로 누적되므로 실효 TR 은 0.5s 가 아니라
ceil(0.5/0.08)·0.08 = **0.56s** 이다. JS 와의 수치 일치를 위해 의도적으로
이 동작을 그대로 유지한다.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from .amari_gl import DT_DEFAULT, GLParams, gl_step
from .balloon import BWParams, BWState, bold_signal, bw_step
from .connectivity import SC
from .nodes import IDS, NN

__all__ = ["SimConfig", "SimResult", "run_simulation"]


# 신경 활동 → BW 입력 변환 (JS: `Math.max(0, phi[i]*0.3) + 0.04`)
_NEURAL_GAIN = 0.3
_NEURAL_BASELINE = 0.04


@dataclass
class SimConfig:
    """시뮬레이션 설정."""

    gl: GLParams = field(default_factory=GLParams)
    bw: BWParams = field(default_factory=BWParams)
    dt: float = DT_DEFAULT      # 적분 스텝 (s)
    sample_dt: float = 0.5      # 목표 샘플 간격 (s) — 실효 TR 은 0.56s
    warmup: float = 60.0        # 버리는 초기 구간 (s)
    n_samples: int = 800        # 수집할 BOLD 샘플 수 (JS BOLD_BUF 와 동일)
    seed: int | None = 42       # 재현성. None 이면 비결정적
    record_phi: bool = False    # True 면 φ 궤적도 저장 (메모리 주의)

    @property
    def effective_tr(self) -> float:
        """실효 반복시간 (s)."""
        return np.ceil(self.sample_dt / self.dt) * self.dt

    @property
    def duration(self) -> float:
        """warmup 포함 총 시뮬레이션 시간 (s)."""
        return self.warmup + self.n_samples * self.effective_tr


@dataclass
class SimResult:
    """시뮬레이션 결과."""

    bold: np.ndarray            # (n_samples, NN)
    fc: np.ndarray              # (NN, NN) 시뮬레이션 rsFC
    phi_trace: np.ndarray | None  # (n_steps, NN) 또는 None
    config: SimConfig
    node_ids: list[str] = field(default_factory=lambda: list(IDS))

    def fc_of(self, a: str, b: str) -> float:
        """노드쌍 FC 조회."""
        return float(self.fc[self.node_ids.index(a), self.node_ids.index(b)])


def run_simulation(cfg: SimConfig | None = None,
                   sc: np.ndarray | None = None,
                   step_fn: Callable[..., np.ndarray] = gl_step) -> SimResult:
    """시뮬레이션을 실행하고 BOLD 기반 rsFC 를 반환한다.

    Args:
        cfg: 시뮬레이션 설정. None 이면 v3 확정 기본값.
        sc:  구조적 연결행렬. None 이면 문헌 기반 기본 SC.
        step_fn: 신경 동역학 적분 함수. 기본값은 정규 Amari-GL 스텝이며,
            `gl_step` 과 동일한 시그니처를 가진 대체 함수를 주입할 수 있다.
            귀무모형(`src/nulls.py` 의 선형 모형)이 이 경로를 쓴다.
    """
    cfg = cfg or SimConfig()
    C = SC if sc is None else sc
    rng = np.random.default_rng(cfg.seed)

    phi = np.zeros(NN, dtype=np.float64)
    bw = BWState.initial(NN)

    bold = np.empty((cfg.n_samples, NN), dtype=np.float64)
    phi_trace: list[np.ndarray] = []

    sim_time = 0.0
    sample_timer = 0.0
    collected = 0

    # 안전 상한: 정상적으로는 duration/dt 안에 모두 수집된다.
    max_steps = int((cfg.duration / cfg.dt) * 1.5) + 1000

    for _ in range(max_steps):
        if collected >= cfg.n_samples:
            break

        phi = step_fn(phi, C, cfg.gl, cfg.dt, rng)

        x = np.maximum(0.0, phi * _NEURAL_GAIN) + _NEURAL_BASELINE
        bw = bw_step(x, bw, cfg.bw, cfg.dt)

        if cfg.record_phi:
            phi_trace.append(phi.copy())

        sim_time += cfg.dt
        sample_timer += cfg.dt

        if sim_time > cfg.warmup and sample_timer >= cfg.sample_dt:
            sample_timer = 0.0
            bold[collected] = bold_signal(bw, cfg.bw)
            collected += 1

    if collected < cfg.n_samples:  # pragma: no cover - 방어적
        raise RuntimeError(
            f"샘플 수집 실패: {collected}/{cfg.n_samples} "
            f"(max_steps={max_steps} 초과)"
        )

    fc = np.corrcoef(bold.T)
    np.fill_diagonal(fc, 1.0)

    return SimResult(
        bold=bold,
        fc=fc,
        phi_trace=np.array(phi_trace) if cfg.record_phi else None,
        config=cfg,
    )
