"""귀무모형(null model) 사다리 — r 값이 무엇을 의미하는지 가늠하기 위한 기준선.

왜 필요한가
-----------
`EMPR_FC` 는 네트워크 소속만으로 값이 거의 결정되는 **블록 행렬**이다
(DMN-TPN 24개 성분이 모두 −0.16 ~ −0.32). 136쌍 Pearson r 은 이런 표적에 대해
블록 간 분산이 지배하므로, "DMN 내부 양 · TPN 내부 양 · DMN-TPN 음" 세 가지만
맞추는 모형이면 무엇이든 높은 r 을 얻는다.

따라서 Amari-GL 의 r = 0.92 를 모델의 성과로 주장하려면, **더 단순한 설명이 같은
수준에 도달하지 못한다**는 것을 먼저 보여야 한다. 이 모듈은 그 기준선을 제공한다.

귀무모형 목록
-------------
=========  =========================================  =============  ==========
코드       모형                                        표적에 적합?    동역학?
=========  =========================================  =============  ==========
N0         블록 평균만 (네트워크 소속 → 값)             예 (관대함)     없음
N1         유클리드 거리 감쇠 a·exp(−d/λ) + c           예 (관대함)     없음
N2         SC 그 자체                                   아니오          없음
N3         가중치 치환 SC 로 돌린 Amari-GL              아니오          있음
N4a        선형 OU 해석해 (Lyapunov 방정식)             아니오          선형
N4b        선형 모형 + 동일 BW/샘플링 파이프라인        아니오          선형
=========  =========================================  =============  ==========

"표적에 적합? 예" 인 모형(N0·N1)은 **자기 파라미터를 EMPR_FC 에 맞춰 적합**하므로
귀무모형에게 유리하다. 그럼에도 Amari-GL 이 이들을 넘지 못한다면 모델의 기여를
주장할 수 없다.

판정 기준 (`docs/재검증_계획.md` §3.1)
--------------------------------------
Amari-GL 이 N0–N4 **전부를** 상회해야 비선형 GL 동역학이 정당화된다.
특히 **N4b 를 이기지 못하면 −φ³ 비선형항과 임계성 논증의 근거가 약해진다** —
선형 확산만으로 같은 FC 패턴이 나온다는 뜻이기 때문이다.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from .amari_gl import PHI_CLIP, GLParams
from .analysis import fc_correlation
from .connectivity import SC, EMPR_FC
from .nodes import NET_MEMBERS, NETWORKS, NN, NODES, gidx
from .simulate import SimConfig, run_simulation

__all__ = [
    "NullResult",
    "node_distances",
    "block_mean_fc",
    "distance_decay_fc",
    "permuted_sc",
    "linear_step",
    "linear_ou_fc",
    "run_null_ladder",
]


def _upper(mat: np.ndarray) -> np.ndarray:
    return mat[np.triu_indices(mat.shape[0], k=1)]


@dataclass(frozen=True)
class NullResult:
    """귀무모형 1건의 결과."""

    code: str
    label: str
    r: float
    fitted_to_target: bool   # True 면 표적에 적합된 모형 (귀무모형에 유리)
    note: str = ""


# ─── N0 · 블록 평균 ─────────────────────────────────────────────────────────

def block_mean_fc(ref: np.ndarray | None = None) -> np.ndarray:
    """각 엣지를 **소속 네트워크 블록의 평균값**으로 예측하는 행렬.

    동역학도, 구조도, 거리도 쓰지 않는다. 오직 "이 노드가 DMN인가 TPN인가"만 안다.
    표적(ref)의 블록 평균을 그대로 쓰므로 귀무모형에게 최대한 유리한 설정이다.
    """
    R = EMPR_FC if ref is None else ref
    out = np.zeros((NN, NN), dtype=np.float64)

    for na in NETWORKS:
        ia = [gidx(x) for x in NET_MEMBERS[na]]
        for nb in NETWORKS:
            ib = [gidx(x) for x in NET_MEMBERS[nb]]
            block = R[np.ix_(ia, ib)]
            if na == nb:
                m = block.shape[0]
                if m < 2:
                    continue
                vals = block[~np.eye(m, dtype=bool)]
            else:
                vals = block.ravel()
            out[np.ix_(ia, ib)] = vals.mean()

    np.fill_diagonal(out, 1.0)
    return out


# ─── N1 · 거리 감쇠 ─────────────────────────────────────────────────────────

def node_distances() -> np.ndarray:
    """노드 간 유클리드 MNI 거리 (mm)."""
    xyz = np.array([n.mni for n in NODES], dtype=np.float64)
    diff = xyz[:, None, :] - xyz[None, :, :]
    return np.sqrt((diff ** 2).sum(axis=-1))


def distance_decay_fc(ref: np.ndarray | None = None) -> tuple[np.ndarray, dict]:
    """FC ≈ a·exp(−d/λ) + c 를 표적에 적합한 예측 행렬.

    "가까운 영역끼리 더 상관된다"는 것만으로 표적을 얼마나 설명할 수 있는지 본다.

    λ 에 대해서만 비선형이므로, λ 를 격자 탐색하고 각 λ 에서 (a, c) 를 최소제곱으로
    푼다 (profile likelihood). 외부 최적화 라이브러리가 필요 없고 국소최적에 빠지지 않는다.
    """
    R = EMPR_FC if ref is None else ref
    D = node_distances()
    d, y = _upper(D), _upper(R)

    def fit_at(lam: float) -> tuple[float, float, float]:
        """주어진 λ 에서 (a, c) 최소제곱해와 잔차제곱합."""
        X = np.column_stack([np.exp(-d / lam), np.ones_like(d)])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        sse = float(((X @ coef - y) ** 2).sum())
        return float(coef[0]), float(coef[1]), sse

    # 거친 격자 → 세밀 격자 2단계 탐색 (λ 는 mm 단위, 뇌 크기 스케일)
    grid = np.linspace(2.0, 400.0, 800)
    sses = [fit_at(l)[2] for l in grid]
    lam = float(grid[int(np.argmin(sses))])

    fine = np.linspace(max(1.0, lam - 2.0), lam + 2.0, 400)
    sses = [fit_at(l)[2] for l in fine]
    lam = float(fine[int(np.argmin(sses))])

    a, c, _ = fit_at(lam)
    pred = a * np.exp(-D / lam) + c
    np.fill_diagonal(pred, 1.0)
    return pred, {"a": a, "lambda_mm": lam, "c": c}


# ─── N3 · 가중치 치환 SC ────────────────────────────────────────────────────

def permuted_sc(sc: np.ndarray | None = None,
                rng: np.random.Generator | None = None) -> np.ndarray:
    """엣지 위상은 유지한 채 **가중치만 무작위로 재배치**한 SC.

    총 결합강도와 연결 개수는 보존되지만 "어느 쌍이 얼마나 강한가"는 파괴된다.
    SC 의 구체적 배선 패턴이 FC 재현에 기여하는지 검정한다.
    """
    C = SC if sc is None else sc
    rng = rng or np.random.default_rng(0)

    iu = np.triu_indices(C.shape[0], k=1)
    w = C[iu]
    nz = w > 0
    w_shuffled = w.copy()
    w_shuffled[nz] = rng.permutation(w[nz])

    out = np.zeros_like(C)
    out[iu] = w_shuffled
    return out + out.T


# ─── N4 · 선형 모형 ─────────────────────────────────────────────────────────

def linear_step(phi: np.ndarray, sc: np.ndarray, p: GLParams,
                dt: float, rng: np.random.Generator) -> np.ndarray:
    """`gl_step` 에서 **−φ³ 비선형항만 제거**한 적분 스텝.

    나머지(확산 결합·전역 억압·잡음·클리핑)는 완전히 동일하다.
    따라서 이 모형과 전체 모형의 차이는 오직 3차 비선형항의 유무다.
    """
    a = p.sigma - 1.0
    dphi = (a * phi) * dt
    dphi += (sc @ phi - phi * sc.sum(axis=1)) * dt
    dphi -= p.beta * phi.mean() * dt
    dphi += p.noise * np.sqrt(dt) * rng.standard_normal(phi.shape[0])
    return np.clip(phi + dphi, -PHI_CLIP, PHI_CLIP)


def jacobian(sc: np.ndarray | None = None,
             p: GLParams | None = None) -> np.ndarray:
    """φ=0 근방 선형화 야코비안.

        J = (σ−1)I + C − diag(k) − (β/N)·11ᵀ,   k = rowsum(C)

    `docs/PORTING_NOTES.md` §3 의 유도와 동일하다.
    """
    C = SC if sc is None else sc
    p = p or GLParams()
    k = C.sum(axis=1)
    n = C.shape[0]
    return ((p.sigma - 1.0) * np.eye(n) + C - np.diag(k)
            - (p.beta / n) * np.ones((n, n)))


def linear_ou_fc(sc: np.ndarray | None = None,
                 p: GLParams | None = None) -> np.ndarray:
    """선형 OU 과정의 **정상상태 상관행렬 해석해**.

    dφ = Jφ dt + s dW 의 정상 공분산 Σ 는 Lyapunov 방정식
    JΣ + ΣJᵀ + s²I = 0 의 해다. J 가 안정(λ_max < 0)일 때만 유효하다.

    J 는 대칭(C·diag(k)·11ᵀ 모두 대칭)이므로 고유분해 J = VΛVᵀ 로 닫힌 해를 얻는다.
    Σ̃ = VᵀΣV 로 두면 ΛΣ̃ + Σ̃Λ = −s²I 이고, 이는 성분별로
    (λᵢ+λⱼ)Σ̃ᵢⱼ = −s²δᵢⱼ 이므로 Σ̃ 는 대각이며 Σ̃ᵢᵢ = −s²/(2λᵢ) 다.
    따라서 Σ = V·diag(−s²/2λᵢ)·Vᵀ — 외부 Lyapunov 솔버가 필요 없다.

    주의: 이것은 **신경 수준** 상관이며 BW 혈역학을 거치지 않았다.
    BW 를 포함한 공정한 비교는 N4b(`linear_step` + 동일 파이프라인)를 쓴다.
    """
    p = p or GLParams()
    J = jacobian(sc, p)
    assert np.allclose(J, J.T), "야코비안이 대칭이 아니다 — 닫힌 해 전제 위반"

    lam, V = np.linalg.eigh(J)
    if lam.max() >= 0:
        raise ValueError(
            f"선형화가 불안정하다 (λ_max = {lam.max():+.4f} ≥ 0). "
            "이 경우 OU 정상해가 존재하지 않는다 — N4a 는 임계 직하에서만 유효하다."
        )

    Sigma = (V * (-(p.noise ** 2) / (2.0 * lam))) @ V.T

    d = np.sqrt(np.diag(Sigma))
    return Sigma / np.outer(d, d)


# ─── 앙상블 헬퍼 ────────────────────────────────────────────────────────────

def _ensemble_fc(cfg: SimConfig, sc: np.ndarray | None = None,
                 step_fn=None, n: int = 1) -> np.ndarray:
    """seed 를 바꿔 n 회 실행한 FC 의 평균."""
    from .amari_gl import gl_step

    fn = step_fn or gl_step
    base = cfg.seed if cfg.seed is not None else 0
    fcs = []
    for k in range(n):
        fcs.append(run_simulation(replace(cfg, seed=base + k), sc=sc,
                                  step_fn=fn).fc)
    return np.mean(fcs, axis=0)


# ─── 사다리 실행 ────────────────────────────────────────────────────────────

def run_null_ladder(cfg: SimConfig | None = None,
                    ensemble: int = 10,
                    n_rewire: int = 5) -> tuple[list[NullResult], float]:
    """귀무모형 전체를 실행하고 (결과 목록, 전체모형 r) 을 반환한다.

    Args:
        cfg: 시뮬레이션 설정 (전체 모형 · N3 · N4b 에 공통 적용).
        ensemble: 앙상블 크기. 단일 실행 r 은 시드마다 ±0.02 흔들린다.
        n_rewire: N3 에서 사용할 독립 치환 횟수.
    """
    cfg = cfg or SimConfig()
    results: list[NullResult] = []

    # 전체 모형 (비교 기준)
    full_fc = _ensemble_fc(cfg, n=ensemble)
    r_full = fc_correlation(full_fc)

    # N0
    results.append(NullResult(
        "N0", "블록 평균만 (네트워크 소속)",
        fc_correlation(block_mean_fc()), True,
        "동역학·구조·거리 모두 불사용",
    ))

    # N1
    dd_fc, dd_par = distance_decay_fc()
    results.append(NullResult(
        "N1", "거리 감쇠 a·exp(−d/λ)+c",
        fc_correlation(dd_fc), True,
        f"λ = {dd_par['lambda_mm']:.1f} mm",
    ))

    # N2
    results.append(NullResult(
        "N2", "SC 그 자체 (동역학 없음)",
        fc_correlation(SC), False,
        "구조행렬을 그대로 FC 예측으로 사용",
    ))

    # N3
    rs = []
    for k in range(n_rewire):
        sc_p = permuted_sc(rng=np.random.default_rng(1000 + k))
        rs.append(fc_correlation(_ensemble_fc(cfg, sc=sc_p, n=ensemble)))
    results.append(NullResult(
        "N3", "가중치 치환 SC + Amari-GL",
        float(np.mean(rs)), False,
        f"{n_rewire}회 치환 평균, SD = {np.std(rs):.3f}",
    ))

    # N4a
    try:
        results.append(NullResult(
            "N4a", "선형 OU 해석해 (Lyapunov)",
            fc_correlation(linear_ou_fc(p=cfg.gl)), False,
            "신경 수준, BW 미적용",
        ))
    except ValueError as e:
        results.append(NullResult("N4a", "선형 OU 해석해 (Lyapunov)",
                                  float("nan"), False, str(e)))

    # N4b
    results.append(NullResult(
        "N4b", "선형 모형 + 동일 BW 파이프라인",
        fc_correlation(_ensemble_fc(cfg, step_fn=linear_step, n=ensemble)),
        False,
        "−φ³ 항만 제거, 나머지 동일 — 가장 공정한 대조",
    ))

    return results, r_full
