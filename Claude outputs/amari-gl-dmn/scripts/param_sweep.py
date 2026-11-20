#!/usr/bin/env python3
"""파라미터 스윕 — σ × β 격자에서 문헌 FC 일치도와 DMN-TPN 반상관을 탐색.

v3 확정값(σ=0.985, β=0.45)이 국소최적인지, 그리고 DMN-TPN 반상관이
어느 영역에서 문헌 수준(−0.199)에 도달하는지를 확인하기 위한 도구다.

사용법:
    python scripts/param_sweep.py
    python scripts/param_sweep.py --sigma 0.95 1.02 8 --beta 0.2 0.8 8 --ensemble 3
    python scripts/param_sweep.py --axis noise --noise 0.03 0.20 10
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import GLParams, SimConfig, fc_correlation, run_simulation  # noqa: E402
from src.analysis import network_blocks, validate  # noqa: E402


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Amari-GL 파라미터 스윕")
    ap.add_argument("--sigma", nargs=3, type=float, metavar=("LO", "HI", "N"),
                    default=[0.95, 1.02, 8], help="σ 범위와 격자수")
    ap.add_argument("--beta", nargs=3, type=float, metavar=("LO", "HI", "N"),
                    default=[0.15, 0.85, 8], help="β 범위와 격자수")
    ap.add_argument("--noise", nargs=3, type=float, metavar=("LO", "HI", "N"),
                    default=[0.09, 0.09, 1], help="noise 범위와 격자수")
    ap.add_argument("--samples", type=int, default=800, help="BOLD 샘플 수")
    ap.add_argument("--ensemble", type=int, default=3,
                    help="격자점마다 반복할 시드 수 (FC 평균)")
    ap.add_argument("--seed", type=int, default=42, help="기준 시드")
    ap.add_argument("--out", type=str, default="results/sweep",
                    help="출력 경로 접두사")
    ap.add_argument("--no-plot", action="store_true", help="히트맵 생성 생략")
    return ap.parse_args()


def _axis(spec: list[float]) -> np.ndarray:
    lo, hi, n = spec[0], spec[1], int(spec[2])
    return np.array([lo]) if n <= 1 else np.linspace(lo, hi, n)


def evaluate(sigma: float, beta: float, noise: float,
             samples: int, ensemble: int, seed: int) -> dict:
    """한 격자점을 평가한다."""
    base = SimConfig(gl=GLParams(sigma=sigma, beta=beta, noise=noise),
                     n_samples=samples, seed=seed)
    fcs = [run_simulation(replace(base, seed=seed + k)).fc
           for k in range(max(1, ensemble))]
    fc = np.mean(fcs, axis=0)

    rows = {r.label: r for r in validate(fc)}
    anti = next(r for lbl, r in rows.items() if "반상관" in lbl)
    blocks = network_blocks(fc)

    return {
        "sigma": sigma,
        "beta": beta,
        "noise": noise,
        "r_vs_literature": fc_correlation(fc),
        "dmn_tpn_anti": anti.simulated,
        "n_passed": sum(r.passed for r in rows.values()),
        "dmn_internal": blocks["DMN-DMN"],
        "tpn_internal": blocks["TPN-TPN"],
        "cla_ai": rows["CLA–AI (동측)"].simulated,
    }


def main() -> int:
    a = parse_args()
    sigmas, betas, noises = _axis(a.sigma), _axis(a.beta), _axis(a.noise)
    total = len(sigmas) * len(betas) * len(noises)

    print(f"스윕 격자 {len(sigmas)}(σ) × {len(betas)}(β) × {len(noises)}(noise) "
          f"= {total} 점,  격자점마다 앙상블 {a.ensemble}회")
    print()

    records: list[dict] = []
    for k, nz in enumerate(noises):
        for i, s in enumerate(sigmas):
            for j, b in enumerate(betas):
                rec = evaluate(s, b, nz, a.samples, a.ensemble, a.seed)
                records.append(rec)
                done = len(records)
                print(f"  [{done:3d}/{total}] σ={s:.4f} β={b:.3f} noise={nz:.3f}"
                      f"  →  r={rec['r_vs_literature']:+.4f}"
                      f"  DMN-TPN={rec['dmn_tpn_anti']:+.4f}"
                      f"  통과={rec['n_passed']}/7")

    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)

    csv_path = f"{out}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        w.writeheader()
        w.writerows(records)

    best_r = max(records, key=lambda r: r["r_vs_literature"])
    best_anti = min(records, key=lambda r: r["dmn_tpn_anti"])

    print()
    print("─" * 72)
    print(f"  최고 문헌일치도 : σ={best_r['sigma']:.4f} β={best_r['beta']:.3f} "
          f"noise={best_r['noise']:.3f}  →  r = {best_r['r_vs_literature']:.4f}")
    print(f"  최강 반상관     : σ={best_anti['sigma']:.4f} β={best_anti['beta']:.3f} "
          f"noise={best_anti['noise']:.3f}  →  DMN-TPN = "
          f"{best_anti['dmn_tpn_anti']:+.4f}")
    print(f"  CSV 저장        : {csv_path}")
    print("─" * 72)

    if not a.no_plot and len(sigmas) > 1 and len(betas) > 1 and len(noises) == 1:
        _plot(records, sigmas, betas, str(out))
        print(f"  히트맵 저장     : {out}_heatmap.png")

    return 0


def _plot(records: list[dict], sigmas: np.ndarray, betas: np.ndarray,
          out: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from src.plotting import L, setup_fonts
    setup_fonts()

    R = np.array([r["r_vs_literature"] for r in records]).reshape(
        len(sigmas), len(betas))
    A = np.array([r["dmn_tpn_anti"] for r in records]).reshape(
        len(sigmas), len(betas))

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    for ax, M, title, cmap in (
        (axes[0], R,
         L("문헌 FC 일치도  Pearson r", "Match to literature FC (Pearson r)"),
         "viridis"),
        (axes[1], A,
         L("DMN–TPN 평균 FC (음수일수록 반상관)",
           "Mean DMN-TPN FC (negative = anticorrelated)"),
         "RdBu_r"),
    ):
        vmax = np.abs(M).max() if cmap == "RdBu_r" else None
        im = ax.imshow(M, origin="lower", aspect="auto", cmap=cmap,
                       vmin=-vmax if vmax else None, vmax=vmax,
                       extent=[betas[0], betas[-1], sigmas[0], sigmas[-1]])
        ax.set_xlabel(L("β  (전역 억압)", "beta  (global inhibition)"))
        ax.set_ylabel(L("σ  (분기 파라미터)", "sigma  (bifurcation parameter)"))
        ax.set_title(title)
        ax.plot(0.45, 0.985, "w*", markersize=16, markeredgecolor="k",
                label=L("v3 확정값", "v3 reference"))
        ax.legend(loc="lower right")
        fig.colorbar(im, ax=ax)

    fig.savefig(f"{out}_heatmap.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
