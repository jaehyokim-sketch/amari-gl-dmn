#!/usr/bin/env python3
"""결과 시각화 — FC 히트맵 · 산점도 · BOLD 시계열 · SC 행렬.

사용법:
    python scripts/plot_results.py
    python scripts/plot_results.py --ensemble 30 --out results/figs
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src import (  # noqa: E402
    EMPR_FC, SC, GLParams, SimConfig, fc_correlation, run_simulation,
)
from src.nodes import IDS, NODES  # noqa: E402
from src.plotting import L, setup_fonts  # noqa: E402


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="시뮬레이션 결과 시각화")
    ap.add_argument("--sigma", type=float, default=0.985)
    ap.add_argument("--beta", type=float, default=0.45)
    ap.add_argument("--noise", type=float, default=0.09)
    ap.add_argument("--samples", type=int, default=800)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ensemble", type=int, default=1,
                    help="FC 평균에 쓸 반복 횟수")
    ap.add_argument("--out", type=str, default="results/figs",
                    help="그림 출력 디렉터리")
    return ap.parse_args()


# 네트워크 경계 (DMN 6 | TPN 6 | SAL 3 | CLA 2)
_BOUNDS = (6, 12, 15)


def _heat(ax, M, title, vmin=-1, vmax=1, cmap="RdBu_r"):
    im = ax.imshow(M, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(IDS)))
    ax.set_yticks(range(len(IDS)))
    ax.set_xticklabels(IDS, rotation=90, fontsize=7)
    ax.set_yticklabels(IDS, fontsize=7)
    ax.set_title(title, fontsize=11)
    for b in _BOUNDS:
        ax.axhline(b - 0.5, color="k", lw=1.2)
        ax.axvline(b - 0.5, color="k", lw=1.2)
    return im


def main() -> int:
    a = parse_args()
    setup_fonts()

    outdir = ROOT / a.out
    outdir.mkdir(parents=True, exist_ok=True)

    base = SimConfig(gl=GLParams(sigma=a.sigma, beta=a.beta, noise=a.noise),
                     n_samples=a.samples, seed=a.seed)
    res = run_simulation(base)
    fc = res.fc
    if a.ensemble > 1:
        fcs = [fc] + [run_simulation(replace(base, seed=a.seed + k)).fc
                      for k in range(1, a.ensemble)]
        fc = np.mean(fcs, axis=0)

    r = fc_correlation(fc)

    # ── 그림 1: FC 히트맵 3종 ────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), constrained_layout=True)
    im0 = _heat(axes[0], fc, L("시뮬레이션 rsFC", "Simulated rsFC"))
    _heat(axes[1], EMPR_FC, L("문헌 rsFC (GSR)", "Literature rsFC (GSR)"))
    im2 = _heat(axes[2], fc - EMPR_FC,
                L("차이 (시뮬 − 문헌)", "Difference (sim - literature)"),
                vmin=-0.6, vmax=0.6, cmap="PuOr_r")
    fig.colorbar(im0, ax=axes[:2], shrink=0.8)
    fig.colorbar(im2, ax=axes[2], shrink=0.8)
    fig.suptitle(
        L(f"확장 Amari-GL v3 (V7) — σ={a.sigma}, β={a.beta}, noise={a.noise}, "
          f"Pearson r = {r:.3f}",
          f"Extended Amari-GL v3 (V7) - sigma={a.sigma}, beta={a.beta}, "
          f"noise={a.noise}, Pearson r = {r:.3f}"),
        fontsize=12)
    fig.savefig(outdir / "fc_heatmaps.png", dpi=150)
    plt.close(fig)

    # ── 그림 2: 산점도 (시뮬 vs 문헌) ────────────────────────────────────
    iu = np.triu_indices(len(IDS), k=1)
    x, y = EMPR_FC[iu], fc[iu]
    net = {n.id: n.net for n in NODES}
    kinds = [f"{net[IDS[i]]}-{net[IDS[j]]}" if net[IDS[i]] == net[IDS[j]]
             else "-".join(sorted((net[IDS[i]], net[IDS[j]]))) 
             for i, j in zip(*iu)]

    fig, ax = plt.subplots(figsize=(7, 6.5), constrained_layout=True)
    for k in sorted(set(kinds)):
        m = [kk == k for kk in kinds]
        ax.scatter(x[m], y[m], s=28, alpha=0.75, label=k)
    lim = [-0.5, 1.0]
    ax.plot(lim, lim, "k--", lw=1, alpha=0.5)
    ax.axhline(0, color="k", lw=0.5, alpha=0.3)
    ax.axvline(0, color="k", lw=0.5, alpha=0.3)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel(L("문헌 rsFC (GSR)", "Literature rsFC (GSR)"))
    ax.set_ylabel(L("시뮬레이션 rsFC", "Simulated rsFC"))
    ax.set_title(L(f"노드쌍 136개 · Pearson r = {r:.3f}",
                   f"136 node pairs - Pearson r = {r:.3f}"))
    ax.legend(fontsize=8, loc="upper left")
    fig.savefig(outdir / "fc_scatter.png", dpi=150)
    plt.close(fig)

    # ── 그림 3: BOLD 시계열 ──────────────────────────────────────────────
    tr = base.effective_tr
    t = np.arange(res.bold.shape[0]) * tr
    show = min(300, len(t))
    fig, ax = plt.subplots(figsize=(13, 6), constrained_layout=True)
    for i, nd in enumerate(NODES):
        sig = res.bold[:show, i]
        sig = (sig - sig.mean()) / (sig.std() + 1e-12)
        ax.plot(t[:show], sig + i * 4.0, lw=0.9, color=nd.color)
        ax.text(t[0] - tr * 6, i * 4.0, nd.id, fontsize=7, va="center",
                ha="right", color=nd.color)
    ax.set_yticks([])
    ax.set_xlabel(L(f"시간 (s)  ·  TR = {tr:.2f}s", f"time (s) - TR = {tr:.2f}s"))
    ax.set_title(L("Balloon–Windkessel BOLD 시계열 (z-정규화)",
                   "Balloon-Windkessel BOLD time series (z-scored)"))
    ax.margins(x=0.02)
    fig.savefig(outdir / "bold_timeseries.png", dpi=150)
    plt.close(fig)

    # ── 그림 4: SC 행렬 ──────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 6), constrained_layout=True)
    im = _heat(ax, SC, L("구조적 연결행렬 SC (dMRI 문헌 기반, 전부 ≥ 0)",
                         "Structural connectivity SC (all >= 0)"),
               vmin=0, vmax=SC.max(), cmap="magma")
    fig.colorbar(im, ax=ax, shrink=0.85)
    fig.savefig(outdir / "sc_matrix.png", dpi=150)
    plt.close(fig)

    print(f"그림 4종 저장 완료 → {outdir}")
    print(f"  fc_heatmaps.png / fc_scatter.png / bold_timeseries.png / sc_matrix.png")
    print(f"  Pearson r = {r:.4f}"
          + (f"  (앙상블 {a.ensemble}회)" if a.ensemble > 1 else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
